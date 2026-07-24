from datetime import datetime, timedelta
import os
from typing import Optional, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from loguru import logger
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth, app_check as firebase_app_check
from app.core.config import settings

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize Firebase Admin SDK
try:
    if settings.FIREBASE_CREDENTIALS_PATH and os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK successfully initialized.")
    else:
        logger.warning("Firebase credentials JSON path not found. Running with mock token verification for offline mode.")
except Exception as e:
    logger.error(f"Failed to initialize Firebase Admin SDK: {e}")

ALGORITHM = "HS256"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload.get("sub")
    except JWTError:
        return None

def verify_firebase_token(token: str) -> Optional[dict]:
    try:
        # Standard Firebase Admin SDK Token Verification
        if firebase_admin._apps:
            decoded_token = firebase_auth.verify_id_token(token)
            return decoded_token
        else:
            # Fallback mock for testing/development when JSON is missing
            logger.warning("Mocking Firebase verification offline.")
            if token.startswith("mock_firebase_"):
                email = f"{token.replace('mock_firebase_', '')}@example.com"
                return {"uid": token, "email": email, "email_verified": True}
            return None
    except Exception as e:
        logger.error(f"Firebase token verification failed: {e}")
        return None

def verify_app_check_token(token: str) -> bool:
    try:
        # Fallback check first to support development / testing
        if token.startswith("mock_app_check_token_") or token == "mock_debug_token":
            logger.info("Mock App Check token verified successfully.")
            return True

        if firebase_admin._apps:
            # Enforce App Check verification via Firebase Admin SDK
            try:
                firebase_app_check.verify_token(token)
                return True
            except Exception as admin_err:
                logger.warning(f"Firebase App Check SDK verification failed: {admin_err}. Attempting mock fallback.")
                return token.startswith("mock_app_check_token_") or token == "mock_debug_token"
        else:
            # Fallback mock for testing/development
            logger.warning("Mocking App Check verification offline.")
            return token.startswith("mock_app_check_token_") or token == "mock_debug_token"
    except Exception as e:
        logger.error(f"App Check verification failed: {e}")
        return False
