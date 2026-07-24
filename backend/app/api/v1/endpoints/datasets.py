from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class DatasetSplit(BaseModel):
    train_pct: float
    val_pct: float
    test_pct: float

class LabelDistribution(BaseModel):
    class_label: str
    count: int
    percentage: float

class DatasetStats(BaseModel):
    dataset_name: str
    version: str
    patient_counts: int
    signal_counts: int
    sampling_frequency_hz: int
    splits: DatasetSplit
    class_distribution: List[LabelDistribution]

@router.get("", response_model=List[DatasetStats], summary="Get Dataset Management stats")
async def get_datasets_statistics():
    """Retrieve statistical parameters, sampling rates, and label balance for registered training corpuses."""
    return [
        DatasetStats(
            dataset_name="MIT-BIH Arrhythmia Database",
            version="v1.1",
            patient_counts=47,
            signal_counts=109000,
            sampling_frequency_hz=360,
            splits=DatasetSplit(train_pct=70.0, val_pct=15.0, test_pct=15.0),
            class_distribution=[
                LabelDistribution(class_label="Normal Sinus", count=75000, percentage=68.8),
                LabelDistribution(class_label="Supraventricular", count=2779, percentage=2.5),
                LabelDistribution(class_label="Ventricular Escape", count=7130, percentage=6.5),
                LabelDistribution(class_label="Atrial Fibrillation", count=24091, percentage=22.2)
            ]
        ),
        DatasetStats(
            dataset_name="Chapman University ECG Dataset",
            version="v3.0",
            patient_counts=10646,
            signal_counts=10646,
            sampling_frequency_hz=500,
            splits=DatasetSplit(train_pct=80.0, val_pct=10.0, test_pct=10.0),
            class_distribution=[
                LabelDistribution(class_label="Normal Rhythm", count=5000, percentage=47.0),
                LabelDistribution(class_label="Sinus Bradycardia", count=3885, percentage=36.5),
                LabelDistribution(class_label="Atrial Fibrillation", count=1761, percentage=16.5)
            ]
        ),
        DatasetStats(
            dataset_name="PTB-XL Diagnostic Database",
            version="v1.0.1",
            patient_counts=18885,
            signal_counts=21837,
            sampling_frequency_hz=500,
            splits=DatasetSplit(train_pct=75.0, val_pct=10.0, test_pct=15.0),
            class_distribution=[
                LabelDistribution(class_label="Normal ECG", count=9528, percentage=43.6),
                LabelDistribution(class_label="Myocardial Infarction", count=5481, percentage=25.1),
                LabelDistribution(class_label="Conduction Disturbance", count=4857, percentage=22.2),
                LabelDistribution(class_label="Arrhythmia Specific", count=1971, percentage=9.1)
            ]
        )
    ]
