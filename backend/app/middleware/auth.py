"""
Authentication Middleware for FinRAG.

Provides FastAPI dependencies for protecting endpoints
with Firebase authentication.
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.firebase_auth import (
    FirebaseAuthService, 
    FirebaseAuthError,
    get_firebase_auth_service
)
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# HTTP Bearer token extractor
security = HTTPBearer(auto_error=False)


@dataclass
class AuthenticatedUser:
    """Authenticated user information."""
    user_id: str
    email: Optional[str]
    email_verified: bool
    name: Optional[str]
    picture: Optional[str]
    provider: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "email_verified": self.email_verified,
            "name": self.name,
            "picture": self.picture,
            "provider": self.provider,
        }


class AuthMiddleware:
    """
    Authentication middleware for Firebase token verification.
    
    Use as a FastAPI dependency to protect endpoints.
    """
    
    def __init__(self, firebase_service: Optional[FirebaseAuthService] = None):
        """
        Initialize auth middleware.
        
        Args:
            firebase_service: Optional Firebase service instance
        """
        self.firebase_service = firebase_service
    
    async def __call__(
        self,
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        firebase_service: FirebaseAuthService = Depends(get_firebase_auth_service)
    ) -> AuthenticatedUser:
        """
        Verify authentication and return user info.
        
        Args:
            request: FastAPI request object
            credentials: HTTP Bearer credentials
            firebase_service: Firebase auth service
            
        Returns:
            AuthenticatedUser with user information
            
        Raises:
            HTTPException: If authentication fails
        """
        # Check if auth is disabled for development
        if settings.debug and getattr(settings, 'auth_disabled', False):
            logger.warning("Auth disabled in debug mode - using mock user")
            return AuthenticatedUser(
                user_id="dev_user",
                email="dev@example.com",
                email_verified=True,
                name="Development User",
                picture=None,
                provider="password"
            )
        
        # Check for credentials
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "Authentication required",
                    "error_code": "NO_CREDENTIALS"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Extract token
        token = credentials.credentials
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "Invalid authorization header",
                    "error_code": "INVALID_HEADER"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check if Firebase is initialized
        if not firebase_service.is_initialized:
            logger.error("Firebase not initialized - cannot verify token")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "Authentication service unavailable",
                    "error_code": "SERVICE_UNAVAILABLE"
                }
            )
        
        # Verify the token
        try:
            user_info = firebase_service.verify_token(token)
            
            return AuthenticatedUser(
                user_id=user_info["user_id"],
                email=user_info.get("email"),
                email_verified=user_info.get("email_verified", False),
                name=user_info.get("name"),
                picture=user_info.get("picture"),
                provider=user_info.get("provider")
            )
            
        except FirebaseAuthError as e:
            status_code = status.HTTP_401_UNAUTHORIZED
            
            if e.error_code == "TOKEN_EXPIRED":
                status_code = status.HTTP_401_UNAUTHORIZED
            elif e.error_code == "TOKEN_REVOKED":
                status_code = status.HTTP_401_UNAUTHORIZED
            elif e.error_code == "NOT_INITIALIZED":
                status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            
            raise HTTPException(
                status_code=status_code,
                detail={
                    "error": e.message,
                    "error_code": e.error_code
                },
                headers={"WWW-Authenticate": "Bearer"}
            )


# Create middleware instance
auth_middleware = AuthMiddleware()


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    firebase_service: FirebaseAuthService = Depends(get_firebase_auth_service)
) -> AuthenticatedUser:
    """
    Dependency to get the current authenticated user.
    
    Use this in endpoint function signatures:
    
    @router.get("/protected")
    async def protected_endpoint(user: AuthenticatedUser = Depends(get_current_user)):
        return {"user_id": user.user_id}
    """
    return await auth_middleware(request, credentials, firebase_service)


async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    firebase_service: FirebaseAuthService = Depends(get_firebase_auth_service)
) -> Optional[AuthenticatedUser]:
    """
    Dependency to optionally get the current user.
    
    Returns None if not authenticated (doesn't raise error).
    Useful for endpoints that work differently for authenticated users.
    """
    if not credentials:
        return None
    
    try:
        return await auth_middleware(request, credentials, firebase_service)
    except HTTPException:
        return None


def get_user_id(user: AuthenticatedUser = Depends(get_current_user)) -> str:
    """
    Simple dependency to get just the user_id.
    
    Use when you only need the user ID:
    
    @router.get("/my-documents")
    async def get_documents(user_id: str = Depends(get_user_id)):
        return get_documents_for_user(user_id)
    """
    return user.user_id
