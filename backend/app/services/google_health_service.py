import os
import time
import hmac
import hashlib
import json
import httpx
from datetime import datetime
from loguru import logger
from fastapi import HTTPException
from dotenv import load_dotenv
from app.database.firestore import get_db

load_dotenv()

class GoogleHealthService:
    def __init__(self):
        self.client_id = os.environ.get("GOOGLE_HEALTH_CLIENT_ID", os.environ.get("GOOGLE_CLIENT_ID", "mock_client_id"))
        self.client_secret = os.environ.get("GOOGLE_HEALTH_CLIENT_SECRET", os.environ.get("GOOGLE_CLIENT_SECRET", "mock_client_secret"))
        # The frontend completes the OAuth code exchange on this page.
        self.redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:5173/connections")
        self.scopes = " ".join((
            "https://www.googleapis.com/auth/fitness.activity.read",
            "https://www.googleapis.com/auth/fitness.heart_rate.read",
            "https://www.googleapis.com/auth/fitness.sleep.read",
            "https://www.googleapis.com/auth/fitness.body.read",
            "email",
            "profile",
            "openid"
        ))

    def _generate_state(self, uid: str) -> str:
        """Generates a CSRF token binding the OAuth request to the verified Firebase UID."""
        timestamp = str(int(time.time()))
        message = f"{uid}:{timestamp}"
        signature = hmac.new(
            self.client_secret.encode(), 
            message.encode(), 
            hashlib.sha256
        ).hexdigest()
        return f"{uid}.{timestamp}.{signature}"

    def _verify_state(self, state: str) -> str:
        """Verifies the CSRF token and extracts the UID."""
        try:
            uid, timestamp, signature = state.split(".")
            # Reconstruct signature
            message = f"{uid}:{timestamp}"
            expected_signature = hmac.new(
                self.client_secret.encode(), 
                message.encode(), 
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(expected_signature, signature):
                raise ValueError("Invalid OAuth state signature (CSRF protection).")
            
            # Reject if older than 15 mins
            if time.time() - int(timestamp) > 900:
                raise ValueError("OAuth state token expired.")
                
            return uid
        except Exception as e:
            logger.error(f"State verification failed: {e}")
            raise ValueError("Malformed or invalid OAuth state.")

    def get_authorization_url(self, uid: str) -> str:
        if self.client_id == "mock_client_id" or self.client_secret == "mock_client_secret":
            raise HTTPException(
                status_code=503,
                detail="Google Health OAuth is not configured. Set GOOGLE_HEALTH_CLIENT_ID and GOOGLE_HEALTH_CLIENT_SECRET in backend/.env, then restart the backend.",
            )
        state = self._generate_state(uid)
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        from urllib.parse import urlencode
        return f"{base_url}?{urlencode({
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': self.scopes,
            'access_type': 'offline',
            'prompt': 'consent',
            'state': state,
        })}"

    async def exchange_code(self, code: str, state: str) -> dict:
        uid = self._verify_state(state)
        
        # Verify in REAL mode
        is_real = os.environ.get("PREDICTION_MODE", "simulator") == "real"
        if is_real and self.client_id == "mock_client_id":
            raise HTTPException(status_code=500, detail="Missing Google Cloud credentials for real mode.")

        # Simulate exchange if in simulator mode
        if not is_real and code.startswith("mock_"):
            access_token = "mock_access_token_123"
            refresh_token = "mock_refresh_token_456"
        else:
            async with httpx.AsyncClient() as client:
                res = await client.post("https://oauth2.googleapis.com/token", data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri
                })
                if res.status_code != 200:
                    logger.error(f"Google token exchange failed: {res.text}")
                    raise HTTPException(status_code=400, detail="Google token exchange failed.")
                data = res.json()
                access_token = data.get("access_token")
                refresh_token = data.get("refresh_token")
                id_token = data.get("id_token")
                
                email = None
                if id_token:
                    import jwt # pyjwt must be installed
                    try:
                        decoded = jwt.decode(id_token, options={"verify_signature": False})
                        email = decoded.get("email")
                    except Exception as e:
                        logger.warning(f"Could not decode ID token: {e}")

        db = get_db()
        if db:
            doc_ref = db.collection("users").document(uid).collection("connections").document("google_health")
            doc_ref.set({
                "provider": "google_health",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "email": email if 'email' in locals() else None,
                "expires_at": int(time.time()) + data.get("expires_in", 3599) if 'data' in locals() else None,
                "connected_at": datetime.utcnow().isoformat() + "Z"
            })
            
        return {"status": "success", "uid": uid}

    async def sync_data(self, uid: str) -> dict:
        db = get_db()
        if not db:
            raise HTTPException(status_code=500, detail="Database unavailable")
            
        doc_ref = db.collection("users").document(uid).collection("connections").document("google_health")
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=400, detail="Google Health not connected.")
            
        data = doc.to_dict()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        expires_at = data.get("expires_at", 0)
        
        # Check if token is expired (or expires in the next minute)
        if time.time() > (expires_at - 60):
            if refresh_token:
                logger.info(f"Refreshing token for user {uid}")
                async with httpx.AsyncClient() as client:
                    res = await client.post("https://oauth2.googleapis.com/token", data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token"
                    })
                    if res.status_code == 200:
                        refresh_data = res.json()
                        access_token = refresh_data.get("access_token")
                        # Some OAuth flows return a new refresh token; if not, keep the old one
                        if "refresh_token" in refresh_data:
                            refresh_token = refresh_data.get("refresh_token")
                        
                        expires_at = int(time.time()) + refresh_data.get("expires_in", 3599)
                        
                        doc_ref.update({
                            "access_token": access_token,
                            "refresh_token": refresh_token,
                            "expires_at": expires_at
                        })
                    else:
                        logger.error(f"Failed to refresh token: {res.text}")
                        # If refresh token is invalid/revoked, force disconnect
                        if res.status_code in [400, 401]:
                            doc_ref.delete()
                            raise HTTPException(status_code=401, detail="Google Health connection expired. Please reconnect.")
        
        is_real = os.environ.get("PREDICTION_MODE", "simulator") == "real"
        if not is_real and access_token == "mock_access_token_123":
            # Simulate fetching data
            health_data = {
                "heart_rate": 72,
                "steps": 6500,
                "calories": 2100,
                "sleep_hours": 7.5,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source": "google_health"
            }
        else:
            # Query the Google Fit REST API
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
                
                # Fetch aggregated data for the last 24 hours
                end_time_ms = int(time.time() * 1000)
                start_time_ms = end_time_ms - (86400 * 1000)
                
                payload = {
                    "aggregateBy": [
                        {"dataTypeName": "com.google.heart_rate.bpm"},
                        {"dataTypeName": "com.google.step_count.delta"},
                        {"dataTypeName": "com.google.calories.expended"},
                        {"dataTypeName": "com.google.sleep.segment"}
                    ],
                    "bucketByTime": {"durationMillis": 86400000},
                    "startTimeMillis": start_time_ms,
                    "endTimeMillis": end_time_ms
                }
                
                res = await client.post("https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate", headers=headers, json=payload)
                if res.status_code != 200:
                    logger.error(f"Google Fit API fetch failed: {res.text}")
                    raise HTTPException(status_code=400, detail="Google Health data could not be retrieved. Reconnect if access has expired.")
                
                data_buckets = res.json().get("bucket", [])
                
                hr_val, steps_val, cal_val, sleep_val = None, None, None, None
                
                if data_buckets and len(data_buckets) > 0:
                    dataset = data_buckets[0].get("dataset", [])
                    for ds in dataset:
                        source = ds.get("dataSourceId", "")
                        points = ds.get("point", [])
                        if "heart_rate" in source:
                            if points and points[0].get("value"):
                                hr_val = int(points[0]["value"][0].get("fpVal", points[0]["value"][0].get("intVal", 0)))
                        elif "step_count" in source:
                            if points and points[0].get("value"):
                                steps_val = sum([p["value"][0].get("intVal", 0) for p in points])
                        elif "calories" in source:
                            if points and points[0].get("value"):
                                cal_val = sum([p["value"][0].get("fpVal", 0) for p in points])
                        elif "sleep" in source:
                            if points and points[0].get("value"):
                                sleep_val = round(sum([(int(p["endTimeNanos"]) - int(p["startTimeNanos"])) / 1e9 / 3600 for p in points]), 1)
                
                health_data = {
                    "heart_rate": hr_val,
                    "steps": steps_val,
                    "calories": round(cal_val) if cal_val else None,
                    "sleep_hours": sleep_val,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "source": "google_health",
                }

        # Store the health data
        sync_ref = db.collection("users").document(uid).collection("health_syncs").document()
        sync_ref.set(health_data)
        
        # Update connection last sync and latest data payload for quick access
        doc_ref.update({
            "last_sync": health_data["timestamp"],
            "latest_data": health_data
        })
        
        return health_data

    def disconnect(self, uid: str):
        db = get_db()
        if db:
            doc_ref = db.collection("users").document(uid).collection("connections").document("google_health")
            doc_ref.delete()
        return {"status": "disconnected"}

    def get_status(self, uid: str):
        db = get_db()
        if db:
            doc_ref = db.collection("users").document(uid).collection("connections").document("google_health")
            doc = doc_ref.get()
            if doc.exists:
                doc_data = doc.to_dict()
                return {
                    "connected": True, 
                    "email": doc_data.get("email"),
                    "last_sync": doc_data.get("last_sync"),
                    "data": doc_data.get("latest_data", None)
                }
        return {"connected": False}
