import pytest
from fastapi.testclient import TestClient
import numpy as np
import pandas as pd
import tempfile
import os
os.environ["PREDICTION_MODE"] = "real"
import wfdb

from app.main import app

client = TestClient(app)

# Helper function to generate mock ECG files
def create_mock_csv(samples=1200):
    fd, path = tempfile.mkstemp(suffix=".csv")
    df = pd.DataFrame(np.random.randn(samples, 1))
    df.to_csv(path, index=False, header=False)
    os.close(fd)
    return path

def create_mock_wfdb(samples=1200, fs=360):
    temp_dir = tempfile.mkdtemp()
    record_name = "test_rec"
    path = os.path.join(temp_dir, record_name)
    sig = np.random.randn(samples, 1)
    wfdb.wrsamp(record_name, fs=fs, units=['mV'], sig_name=['MLII'],
                p_signal=sig, fmt=['16'], write_dir=temp_dir)
    return path + ".hea", path + ".dat", temp_dir

@pytest.mark.asyncio
async def test_csv_upload_success():
    csv_path = create_mock_csv(1500)
    with open(csv_path, "rb") as f:
        response = client.post(
            "/api/v1/predictions/physionet",
            files=[("files", ("test.csv", f, "text/csv"))],
            headers={"Authorization": "Bearer mock_firebase_token"}
        )
    os.remove(csv_path)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_wfdb_upload_success():
    hea_path, dat_path, temp_dir = create_mock_wfdb(3600, fs=360) # 10 seconds at 360 Hz
    with open(hea_path, "rb") as f_hea, open(dat_path, "rb") as f_dat:
        response = client.post(
            "/api/v1/predictions/physionet",
            files=[
                ("files", ("test_rec.hea", f_hea, "application/octet-stream")),
                ("files", ("test_rec.dat", f_dat, "application/octet-stream"))
            ],
            headers={"Authorization": "Bearer mock_firebase_token"}
        )
    import shutil
    shutil.rmtree(temp_dir)
    assert response.status_code == 200
    data = response.json()
    assert data["signal_quality"] in ["GOOD", "POOR"]
    if data["signal_quality"] == "POOR":
        assert data["segments_analyzed"] == 0

@pytest.mark.asyncio
async def test_incomplete_wfdb_upload():
    hea_path, dat_path, temp_dir = create_mock_wfdb(3600, fs=360)
    with open(hea_path, "rb") as f_hea:
        response = client.post(
            "/api/v1/predictions/physionet",
            files=[
                ("files", ("test_rec.hea", f_hea, "application/octet-stream"))
            ],
            headers={"Authorization": "Bearer mock_firebase_token"}
        )
    import shutil
    shutil.rmtree(temp_dir)
    assert response.status_code == 400
    assert "Invalid files" in response.json()["detail"]

@pytest.mark.asyncio
async def test_short_ecg_rejection():
    csv_path = create_mock_csv(500) # Only 500 samples (5 seconds)
    with open(csv_path, "rb") as f:
        response = client.post(
            "/api/v1/predictions/physionet",
            files=[("files", ("short.csv", f, "text/csv"))],
            headers={"Authorization": "Bearer mock_firebase_token"}
        )
    os.remove(csv_path)
    assert response.status_code == 400
    assert "Insufficient ECG samples" in response.json()["detail"]
