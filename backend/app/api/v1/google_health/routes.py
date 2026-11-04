from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from app.services.auth_service import get_current_user
from app.services.google_health_service import GoogleHealthService

router = APIRouter()
google_service = GoogleHealthService()

class OAuthCallbackRequest(BaseModel):
    code: str
    state: str

@router.get("/connect", summary="Get OAuth Authorization URL")
async def connect_google_health(current_user: dict = Depends(get_current_user)):
    """Generates a secure OAuth URL with CSRF protection bound to the user ID."""
    user_id = current_user.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    url = google_service.get_authorization_url(user_id)
    return {"url": url}

@router.post("/callback", summary="Exchange Code for Tokens")
async def oauth_callback(
    payload: OAuthCallbackRequest,
    current_user: dict = Depends(get_current_user)
):
    """Exchanges the authorization code for tokens and validates CSRF state."""
    # Note: State validation inherently checks if the state belongs to the current user
    # because the state is HMAC-SHA256 signed using their UID and our client secret.
    try:
        # Extract UID from state inside exchange_code
        result = await google_service.exchange_code(payload.code, payload.state)
        # Extra security check: ensure the token belongs to the logged-in user
        if result["uid"] != current_user.get("uid"):
            raise ValueError("Token identity mismatch")
        return {"message": "Successfully connected"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync", summary="Fetch Vitals from Google Fit")
async def sync_vitals(current_user: dict = Depends(get_current_user)):
    """Fetches heart rate and steps via REST API."""
    user_id = current_user.get("uid")
    return await google_service.sync_data(user_id)

@router.get("/status", summary="Get Google Health Connection Status")
async def get_status(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("uid")
    return google_service.get_status(user_id)

@router.post("/disconnect", summary="Disconnect Google Health")
async def disconnect(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("uid")
    return google_service.disconnect(user_id)
