import torch
import torch.nn as nn
import math

class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 5000):
        super(PositionalEncoding, self).__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: [batch_size, seq_len, d_model]
        return x + self.pe[:, :x.size(1)]

class TimeSeriesTransformer(nn.Module):
    def __init__(
        self, 
        input_dim: int = 1, 
        d_model: int = 64, 
        nhead: int = 4, 
        num_layers: int = 3, 
        dim_feedforward: int = 128, 
        dropout: float = 0.1,
        num_classes: int = 2
    ):
        super(TimeSeriesTransformer, self).__init__()
        self.d_model = d_model
        
        # Projection layer for multi-channel/single-channel raw input
        self.input_projection = nn.Linear(input_dim, d_model)
        self.pos_encoder = PositionalEncoding(d_model)
        
        # Transformer encoder layers
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, 
            nhead=nhead, 
            dim_feedforward=dim_feedforward, 
            dropout=dropout,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # Output layers: pooling and projection
        self.pooling = nn.AdaptiveAvgPool1d(1)
        self.classifier = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, num_classes)
        )

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """Projects the inputs and runs the sequence transformer to extract latent feature embeddings."""
        # Input shape: [batch_size, seq_len, input_dim]
        x = self.input_projection(x) * math.sqrt(self.d_model)
        x = self.pos_encoder(x)
        latents = self.transformer_encoder(x)
        # Global average pooling over the temporal dimension
        pooled = self.pooling(latents.transpose(1, 2)).squeeze(2)
        return pooled # shape: [batch_size, d_model]

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        pooled = self.encode(x)
        logits = self.classifier(pooled)
        return logits
