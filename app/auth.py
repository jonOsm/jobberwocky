from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status, Request, Response
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


def authenticate_admin_plain(username: str, password: str) -> bool:
    """Authenticate admin with plain text credentials"""
    print(f"DEBUG: authenticate_admin_plain called with username='{username}', password='{password}'")
    print(f"DEBUG: settings.admin_username='{settings.admin_username}', settings.admin_password='{settings.admin_password}'")
    
    is_correct_username = username == settings.admin_username
    # For now, compare plain text passwords (in production, use proper hashing)
    is_correct_password = password == settings.admin_password
    
    print(f"DEBUG: is_correct_username={is_correct_username}, is_correct_password={is_correct_password}")
    
    result = is_correct_username and is_correct_password
    print(f"DEBUG: Final result={result}")
    return result


def create_admin_session(response: Response) -> None:
    """Create a session for admin authentication"""
    session_token = serializer.dumps("admin_session")
    response.set_cookie(
        key="admin_session",
        value=session_token,
        max_age=3600,  # 1 hour
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax"
    )


def verify_admin_session(request: Request) -> bool:
    """Verify admin session from cookie"""
    session_token = request.cookies.get("admin_session")
    print(f"DEBUG: verify_admin_session - session_token: {session_token}")
    
    if not session_token:
        print("DEBUG: verify_admin_session - no session token found")
        return False
    
    try:
        serializer.loads(session_token, max_age=3600)
        print("DEBUG: verify_admin_session - session token valid")
        return True
    except Exception as e:
        print(f"DEBUG: verify_admin_session - session token invalid: {e}")
        return False


def clear_admin_session(response: Response) -> None:
    """Clear admin session"""
    print("DEBUG: clear_admin_session called")
    response.delete_cookie("admin_session")
    print("DEBUG: admin_session cookie deleted")


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