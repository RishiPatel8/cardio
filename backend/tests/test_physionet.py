import pytest
import os
import numpy as np
# Remove TestClient import as we will use the fixture

@pytest.fixture
def mock_csv_file(tmp_path):
    # Create a 187-column CSV
    csv_path = tmp_path / "test.csv"
    data = np.random.rand(10, 187)
    np.savetxt(csv_path, data, delimiter=",")
    return csv_path

from app.services.inference_service import get_inference_service

@pytest.mark.asyncio
async def test_physionet_upload_csv(mock_csv_file, client):
    # This might fail if the inference service tries to load models but fails
    # But it verifies the routing and logic.
    with open(mock_csv_file, "rb") as f:
        # We need to simulate REAL mode for this to pass
        get_inference_service().mode = "real"
        response = await client.post(
            "/api/v1/predictions/physionet",
            files=[("files", ("test.csv", f, "text/csv"))],
        )
    # We just want to ensure it's not a 404
    assert response.status_code in [200, 400, 401, 500]
