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


import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

def generate_pdf_document(
    title: str,
    user_email: str,
    request_data: ReportGenerateRequest
) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # 1. Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "CARDIOGUARD AI")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 70, "Diagnostic Research Report")
    c.setFont("Helvetica", 10)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.drawString(50, height - 90, f"Report Generated: {current_time}")
    
    c.line(50, height - 100, width - 50, height - 100)
    
    # 2. ANALYSIS SUMMARY
    y = height - 130
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "1. ANALYSIS SUMMARY")
    y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Predicted Class: {request_data.prediction_class}")
    y -= 20
    c.drawString(50, y, f"Model: {request_data.model_version}")
    y -= 20
    # normalization
    conf = request_data.confidence
    if conf <= 1.0 and conf > 0:
        conf = conf * 100.0
    c.drawString(50, y, f"Predicted Class Probability: {conf:.1f}%")
    y -= 20
    c.drawString(50, y, f"Inference Latency: {request_data.inference_time_ms} ms")
    
    y -= 20
    c.line(50, y, width - 50, y)
    
    # 3. CLASS PROBABILITY DISTRIBUTION
    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "2. CLASS PROBABILITY DISTRIBUTION")
    y -= 15
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, y, "V6 ResNet predicted probability for each classification.")
    
    y -= 30
    classes = [
        "Normal Sinus Rhythm",
        "Atrial Fibrillation (AFIB)",
        "Conduction Block",
        "Other Arrhythmia"
    ]
    probs = request_data.probability_vector
    if not probs or len(probs) != 4:
        probs = [0.0, 0.0, 0.0, 0.0]
        
    for i, class_name in enumerate(classes):
        p = probs[i]
        if p <= 1.0:
            p = p * 100.0
        c.setFont("Helvetica", 10)
        c.drawString(50, y, class_name)
        # Bar
        c.setFillColor(colors.lightgrey)
        c.rect(200, y-2, 200, 10, fill=1, stroke=0)
        c.setFillColor(colors.darkgrey)
        c.rect(200, y-2, p * 2.0, 10, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.drawString(410, y, f"{p:.1f}%")
        y -= 25
        
    y -= 10
    c.line(50, y, width - 50, y)
    
    # 4. INPUT / ECG INFORMATION
    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "3. INPUT / ECG INFORMATION")
    y -= 20
    c.setFont("Helvetica", 10)
    meta = request_data.dataset_metadata or {}
    c.drawString(50, y, f"Dataset / File: {meta.get('fileName', 'Not available')}")
    y -= 15
    c.drawString(50, y, f"Records: {meta.get('recordsCount', 'Not available')}")
    y -= 15
    c.drawString(50, y, f"Sampling Frequency: {meta.get('fs', '100 Hz')}")
    
    y -= 20
    c.line(50, y, width - 50, y)
    
    # PAGE 2 if required
    if y < 250:
        c.showPage()
        y = height - 50
        
    # 5. SUPPLEMENTARY PHYSIOLOGICAL INSIGHTS
    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "4. SUPPLEMENTARY PHYSIOLOGICAL INSIGHTS")
    y -= 20
    c.setFont("Helvetica", 10)
    
    if not request_data.explainable_insights:
        c.drawString(50, y, "Not available")
        y -= 15
    else:
        for insight in request_data.explainable_insights:
            c.drawString(50, y, insight)
            y -= 15
            
    y -= 10
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, y, "These physiological insights are supplementary and are not explanations of the neural network's internal decision.")
    y -= 20
    c.line(50, y, width - 50, y)
    
    # 6. AI INFERENCE PIPELINE
    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "5. AI INFERENCE PIPELINE")
    y -= 20
    c.setFont("Helvetica", 10)
    pipeline_txt = "Uploaded ECG CSV -> Raw ECG Signal -> Signal Quality Validation -> V6 Preprocessing -> resnet_improved_v6 -> 4-Class Output -> Predicted Class"
    c.drawString(50, y, pipeline_txt)
    y -= 20
    c.line(50, y, width - 50, y)
    
    # 7. CLINICAL / RESEARCH DISCLAIMER
    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "6. CLINICAL / RESEARCH DISCLAIMER")
    y -= 20
    c.setFont("Helvetica", 8)
    disclaimer_1 = "This output is an AI research prediction and is not a clinical diagnosis. The model probabilities represent the"
    disclaimer_2 = "neural network's classification output and should not be interpreted as a patient's clinical probability of disease."
    disclaimer_3 = "Clinical interpretation must be performed by a qualified healthcare professional."
    c.drawString(50, y, disclaimer_1)
    y -= 12
    c.drawString(50, y, disclaimer_2)
    y -= 12
    c.drawString(50, y, disclaimer_3)
    
    y -= 40
    c.drawString(50, y, "Report generated by CardioGuard AI Research Prototype")
    
    c.save()
    buffer.seek(0)
    return buffer.read()

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
    
    filename = f"report_{current_user.id}_{request_data.prediction_id or 'latest'}.pdf"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Write the dynamically compiled PDF layout file
    pdf_bytes = generate_pdf_document(
        title=request_data.title,
        user_email=current_user.email,
        request_data=request_data
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
