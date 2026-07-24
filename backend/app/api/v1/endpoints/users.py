import os
from fastapi import APIRouter, Depends, UploadFile, File, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserResponse, UserUpdate
from app.repositories.user_profile import UserProfileRepository
from app.schemas.user_profile import UserProfileResponse, UserProfileUpdate
from app.models.user_profile import UserProfile

router = APIRouter()

# Configure local uploads directory absolute path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/me", response_model=UserResponse, summary="Get Current Profile")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Fetch the profile record of the currently logged-in user."""
    return current_user

@router.put("/profile", response_model=UserResponse, summary="Update Profile")
async def update_my_profile(
    request_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update profile credentials or email contact configurations."""
    user_repo = UserRepository(db)
    if request_data.email:
        current_user.email = request_data.email
    if request_data.password:
        from app.core.security import get_password_hash
        current_user.hashed_password = get_password_hash(request_data.password)
    
    await user_repo.update(current_user)
    return current_user

@router.post("/upload", summary="Upload User File Locally")
async def upload_user_file_local(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload custom timeseries data or profile images locally to the server."""
    filename = f"{current_user.id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write file to local disk: {e}"
        )
        
    return {
        "filename": filename,
        "url": f"http://localhost:8000/api/v1/reports/download/{filename}"
    }

@router.get("/me/profile", response_model=UserProfileResponse, summary="Get User Profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch the profile record of the currently logged-in user, creating a default one if none exists."""
    profile_repo = UserProfileRepository(db)
    profile = await profile_repo.get_by_user_id(current_user.id)
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        profile = await profile_repo.create(profile)
        await db.commit()
    return profile

@router.put("/me/profile", response_model=UserProfileResponse, summary="Update User Profile")
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update personal clinical, lifestyle, and goal statistics."""
    profile_repo = UserProfileRepository(db)
    profile = await profile_repo.get_by_user_id(current_user.id)
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        profile = await profile_repo.create(profile)
    
    # Update fields
    # Use standard dict unpack or direct setattr
    # We unpack current_medications and allergies from pydantic submodels safely
    data_dict = profile_data.model_dump(exclude_unset=True)
    if "current_medications" in data_dict:
        data_dict["current_medications"] = [m.model_dump() for m in profile_data.current_medications] if profile_data.current_medications else []
    
    for field, value in data_dict.items():
        setattr(profile, field, value)
        
    await profile_repo.update(profile)
    await db.commit()
    return profile
