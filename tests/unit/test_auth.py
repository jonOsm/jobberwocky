import pytest
from datetime import datetime, timezone
from app.auth import (
    get_password_hash, 
    verify_password, 
    generate_csrf_token, 
    verify_csrf_token,
    create_admin_session,
    verify_admin_session,
    clear_admin_session,
    create_employer_session,
    verify_employer_session,
    clear_employer_session
)
from app.config import settings


class TestPasswordHashing:
    """Test password hashing and verification"""
    
    def test_password_hashing(self):
        """Test that password hashing works and produces different hashes"""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different (due to salt)
        assert hash1 != hash2
        assert len(hash1) > 20  # Reasonable hash length
    
    def test_password_verification_correct(self):
        """Test password verification with correct password"""
        password = "testpassword123"
        password_hash = get_password_hash(password)
        
        assert verify_password(password, password_hash) is True
    
    def test_password_verification_incorrect(self):
        """Test password verification with incorrect password"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        password_hash = get_password_hash(password)
        
        assert verify_password(wrong_password, password_hash) is False
    
    def test_password_verification_empty_password(self):
        """Test password verification with empty password"""
        password = ""
        password_hash = get_password_hash(password)
        
        assert verify_password(password, password_hash) is True
        assert verify_password("wrong", password_hash) is False


class TestCSRFToken:
    """Test CSRF token generation and verification"""
    
    def test_generate_csrf_token(self):
        """Test CSRF token generation"""
        token1 = generate_csrf_token()
        token2 = generate_csrf_token()
        
        # Tokens should be different
        assert token1 != token2
        assert len(token1) > 10  # Reasonable token length
    
    def test_verify_csrf_token_valid(self):
        """Test CSRF token verification with valid token"""
        token = generate_csrf_token()
        assert verify_csrf_token(token) is True
    
    def test_verify_csrf_token_invalid(self):
        """Test CSRF token verification with invalid token"""
        assert verify_csrf_token("invalid_token") is False
    
    def test_verify_csrf_token_empty(self):
        """Test CSRF token verification with empty token"""
        assert verify_csrf_token("") is False
        assert verify_csrf_token(None) is False


class TestSessionManagement:
    """Test session creation, verification, and clearing"""
    
    def test_admin_session_creation(self):
        """Test admin session creation"""
        from fastapi import Response
        
        response = Response()
        create_admin_session(response)
        
        # Check that session cookie is set
        cookies = response.headers.getlist("set-cookie")
        admin_cookies = [c for c in cookies if "admin_session" in c]
        assert len(admin_cookies) == 1
    
    def test_admin_session_verification(self, monkeypatch):
        """Test admin session verification"""
        from fastapi import Request
        
        # Mock request with valid session
        request = Request(scope={"type": "http", "headers": []})
        
        # Mock session data
        session_data = {"admin": True, "type": "admin"}
        from app.auth import serializer
        session_token = serializer.dumps(session_data)
        
        # Mock cookies
        request.cookies = {"admin_session": session_token}
        
        # Test verification
        result = verify_admin_session(request)
        assert result is True
    
    def test_admin_session_verification_invalid(self):
        """Test admin session verification with invalid session"""
        from fastapi import Request
        
        request = Request(scope={"type": "http", "headers": []})
        request.cookies = {"admin_session": "invalid_token"}
        
        result = verify_admin_session(request)
        assert result is False
    
    def test_admin_session_verification_no_session(self):
        """Test admin session verification with no session"""
        from fastapi import Request
        
        request = Request(scope={"type": "http", "headers": []})
        request.cookies = {}
        
        result = verify_admin_session(request)
        assert result is False
    
    def test_employer_session_creation(self):
        """Test employer session creation"""
        from fastapi import Response
        
        response = Response()
        employer_account_id = 123
        create_employer_session(response, employer_account_id)
        
        # Check that session cookie is set
        cookies = response.headers.getlist("set-cookie")
        employer_cookies = [c for c in cookies if "employer_session" in c]
        assert len(employer_cookies) == 1
    
    def test_employer_session_verification(self, monkeypatch):
        """Test employer session verification"""
        from fastapi import Request
        
        # Mock request with valid session
        request = Request(scope={"type": "http", "headers": []})
        
        # Mock session data
        session_data = {"employer_account_id": 123, "type": "employer"}
        from app.auth import serializer
        session_token = serializer.dumps(session_data)
        
        # Mock cookies
        request.cookies = {"employer_session": session_token}
        
        # Test verification
        result = verify_employer_session(request)
        assert result == 123
    
    def test_employer_session_verification_invalid(self):
        """Test employer session verification with invalid session"""
        from fastapi import Request
        
        request = Request(scope={"type": "http", "headers": []})
        request.cookies = {"employer_session": "invalid_token"}
        
        result = verify_employer_session(request)
        assert result is None
    
    def test_employer_session_verification_no_session(self):
        """Test employer session verification with no session"""
        from fastapi import Request
        
        request = Request(scope={"type": "http", "headers": []})
        request.cookies = {}
        
        result = verify_employer_session(request)
        assert result is None
    
    def test_clear_admin_session(self):
        """Test admin session clearing"""
        from fastapi import Response
        
        response = Response()
        clear_admin_session(response)
        
        # Check that session cookie is cleared
        cookies = response.headers.getlist("set-cookie")
        admin_cookies = [c for c in cookies if "admin_session" in c and "max-age=0" in c]
        assert len(admin_cookies) == 1
    
    def test_clear_employer_session(self):
        """Test employer session clearing"""
        from fastapi import Response
        
        response = Response()
        clear_employer_session(response)
        
        # Check that session cookie is cleared
        cookies = response.headers.getlist("set-cookie")
        employer_cookies = [c for c in cookies if "employer_session" in c and "max-age=0" in c]
        assert len(employer_cookies) == 1


class TestSecurityFeatures:
    """Test security-related features"""
    
    def test_csrf_token_uniqueness(self):
        """Test that CSRF tokens are unique"""
        tokens = set()
        for _ in range(100):
            token = generate_csrf_token()
            tokens.add(token)
        
        # All tokens should be unique
        assert len(tokens) == 100
    
    def test_password_hash_uniqueness(self):
        """Test that password hashes are unique for same password"""
        password = "testpassword"
        hashes = set()
        
        for _ in range(10):
            hash_value = get_password_hash(password)
            hashes.add(hash_value)
        
        # All hashes should be unique due to salt
        assert len(hashes) == 10 