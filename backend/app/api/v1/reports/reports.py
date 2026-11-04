from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_reports():
    return []

@router.post("/generate")
async def generate_report():
    return {"report_url": "https://example.com/mock-report.pdf"}
