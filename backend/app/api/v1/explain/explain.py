from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_explainability():
    return {
        "status": "success",
        "explanation": []
    }
