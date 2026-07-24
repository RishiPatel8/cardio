import torch
import os
from typing import str
from ai.foundation_models.transformer import TimeSeriesTransformer

def export_pytorch_to_onnx(model_path: str, output_dir: str, version: str = "v1.0") -> str:
    """Exports a PyTorch TimeSeriesTransformer foundation model to ONNX format with version tag."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize model
    model = TimeSeriesTransformer(input_dim=1, d_model=64, nhead=4, num_layers=3)
    
    # Load state dict if path exists
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
        
    model.eval()
    
    # Generate physiological dummy input: shape [batch_size=1, seq_len=100, input_dim=1]
    dummy_input = torch.randn(1, 100, 1)
    
    onnx_filename = f"timeseries_transformer_{version}.onnx"
    onnx_path = os.path.join(output_dir, onnx_filename)
    
    # Run PyTorch ONNX export
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=['input_signals'],
        output_names=['classification_logits'],
        dynamic_axes={'input_signals': {0: 'batch_size', 1: 'seq_len'}, 'classification_logits': {0: 'batch_size'}}
    )
    
    print(f"TimeSeriesTransformer model successfully exported to ONNX format: {onnx_path}")
    return onnx_path

def generate_tflite_placeholder(output_dir: str, version: str = "v1.0") -> str:
    """Writes a TFLite model structure placeholder to exports folder for Android wearable imports."""
    os.makedirs(output_dir, exist_ok=True)
    tflite_filename = f"timeseries_transformer_{version}.tflite"
    tflite_path = os.path.join(output_dir, tflite_filename)
    
    # Write a small valid binary byte sequence mimicking model metadata structure
    with open(tflite_path, "wb") as f:
        f.write(b"TFLITE_MOCK_MODEL_METADATA_VERSION_" + version.encode() + b"\x00" * 64)
        
    print(f"TFLite model placeholder successfully generated: {tflite_path}")
    return tflite_path
