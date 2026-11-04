from fastapi import APIRouter

router = APIRouter()

@router.get("/me/profile")
async def get_profile():
    return {
        "name": "Alex Mercer",
        "email": "alex.mercer@example.com",
        "age": 42,
        "weight": 72.5,
        "hypertension": False,
        "diabetes": False,
        "smoking": False,
        "bmi": 22.8
    }

@router.get("/")
async def get_profile_root():
    return await get_profile()

@router.post("/upload")
async def upload_dataset():
    return {"status": "Dataset uploaded successfully"}
