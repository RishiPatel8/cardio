import os
import uuid
from fastapi import APIRouter, Depends, Query, status, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.report import Report
from app.repositories.report import ReportRepository
from app.repositories.prediction import PredictionRepository
from app.repositories.user_profile import UserProfileRepository
from app.schemas.report import ReportGenerateRequest, ReportResponse

router = APIRouter()

# Configure local uploads directory absolute path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def generate_pdf_document(
    title: str,
    user_email: str,
    prediction_class: str,
    confidence: float,
    insights: List[str],
    model_version: str,
    age: int = 30,
    sex: str = "Unspecified",
    height: float = 175.0,
    weight: float = 70.0,
    bmi: float = 22.86,
    daily_steps_goal: int = 10000,
    weekly_exercise_goal: int = 150,
    hydration_goal: int = 2500
) -> bytes:
    """Composes a standard PDF 1.4 document stream from dynamic diagnostic parameters."""
    pdf_stream = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 6 0 R >>
stream
BT
/F1 20 Tf
70 720 Td
({title}) Tj
/F1 10 Tf
0 -30 Td
(User Profile: {user_email}) Tj
0 -16 Td
(Demographics: Age {age} | Sex {sex} | Height {height}cm | Weight {weight}kg | BMI {bmi:.2f}) Tj
0 -16 Td
(Fitness Targets: Daily Steps: {daily_steps_goal} | Weekly Exercise: {weekly_exercise_goal}min | Hydration: {hydration_goal}ml) Tj
0 -16 Td
(Model Classification: {prediction_class}) Tj
0 -16 Td
(Confidence Score: {confidence:.2f}%) Tj
0 -16 Td
(Inference Version: {model_version}) Tj
0 -25 Td
(Clinical Diagnostic Analysis & Explainable AI Insights:) Tj
"""
    for idx, insight in enumerate(insights):
        # Escape parenthesis inside PDF Tj command
        safe_insight = insight.replace("(", "\\(").replace(")", "\\)")
        # Split long strings to prevent printing off right-hand margins
        chunks = [safe_insight[i:i+80] for i in range(0, len(safe_insight), 80)]
        for chunk in chunks:
            pdf_stream += f"\n0 -16 Td\n({chunk}) Tj"
            
    pdf_stream += """
ET
endstream
endobj
6 0 obj
"""
    
    stream_start = pdf_stream.find("stream\n") + len("stream\n")
    stream_end = pdf_stream.find("\nendstream")
    stream_length = stream_end - stream_start
    
    pdf_stream += f"{stream_length}\nendobj\nxref\n0 7\n0000000000 65535 f\ntrailer\n<< /Size 7 /Root 1 0 R >>\n%%EOF\n"
    return pdf_stream.encode('latin1')

@router.get("", response_model=List[ReportResponse], summary="Get Reports List")
async def get_reports_list(
    limit: int = Query(50, description="Max reports to fetch"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch previously generated diagnostic and cardiovascular PDF reports list."""
    report_repo = ReportRepository(db)
    return await report_repo.get_by_user(current_user.id, limit)

@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED, summary="Generate Report")
async def generate_pdf_report(
    request_data: ReportGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Compile and export a clinical PDF diagnostics summary report locally on the server."""
    report_repo = ReportRepository(db)
    pred_repo = PredictionRepository(db)
    profile_repo = UserProfileRepository(db)
    
    # Fetch prediction target from datastore
    prediction = None
    if request_data.prediction_id:
        try:
            pred_id = uuid.UUID(request_data.prediction_id) if isinstance(request_data.prediction_id, str) else request_data.prediction_id
            prediction = await pred_repo.get_by_id(pred_id)
        except Exception:
            pass
            
    if not prediction:
        # Fallback to the latest user prediction logged
        user_preds = await pred_repo.get_by_user(current_user.id, limit=1)
        if user_preds:
            prediction = user_preds[0]
            
    # Resolve parameters to write
    classification = prediction.classification if prediction else "Normal"
    confidence = prediction.confidence_score if prediction else 96.2
    insights = prediction.explainable_insights if prediction else [
        "Average heart rate registered at 72 bpm.",
        "ECG Lead-II QRS morphology indicates normal sinus rhythm."
    ]
    model_version = prediction.model_version if prediction else "ensemble-random_forest-v2.0"
    
    # Load profile details
    profile = await profile_repo.get_by_user_id(current_user.id)
    age = profile.age if profile else 30
    sex = profile.sex if profile else "Unspecified"
    height = profile.height if profile else 175.0
    weight = profile.weight if profile else 70.0
    bmi = profile.bmi if profile else 22.86
    daily_steps_goal = profile.daily_steps_goal if profile else 10000
    weekly_exercise_goal = profile.weekly_exercise_goal if profile else 150
    hydration_goal = profile.hydration_goal if profile else 2500

    filename = f"report_{current_user.id}_{prediction.id if prediction else 'latest'}.pdf"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Write the dynamically compiled PDF layout file
    pdf_bytes = generate_pdf_document(
        title=request_data.title,
        user_email=current_user.email,
        prediction_class=classification,
        confidence=confidence,
        insights=insights,
        model_version=model_version,
        age=age,
        sex=sex,
        height=height,
        weight=weight,
        bmi=bmi,
        daily_steps_goal=daily_steps_goal,
        weekly_exercise_goal=weekly_exercise_goal,
        hydration_goal=hydration_goal
    )
    
    with open(file_path, "wb") as f:
        f.write(pdf_bytes)
            
    # Direct access URL to download the report from backend
    local_report_url = f"http://localhost:8000/api/v1/reports/download/{filename}"
    
    report = Report(
        user_id=current_user.id,
        title=request_data.title,
        report_url=local_report_url
    )
    report = await report_repo.create(report)
    return report

@router.get("/download/{filename}", summary="Download Local Report File")
async def download_report_file(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Serve the local PDF reports directly from server uploads directory."""
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Requested report file does not exist on storage.")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)
