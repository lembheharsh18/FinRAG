"""
Firebase Authentication Service for FinRAG.

Handles Firebase Admin SDK initialization and token verification.
"""

import logging
from typing import Optional, Dict, Any
from functools import lru_cache
import json
from pathlib import Path

import firebase_admin
from firebase_admin import auth, credentials
from firebase_admin.exceptions import FirebaseError

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class FirebaseAuthError(Exception):
    """Custom exception for Firebase auth errors."""
    def __init__(self, message: str, error_code: str = "AUTH_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class FirebaseAuthService:
    """
    Firebase Authentication service.
    
    Handles Firebase Admin SDK initialization and token verification.
    """
    
    _initialized: bool = False
    _app: Optional[firebase_admin.App] = None
    
    def __init__(self):
        """Initialize Firebase Admin SDK."""
        if not self._initialized:
            self._initialize_firebase()
    
    def _initialize_firebase(self) -> None:
        """
        Initialize Firebase Admin SDK.
        
        Supports multiple initialization methods:
        1. Service account JSON file (FIREBASE_SERVICE_ACCOUNT_PATH)
        2. Service account JSON string (FIREBASE_SERVICE_ACCOUNT_JSON)
        3. Application Default Credentials (for GCP environments)
        4. Project ID only (limited functionality)
        """
        if firebase_admin._apps:
            logger.info("Firebase already initialized")
            FirebaseAuthService._initialized = True
            FirebaseAuthService._app = firebase_admin.get_app()
            return
        
        try:
            cred = None
            
            # Method 1: Service account file path
            service_account_path = getattr(settings, 'firebase_service_account_path', None)
            if service_account_path and Path(service_account_path).exists():
                logger.info(f"Initializing Firebase with service account file: {service_account_path}")
                cred = credentials.Certificate(service_account_path)
            
            # Method 2: Service account JSON string (from env)
            elif hasattr(settings, 'firebase_service_account_json') and settings.firebase_service_account_json:
                logger.info("Initializing Firebase with service account JSON")
                service_account_info = json.loads(settings.firebase_service_account_json)
                cred = credentials.Certificate(service_account_info)
            
            # Method 3: Application Default Credentials
            elif hasattr(settings, 'google_application_credentials'):
                logger.info("Initializing Firebase with Application Default Credentials")
                cred = credentials.ApplicationDefault()
            
            # Method 4: Project ID only (for token verification in development)
            elif settings.firebase_project_id:
                logger.info(f"Initializing Firebase with project ID: {settings.firebase_project_id}")
                # Initialize without credentials - limited functionality
                FirebaseAuthService._app = firebase_admin.initialize_app(
                    options={'projectId': settings.firebase_project_id}
                )
                FirebaseAuthService._initialized = True
                logger.info("Firebase initialized with project ID only")
                return
            
            else:
                logger.warning(
                    "No Firebase credentials found. Auth will not work. "
                    "Set FIREBASE_PROJECT_ID or provide service account credentials."
                )
                return
            
            # Initialize with credentials
            if cred:
                FirebaseAuthService._app = firebase_admin.initialize_app(cred)
                FirebaseAuthService._initialized = True
                logger.info("Firebase Admin SDK initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise FirebaseAuthError(
                f"Firebase initialization failed: {str(e)}",
                "INITIALIZATION_ERROR"
            )
    
    @property
    def is_initialized(self) -> bool:
        """Check if Firebase is initialized."""
        return self._initialized
    
    def verify_token(self, id_token: str) -> Dict[str, Any]:
        """
        Verify a Firebase ID token.
        
        Args:
            id_token: The Firebase ID token from the client
            
        Returns:
            Decoded token claims including user_id
            
        Raises:
            FirebaseAuthError: If token is invalid
        """
        if not self._initialized:
            raise FirebaseAuthError(
                "Firebase not initialized",
                "NOT_INITIALIZED"
            )
        
        try:
            # Verify the token
            decoded_token = auth.verify_id_token(id_token)
            
            return {
                "user_id": decoded_token["uid"],
                "email": decoded_token.get("email"),
                "email_verified": decoded_token.get("email_verified", False),
                "name": decoded_token.get("name"),
                "picture": decoded_token.get("picture"),
                "auth_time": decoded_token.get("auth_time"),
                "provider": decoded_token.get("firebase", {}).get("sign_in_provider"),
            }
            
        except auth.ExpiredIdTokenError:
            raise FirebaseAuthError(
                "Token has expired. Please sign in again.",
                "TOKEN_EXPIRED"
            )
        except auth.RevokedIdTokenError:
            raise FirebaseAuthError(
                "Token has been revoked. Please sign in again.",
                "TOKEN_REVOKED"
            )
        except auth.InvalidIdTokenError as e:
            raise FirebaseAuthError(
                f"Invalid token: {str(e)}",
                "INVALID_TOKEN"
            )
        except FirebaseError as e:
            logger.error(f"Firebase auth error: {e}")
            raise FirebaseAuthError(
                f"Authentication failed: {str(e)}",
                "AUTH_FAILED"
            )
        except Exception as e:
            logger.error(f"Unexpected auth error: {e}")
            raise FirebaseAuthError(
                "Authentication failed",
                "AUTH_ERROR"
            )
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user information by user ID.
        
        Args:
            user_id: Firebase user ID
            
        Returns:
            User information or None if not found
        """
        if not self._initialized:
            return None
        
        try:
            user = auth.get_user(user_id)
            return {
                "user_id": user.uid,
                "email": user.email,
                "display_name": user.display_name,
                "photo_url": user.photo_url,
                "email_verified": user.email_verified,
                "disabled": user.disabled,
                "created_at": user.user_metadata.creation_timestamp if user.user_metadata else None,
            }
        except auth.UserNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error fetching user: {e}")
            return None


@lru_cache()
def get_firebase_auth_service() -> FirebaseAuthService:
    """Get cached Firebase auth service instance."""
    return FirebaseAuthService()
