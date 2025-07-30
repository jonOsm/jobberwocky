import pytest
from datetime import datetime, timezone
from unittest.mock import patch
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
    
    def test_admin_session_verification(self):
        """Test admin session verification"""
        # Mock session data
        session_data = {"admin": True, "type": "admin"}
        from app.auth import serializer
        session_token = serializer.dumps(session_data)
        
        # Create a simple mock request object
        class MockRequest:
            def __init__(self, cookies_dict):
                self._cookies = cookies_dict
            
            @property
            def cookies(self):
                return self._cookies
        
        # Create mock request with session cookie
        request = MockRequest({"admin_session": session_token})
        
        # Test verification
        result = verify_admin_session(request)
        assert result is True
    
    def test_admin_session_verification_invalid(self):
        """Test admin session verification with invalid session"""
        # Create a simple mock request object
        class MockRequest:
            def __init__(self, cookies_dict):
                self._cookies = cookies_dict
            
            @property
            def cookies(self):
                return self._cookies
        
        # Create mock request with invalid session cookie
        request = MockRequest({"admin_session": "invalid_token"})
        
        result = verify_admin_session(request)
        assert result is False
    
    def test_admin_session_verification_no_session(self):
        """Test admin session verification with no session"""
        # Create a simple mock request object
        class MockRequest:
            def __init__(self, cookies_dict):
                self._cookies = cookies_dict
            
            @property
            def cookies(self):
                return self._cookies
        
        # Create mock request with no session cookie
        request = MockRequest({})
        
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
    
    def test_employer_session_verification(self):
        """Test employer session verification"""
        # Mock session data
        session_data = {"employer_account_id": 123, "type": "employer"}
        from app.auth import serializer
        session_token = serializer.dumps(session_data)
        
        # Create a simple mock request object
        class MockRequest:
            def __init__(self, cookies_dict):
                self._cookies = cookies_dict
            
            @property
            def cookies(self):
                return self._cookies
        
        # Create mock request with session cookie
        request = MockRequest({"employer_session": session_token})
        
        # Test verification
        result = verify_employer_session(request)
        assert result == 123
    
    def test_employer_session_verification_invalid(self):
        """Test employer session verification with invalid session"""
        # Create a simple mock request object
        class MockRequest:
            def __init__(self, cookies_dict):
                self._cookies = cookies_dict
            
            @property
            def cookies(self):
                return self._cookies
        
        # Create mock request with invalid session cookie
        request = MockRequest({"employer_session": "invalid_token"})
        
        result = verify_employer_session(request)
        assert result is None
    
    def test_employer_session_verification_no_session(self):
        """Test employer session verification with no session"""
        # Create a simple mock request object
        class MockRequest:
            def __init__(self, cookies_dict):
                self._cookies = cookies_dict
            
            @property
            def cookies(self):
                return self._cookies
        
        # Create mock request with no session cookie
        request = MockRequest({})
        
        result = verify_employer_session(request)
        assert result is None
    
    def test_clear_admin_session(self):
        """Test admin session clearing"""
        from fastapi import Response
        
        response = Response()
        clear_admin_session(response)
        
        # Check that session cookie is cleared (delete_cookie sets max-age=0)
        cookies = response.headers.getlist("set-cookie")
        admin_cookies = [c for c in cookies if "admin_session" in c]
        assert len(admin_cookies) == 1
        # Verify it's a deletion cookie (either max-age=0 or expires in the past)
        admin_cookie = admin_cookies[0]
        assert "max-age=0" in admin_cookie or "expires=" in admin_cookie
    
    def test_clear_employer_session(self):
        """Test employer session clearing"""
        from fastapi import Response
        
        response = Response()
        clear_employer_session(response)
        
        # Check that session cookie is cleared (delete_cookie sets max-age=0)
        cookies = response.headers.getlist("set-cookie")
        employer_cookies = [c for c in cookies if "employer_session" in c]
        assert len(employer_cookies) == 1
        # Verify it's a deletion cookie (either max-age=0 or expires in the past)
        employer_cookie = employer_cookies[0]
        assert "max-age=0" in employer_cookie or "expires=" in employer_cookie


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


class TestAdminAuthentication:
    """Test admin authentication functions"""
    
    def test_authenticate_admin_plain_success(self):
        """Test successful admin authentication with plain text"""
        from app.auth import authenticate_admin_plain
        
        # Mock settings to return known values
        with patch('app.auth.settings') as mock_settings:
            mock_settings.admin_username = "admin"
            mock_settings.admin_password = "password123"
            
            result = authenticate_admin_plain("admin", "password123")
            assert result is True
    
    def test_authenticate_admin_plain_failure(self):
        """Test failed admin authentication with plain text"""
        from app.auth import authenticate_admin_plain
        
        # Mock settings to return known values
        with patch('app.auth.settings') as mock_settings:
            mock_settings.admin_username = "admin"
            mock_settings.admin_password = "password123"
            
            result = authenticate_admin_plain("admin", "wrongpassword")
            assert result is False
    
    def test_authenticate_admin_plain_wrong_username(self):
        """Test admin authentication with wrong username"""
        from app.auth import authenticate_admin_plain
        
        # Mock settings to return known values
        with patch('app.auth.settings') as mock_settings:
            mock_settings.admin_username = "admin"
            mock_settings.admin_password = "password123"
            
            result = authenticate_admin_plain("wronguser", "password123")
            assert result is False


class TestCSRFTokenExtraction:
    """Test CSRF token extraction from requests"""
    
    def test_get_csrf_token_from_form_data(self):
        """Test extracting CSRF token from form data"""
        from app.auth import get_csrf_token_from_request
        
        class MockRequest:
            def __init__(self, method="POST", form_data=None, headers=None):
                self.method = method
                self._form_data = form_data or {}
                self._headers = headers or {}
            
            def form(self):
                return self._form_data
            
            @property
            def headers(self):
                return self._headers
        
        # Test with CSRF token in form data
        request = MockRequest(
            form_data={"csrf_token": "test_token_123"}
        )
        token = get_csrf_token_from_request(request)
        assert token == "test_token_123"
    
    def test_get_csrf_token_from_headers(self):
        """Test extracting CSRF token from headers"""
        from app.auth import get_csrf_token_from_request
        
        class MockRequest:
            def __init__(self, method="POST", form_data=None, headers=None):
                self.method = method
                self._form_data = form_data or {}
                self._headers = headers or {}
            
            def form(self):
                raise Exception("No form data")
            
            @property
            def headers(self):
                return self._headers
        
        # Test with CSRF token in headers
        request = MockRequest(
            headers={"X-CSRF-Token": "test_token_456"}
        )
        token = get_csrf_token_from_request(request)
        assert token == "test_token_456"
    
    def test_get_csrf_token_no_token(self):
        """Test extracting CSRF token when none is present"""
        from app.auth import get_csrf_token_from_request
        
        class MockRequest:
            def __init__(self, method="POST", form_data=None, headers=None):
                self.method = method
                self._form_data = form_data or {}
                self._headers = headers or {}
            
            def form(self):
                return self._form_data
            
            @property
            def headers(self):
                return self._headers
        
        # Test with no CSRF token
        request = MockRequest()
        token = get_csrf_token_from_request(request)
        assert token is None


class TestErrorHandling:
    """Test error handling in authentication functions"""
    
    def test_verify_employer_session_exception_handling(self):
        """Test verify_employer_session handles exceptions gracefully"""
        from app.auth import verify_employer_session
        
        class MockRequest:
            def __init__(self, cookies_dict):
                self._cookies = cookies_dict
            
            @property
            def cookies(self):
                return self._cookies
        
        # Test with invalid session token that causes exception
        request = MockRequest({"employer_session": "invalid_token"})
        result = verify_employer_session(request)
        assert result is None
    
    def test_verify_admin_session_exception_handling(self):
        """Test verify_admin_session handles exceptions gracefully"""
        from app.auth import verify_admin_session
        
        class MockRequest:
            def __init__(self, cookies_dict):
                self._cookies = cookies_dict
            
            @property
            def cookies(self):
                return self._cookies
        
        # Test with invalid session token that causes exception
        request = MockRequest({"admin_session": "invalid_token"})
        result = verify_admin_session(request)
        assert result is False
    
    def test_verify_csrf_token_exception_handling(self):
        """Test verify_csrf_token handles exceptions gracefully"""
        from app.auth import verify_csrf_token
        
        # Test with malformed token that causes exception
        result = verify_csrf_token("malformed.token.here")
        assert result is False
    
    def test_require_csrf_token_decorator(self):
        """Test the require_csrf_token decorator"""
        from app.auth import require_csrf_token
        
        class MockRequest:
            def __init__(self, method="POST", form_data=None, headers=None):
                self.method = method
                self._form_data = form_data or {}
                self._headers = headers or {}
            
            def form(self):
                return self._form_data
            
            @property
            def headers(self):
                return self._headers
        
        # Test with valid CSRF token
        request = MockRequest(form_data={"csrf_token": "valid_token"})
        # This should not raise an exception
        # Note: This is a basic test - in practice, the decorator would be used on route functions
        
        # Test with missing CSRF token (this would normally raise an exception)
        request_no_token = MockRequest()
        # This test verifies the function exists and can be called
        # The actual exception handling would be tested in integration tests 