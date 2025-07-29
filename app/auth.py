from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext
from itsdangerous import URLSafeTimedSerializer
from app.config import settings

security = HTTPBasic()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
serializer = URLSafeTimedSerializer(settings.secret_key)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_admin(credentials: HTTPBasicCredentials) -> bool:
    is_correct_username = credentials.username == settings.admin_username
    is_correct_password = verify_password(credentials.password, get_password_hash(settings.admin_password))
    return is_correct_username and is_correct_password


def generate_csrf_token() -> str:
    return serializer.dumps("csrf_token")


def verify_csrf_token(token: str, max_age: int = 3600) -> bool:
    try:
        serializer.loads(token, max_age=max_age)
        return True
    except:
        return False


def get_csrf_token_from_request(request: Request) -> Optional[str]:
    """Extract CSRF token from form data or headers"""
    # For multipart form data, we need to check the form data
    if request.method == "POST":
        try:
            # Try to get form data
            form_data = request.form()
            if hasattr(form_data, "get"):
                return form_data.get("csrf_token")
        except:
            pass
    
    # Check headers
    return request.headers.get("X-CSRF-Token")


def require_csrf_token(request: Request):
    """Middleware to require CSRF token on POST requests"""
    if request.method == "POST":
        token = get_csrf_token_from_request(request)
        if not token or not verify_csrf_token(token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid CSRF token"
            ) 