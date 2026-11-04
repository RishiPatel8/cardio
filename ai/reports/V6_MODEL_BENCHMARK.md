# CardioGuard AI V6: Model Benchmark

Model | Params | Accuracy | Macro F1 | AFIB F1 | AFIB Recall | Block F1 | Other F1 | Inference Time (ms/sample)
---|---|---|---|---|---|---|---|---
**resnet_v5 (V5 BASELINE)** | 134212 | 0.7513 | 0.5923 | 0.7843 | 0.8824 | 0.4949 | 0.2195 | 0.85ms
**resnet_improved (V6 BEST VALIDATION MODEL)** | 510788 | 0.7733 | 0.6157 | 0.8025 | 0.9559 | 0.6173 | 0.1519 | 0.50ms
cnn_lstm | 48324 | 0.6751 | 0.4267 | 0.4560 | 0.6471 | 0.3704 | 0.0000 | 0.55ms
cnn_bilstm | 85444 | 0.7107 | 0.5040 | 0.6329 | 0.7353 | 0.4348 | 0.0779 | 0.76ms
tcn | 55364 | 0.5635 | 0.1804 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.93ms
resnet_attention | 76036 | 0.7174 | 0.5339 | 0.6341 | 0.5735 | 0.5039 | 0.1282 | 2.16ms
transformer | 151556 | 0.7140 | 0.5074 | 0.7394 | 0.8971 | 0.3961 | 0.0270 | 3.44ms

## Conclusion
The best performing architecture was **resnet_improved** with a Macro F1 of 0.6157. It was selected as the winner because it provides the best balance of multi-class discrimination (Macro F1) which is critical for the new 4-class taxonomy, while also demonstrating excellent AFIB F1/Recall. It is saved to `scratch/best_v6_benchmark_model.h5` and will be used as the backbone for Phase 6 augmentation experiments.
