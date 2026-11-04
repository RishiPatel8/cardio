import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_pdf_report_generation(client: AsyncClient):
    payload = {
        "title": "Cardio Diagnostics Summary",
        "prediction_class": "Atrial Fibrillation (AFIB)",
        "confidence": 0.962,
        "probability_vector": [0.01, 0.962, 0.02, 0.008],
        "model_version": "resnet_improved_v6",
        "inference_time_ms": 32,
        "explainable_insights": ["SUPPLEMENTARY INSIGHT: SDNN is 45.0 ms"],
        "dataset_metadata": {
            "fileName": "test.csv",
            "recordsCount": 5000,
            "fs": "100 Hz"
        }
    }
    
    # Generate the report
    res = await client.post("/api/v1/reports/generate", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert "report_url" in data
    
    # Download the report
    filename = data["report_url"].split("/")[-1]
    res_dl = await client.get(f"/api/v1/reports/download/{filename}")
    assert res_dl.status_code == 200
    assert res_dl.headers["content-type"] == "application/pdf"
    
    pdf_bytes = res_dl.content
    assert len(pdf_bytes) > 0
    
    assert pdf_bytes.startswith(b"%PDF-")
