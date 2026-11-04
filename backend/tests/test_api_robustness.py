import pytest
from httpx import AsyncClient
import numpy as np
import io
import os
import sys
from app.services.inference_service import get_inference_service

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["PREDICTION_MODE"] = "real"
from app.main import app



@pytest.mark.asyncio
async def test_missing_files(client):
    response = await client.post("/api/v1/predictions/physionet")
    assert response.status_code == 422 # FastAPI validation error for missing files

@pytest.mark.asyncio
async def test_invalid_csv_format(client):
    # Create a dummy CSV that is too small
    csv_content = "1,2,3\n4,5,6"
    file = io.BytesIO(csv_content.encode("utf-8"))
    
    get_inference_service().mode = "real"
    response = await client.post(
        "/api/v1/predictions/physionet",
        files={"files": ("test.csv", file, "text/csv")}
    )
    assert response.status_code == 400
    assert "CSV must have at least" in response.json()["detail"]

@pytest.mark.asyncio
async def test_extreme_noise_rejection(tmp_path, client):
    # Generate extreme noise CSV (variance > 10.0)
    # 1001 samples to account for pandas read_csv treating first as header
    noise = np.random.normal(0, 5, 1001)
    csv_content = ",".join([str(val) for val in noise])
    file = io.BytesIO(csv_content.encode("utf-8"))
    
    get_inference_service().mode = "real"
    response = await client.post(
        "/api/v1/predictions/physionet",
        files={"files": ("noise.csv", file, "text/csv")}
    )
    print("Noise Rejection Response:", response.text)

    # It should return 200 OK but with "POOR" signal quality
    assert response.status_code == 200
    data = response.json()
    assert data["signal_quality"] == "POOR"
    assert "Insufficient signal quality" in data["primary_prediction"]
    
@pytest.mark.asyncio
async def test_flatline_rejection(client):
    # Generate flatline CSV
    flatline = np.zeros(1001)
    csv_content = ",".join([str(val) for val in flatline])
    file = io.BytesIO(csv_content.encode("utf-8"))
    
    get_inference_service().mode = "real"
    response = await client.post(
        "/api/v1/predictions/physionet",
        files={"files": ("flat.csv", file, "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["signal_quality"] == "POOR"
    assert "Insufficient signal quality" in data["primary_prediction"]
