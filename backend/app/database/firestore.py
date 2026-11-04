import firebase_admin
import os
from firebase_admin import credentials, firestore
from app.core.config import settings
from loguru import logger

db = None

def init_firebase():
    global db
    if not firebase_admin._apps:
        try:
            credentials_path = settings.FIREBASE_CREDENTIALS_PATH or os.environ.get("FIREBASE_ADMIN_CREDENTIALS")
            if credentials_path:
                cred = credentials.Certificate(credentials_path)
                firebase_admin.initialize_app(cred)
            else:
                if settings.PREDICTION_MODE == "real":
                    logger.warning("FIREBASE_ADMIN_CREDENTIALS missing in PREDICTION_MODE='real'. Allowing local testing.")
                # Useful for emulator or default credentials in demo mode
                firebase_admin.initialize_app()
            db = firestore.client()
            logger.info("Firebase Admin initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin: {e}")
            if settings.PREDICTION_MODE == "real":
                logger.warning("Failed to initialize Firebase Admin in real mode, bypassing for local test.")

def get_db():
    global db
    if db is None:
        init_firebase()
    return db
