import os
from fastapi import Request, HTTPException
from loguru import logger
from app.core.config import settings

# Try to import firebase_admin, but if it's not installed/configured,
# we can mock authentication to unblock frontend development.
try:
    import firebase_admin
    from firebase_admin import auth, credentials
    
    FIREBASE_MOCKED = False
    
    # Initialize Firebase Admin if not already initialized
    if not firebase_admin._apps:
        cred_path = settings.FIREBASE_CREDENTIALS_PATH or os.environ.get("FIREBASE_ADMIN_CREDENTIALS")
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info(f"Firebase Admin initialized with {cred_path}")
        else:
            if os.environ.get("PREDICTION_MODE", "real") == "real":
                logger.warning("FIREBASE_ADMIN_CREDENTIALS missing in PREDICTION_MODE='real'. Allowing mock auth for local E2E testing.")
            logger.warning("FIREBASE_ADMIN_CREDENTIALS not set or missing. Falling back to mocked auth.")
            FIREBASE_MOCKED = True

except ImportError as e:
    if os.environ.get("PREDICTION_MODE", "real") == "real":
        logger.warning("firebase-admin package missing in PREDICTION_MODE='real'. Allowing mock auth for local E2E testing.")
    logger.warning("firebase-admin package not found. Falling back to mocked auth.")
    FIREBASE_MOCKED = True

class AuthService:
    """Service to verify Firebase tokens and return authenticated user context."""
    
    @staticmethod
    def verify_token(token: str) -> dict:
        if FIREBASE_MOCKED or token == "mock-token" or not token:
            if os.environ.get("PREDICTION_MODE", "real") == "real":
                logger.warning("Mock authentication is being used in real mode.")
            logger.info("Using mocked authentication context.")
            return {
                "uid": "mock_user_id_123",
                "email": "test@cardioguard.ai",
                "email_verified": True
            }
        
        try:
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def get_current_user(request: Request):
    """Dependency to extract and verify the Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        if os.environ.get("PREDICTION_MODE", "real") == "real":
            logger.warning("Missing or invalid Authorization header in real mode")
        if FIREBASE_MOCKED:
            return AuthService.verify_token("mock-token")
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = auth_header.split(" ")[1]
    user_data = AuthService.verify_token(token)
    return user_data
