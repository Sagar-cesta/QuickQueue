from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import hashlib
from app.core.config import settings

# Simple password hashing (for demo purposes)
def hash_password(password: str) -> str:
    """Simple password hashing using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(plain_password) == hashed_password

# JWT token handling
security = HTTPBearer()

# Role-based permissions
ROLE_PERMISSIONS = {
    "admin": {
        "can_create_users": True,
        "can_edit_users": True,
        "can_delete_users": True,
        "can_change_roles": True,
        "can_view_all_tickets": True,
        "can_edit_all_tickets": True,
        "can_delete_tickets": True,
        "can_close_tickets": True,
        "can_resolve_tickets": True,
        "can_mark_repeat": True,
        "can_view_analytics": True,
        "can_view_dashboard": True,
        "can_manage_system": True
    },
    "agent": {
        "can_create_users": False,
        "can_edit_users": False,
        "can_delete_users": False,
        "can_change_roles": False,
        "can_view_all_tickets": True,
        "can_edit_all_tickets": True,
        "can_delete_tickets": False,
        "can_close_tickets": True,
        "can_resolve_tickets": True,
        "can_mark_repeat": True,
        "can_view_analytics": True,
        "can_view_dashboard": True,
        "can_manage_system": False
    },
    "user": {
        "can_create_users": False,
        "can_edit_users": False,
        "can_delete_users": False,
        "can_change_roles": False,
        "can_view_all_tickets": False,
        "can_edit_all_tickets": False,
        "can_delete_tickets": False,
        "can_close_tickets": False,
        "can_resolve_tickets": True,
        "can_mark_repeat": False,
        "can_view_analytics": True,
        "can_view_dashboard": True,
        "can_manage_system": False
    }
}

# In-memory user storage (for demo purposes)
users_db = {
    "admin": {
        "id": 1,
        "username": "admin",
        "hashed_password": hash_password("admin123"),
        "role": "admin",
        "full_name": "System Administrator",
        "email": "admin@quickqueue.com",
        "is_active": True,
        "created_at": datetime.now()
    },
    "agent": {
        "id": 2,
        "username": "agent",
        "hashed_password": hash_password("agent123"),
        "role": "agent",
        "full_name": "Support Agent",
        "email": "agent@quickqueue.com",
        "is_active": True,
        "created_at": datetime.now()
    },
    "user": {
        "id": 3,
        "username": "user",
        "hashed_password": hash_password("user123"),
        "role": "user",
        "full_name": "Regular User",
        "email": "user@quickqueue.com",
        "is_active": True,
        "created_at": datetime.now()
    }
}

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return hash_password(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user data"""
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=["HS256"])
        user_id: int = payload.get("sub")
        role: str = payload.get("role", "user")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"user_id": user_id, "role": role}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(token_data: dict = Depends(verify_token)):
    """Get current authenticated user"""
    return token_data

def authenticate_user(username: str, password: str):
    """Authenticate user with username and password"""
    user = users_db.get(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    if not user["is_active"]:
        return False
    return user

def get_user_permissions(role: str) -> Dict[str, bool]:
    """Get permissions for a specific role"""
    return ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["user"])

def has_permission(user_role: str, permission: str) -> bool:
    """Check if user has specific permission"""
    permissions = get_user_permissions(user_role)
    return permissions.get(permission, False)

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def permission_checker(current_user: dict = Depends(get_current_user)):
        if not has_permission(current_user["role"], permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}"
            )
        return current_user
    return permission_checker

def get_user_by_id(user_id: int):
    """Get user by ID"""
    for user in users_db.values():
        if user["id"] == user_id:
            return user
    return None

def get_user_by_username(username: str):
    """Get user by username"""
    return users_db.get(username)

def create_user(username: str, password: str, role: str, full_name: str, email: str):
    """Create a new user (Admin only)"""
    if username in users_db:
        raise ValueError("Username already exists")
    
    user_id = max([u["id"] for u in users_db.values()]) + 1
    new_user = {
        "id": user_id,
        "username": username,
        "hashed_password": get_password_hash(password),
        "role": role,
        "full_name": full_name,
        "email": email,
        "is_active": True,
        "created_at": datetime.now()
    }
    users_db[username] = new_user
    return new_user

def update_user_role(username: str, new_role: str):
    """Update user role (Admin only)"""
    if username not in users_db:
        raise ValueError("User not found")
    users_db[username]["role"] = new_role
    return users_db[username]

def get_all_users():
    """Get all users (Admin only)"""
    return list(users_db.values())

def delete_user(username: str):
    """Delete user (Admin only)"""
    if username not in users_db:
        raise ValueError("User not found")
    if username in ["admin", "agent", "user"]:  # Prevent deleting default users
        raise ValueError("Cannot delete default users")
    del users_db[username]
    return True

# Session-based authentication for web routes
def get_current_user_from_session(request: Request):
    """Get current user from session (for web routes)"""
    username = request.cookies.get("username")
    if not username:
        return None
    return users_db.get(username)

def require_login():
    """Require user to be logged in"""
    def login_checker(request: Request):
        user = get_current_user_from_session(request)
        if not user:
            # Redirect to login instead of raising exception
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/login", status_code=302)
        return user
    return login_checker

def require_role(required_role: str):
    """Require specific role"""
    def role_checker(request: Request):
        user = get_current_user_from_session(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        if user["role"] != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return user
    return role_checker

def require_permission_web(permission: str):
    """Require specific permission for web routes"""
    def permission_checker(request: Request):
        user = get_current_user_from_session(request)
        if not user:
            # Redirect to login instead of raising exception
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/login", status_code=302)
        if not has_permission(user["role"], permission):
            # Raise exception for dependency injection to handle
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permission: {permission}"
            )
        return user
    return permission_checker