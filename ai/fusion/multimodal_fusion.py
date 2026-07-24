import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Any
from ai.foundation_models.transformer import TimeSeriesTransformer

class MultimodalFusionModel(nn.Module):
    def __init__(
        self,
        transformer_model: TimeSeriesTransformer,
        tabular_dim: int,
        fused_dim: int = 128,
        num_classes: int = 2,
        dropout: float = 0.2
    ):
        super(MultimodalFusionModel, self).__init__()
        self.transformer = transformer_model
        
        # Dimension of projected transformer latents
        self.latent_dim = transformer_model.d_model
        self.tabular_dim = tabular_dim
        
        # Dense fusion layer combining sequence latents and tabular vectors
        self.fusion_network = nn.Sequential(
            nn.Linear(self.latent_dim + tabular_dim, fused_dim),
            nn.BatchNorm1d(fused_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(fused_dim, fused_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        # Final classification logits
        self.classifier = nn.Linear(fused_dim // 2, num_classes)

    def forward(self, timeseries_input: torch.Tensor, tabular_input: torch.Tensor) -> torch.Tensor:
        # timeseries_input shape: [batch_size, seq_len, input_dim]
        # tabular_input shape: [batch_size, tabular_dim]
        
        # 1. Extract latents from foundation ECG transformer
        ecg_latents = self.transformer.encode(timeseries_input) # [batch_size, latent_dim]
        
        # 2. Concatenate latents with tabular features
        fused_vector = torch.cat([ecg_latents, tabular_input], dim=1) # [batch_size, latent_dim + tabular_dim]
        
        # 3. Project to fused classification representation
        fused_features = self.fusion_network(fused_vector)
        logits = self.classifier(fused_features)
        return logits

def preprocess_tabular_features(
    hrv_features: Dict[str, float], 
    wearable_features: Dict[str, float],
    demographics: Dict[str, float]
) -> np.ndarray:
    """Preprocesses and vectorizes mixed tabular parameters for multimodal fusion input."""
    # Ordered features: MeanRR, SDNN, RMSSD, pNN50, LF/HF, SD1, SD2, Steps, Calories, Sleep, SpO2, Age
    features_ordered = [
        hrv_features.get("mean_rr", 800.0),
        hrv_features.get("sdnn", 50.0),
        hrv_features.get("rmssd", 35.0),
        hrv_features.get("pnn50", 10.0),
        hrv_features.get("lf_hf_ratio", 1.5),
        hrv_features.get("sd1", 25.0),
        hrv_features.get("sd2", 70.0),
        
        wearable_features.get("steps", 6000.0),
        wearable_features.get("calories", 300.0),
        wearable_features.get("sleep_minutes", 420.0),
        wearable_features.get("spo2", 98.0),
        
        demographics.get("age", 45.0)
    ]
    return np.array(features_ordered, dtype=np.float32)
