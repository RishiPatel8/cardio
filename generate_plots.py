import os
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

os.makedirs('model_plots', exist_ok=True)

# 1. Individual Training Plots
models = {
    'v7_resnet': r'g:/cardio\ai\artifacts\models\v7\resnet_improved\history.json',
    'v7_tcn': r'g:/cardio\ai\artifacts\models\v7\tcn\history.json',
    'v7_transformer': None,  # No history
    'v7_cnn_lstm': r'g:/cardio\ai\artifacts\models\v7\cnn_lstm\history.json',
    'v8_tcn_multimodal': r'g:/cardio\ai\artifacts\models\v8\tcn_multimodal\history.json',
    'v8_tabular_mlp': r'g:/cardio\ai\artifacts\models\v8\tabular_mlp\history.json'
}

all_histories = {}

for name, path in models.items():
    acc_path = f'model_plots/{name}_training_accuracy.png'
    loss_path = f'model_plots/{name}_loss.png'
    
    if path and os.path.exists(path):
        with open(path, 'r') as f:
            hist = json.load(f)
            all_histories[name] = hist
            
        epochs = range(1, len(hist['accuracy']) + 1)
        
        plt.figure()
        plt.plot(epochs, hist['accuracy'], label='Train Accuracy')
        plt.plot(epochs, hist['val_accuracy'], label='Validation Accuracy')
        plt.title(f'{name} Training Accuracy')
        plt.xlabel('Epochs')
        plt.ylabel('Accuracy')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(acc_path, bbox_inches='tight')
        plt.close()
        
        plt.figure()
        plt.plot(epochs, hist['loss'], label='Train Loss')
        plt.plot(epochs, hist['val_loss'], label='Validation Loss')
        plt.title(f'{name} Training Loss')
        plt.xlabel('Epochs')
        plt.ylabel('Loss')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(loss_path, bbox_inches='tight')
        plt.close()
    else:
        # Create empty plot with note
        plt.figure()
        plt.text(0.5, 0.5, 'Training history not found\nfor this model artifact.', 
                 horizontalalignment='center', verticalalignment='center', fontsize=12)
        plt.title(f'{name} Training Accuracy')
        plt.axis('off')
        plt.savefig(acc_path, bbox_inches='tight')
        plt.close()
        
        plt.figure()
        plt.text(0.5, 0.5, 'Training history not found\nfor this model artifact.', 
                 horizontalalignment='center', verticalalignment='center', fontsize=12)
        plt.title(f'{name} Training Loss')
        plt.axis('off')
        plt.savefig(loss_path, bbox_inches='tight')
        plt.close()

# 2. Combined Training Plots
plt.figure(figsize=(10, 6))
for name, hist in all_histories.items():
    epochs = range(1, len(hist['accuracy']) + 1)
    plt.plot(epochs, hist['accuracy'], label=name)
plt.title('All Models Training Accuracy Comparison')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, alpha=0.3)
plt.savefig('model_plots/all_models_training_accuracy.png', bbox_inches='tight')
plt.close()

plt.figure(figsize=(10, 6))
for name, hist in all_histories.items():
    epochs = range(1, len(hist['val_accuracy']) + 1)
    plt.plot(epochs, hist['val_accuracy'], label=name)
plt.title('All Models Validation Accuracy Comparison')
plt.xlabel('Epochs')
plt.ylabel('Validation Accuracy')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, alpha=0.3)
plt.savefig('model_plots/all_models_validation_accuracy.png', bbox_inches='tight')
plt.close()

# 3. Test Metric Comparisons
df = pd.read_csv(r'g:/cardio\docs\research\final_model_comparison.csv')

# Filter for the relevant models
target_models = ['Resnet Improved', 'Tcn', 'Transformer', 'Cnn Lstm', 'Tcn Multimodal', 'Tabular Mlp']
df_filtered = df[df['Architecture'].isin(target_models)].copy()
df_filtered['ModelKey'] = df_filtered['Architecture'] # just use architecture name for plotting

# test_accuracy_comparison
plt.figure(figsize=(10, 5))
plt.bar(df_filtered['ModelKey'], df_filtered['Test Accuracy'], color='skyblue')
plt.title('Test Accuracy Comparison')
plt.ylabel('Accuracy')
plt.xticks(rotation=45, ha='right')
plt.ylim(0, 1.0)
plt.grid(axis='y', alpha=0.3)
for i, v in enumerate(df_filtered['Test Accuracy']):
    if pd.notna(v):
        plt.text(i, v + 0.02, f'{v:.3f}', ha='center')
plt.savefig('model_plots/test_accuracy_comparison.png', bbox_inches='tight')
plt.close()

# test_macro_f1_comparison
plt.figure(figsize=(10, 5))
plt.bar(df_filtered['ModelKey'], df_filtered['Macro F1'], color='lightgreen')
plt.title('Test Macro F1 Comparison')
plt.ylabel('Macro F1')
plt.xticks(rotation=45, ha='right')
plt.ylim(0, 1.0)
plt.grid(axis='y', alpha=0.3)
for i, v in enumerate(df_filtered['Macro F1']):
    if pd.notna(v):
        plt.text(i, v + 0.02, f'{v:.3f}', ha='center')
plt.savefig('model_plots/test_macro_f1_comparison.png', bbox_inches='tight')
plt.close()

# test_roc_auc_comparison
plt.figure(figsize=(10, 5))
plt.bar(df_filtered['ModelKey'], df_filtered['ROC-AUC'], color='salmon')
plt.title('Test ROC-AUC Comparison')
plt.ylabel('ROC-AUC')
plt.xticks(rotation=45, ha='right')
plt.ylim(0, 1.0)
plt.grid(axis='y', alpha=0.3)
for i, v in enumerate(df_filtered['ROC-AUC']):
    if pd.notna(v):
        plt.text(i, v + 0.02, f'{v:.3f}', ha='center')
plt.savefig('model_plots/test_roc_auc_comparison.png', bbox_inches='tight')
plt.close()

# actual_epochs_comparison
plt.figure(figsize=(10, 5))
plt.bar(df_filtered['ModelKey'], df_filtered['Epochs'], color='purple')
plt.title('Actual Epochs Comparison')
plt.ylabel('Epochs')
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', alpha=0.3)
for i, v in enumerate(df_filtered['Epochs']):
    if pd.notna(v):
        plt.text(i, v + 0.5, f'{int(v)}', ha='center')
plt.savefig('model_plots/actual_epochs_comparison.png', bbox_inches='tight')
plt.close()

# best_epoch_comparison
plt.figure(figsize=(10, 5))
plt.bar(df_filtered['ModelKey'], df_filtered['Best Epoch'], color='orange')
plt.title('Best Epoch Comparison')
plt.ylabel('Best Epoch')
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', alpha=0.3)
for i, v in enumerate(df_filtered['Best Epoch']):
    if pd.notna(v):
        plt.text(i, v + 0.5, f'{int(v)}', ha='center')
plt.savefig('model_plots/best_epoch_comparison.png', bbox_inches='tight')
plt.close()

# training_validation_test_accuracy
plt.figure(figsize=(12, 6))
barWidth = 0.25
r1 = np.arange(len(df_filtered))
r2 = [x + barWidth for x in r1]
r3 = [x + barWidth for x in r2]

plt.bar(r1, df_filtered['Train Accuracy'].fillna(0), color='b', width=barWidth, edgecolor='grey', label='Train')
plt.bar(r2, df_filtered['Validation Accuracy'].fillna(0), color='g', width=barWidth, edgecolor='grey', label='Val')
plt.bar(r3, df_filtered['Test Accuracy'].fillna(0), color='r', width=barWidth, edgecolor='grey', label='Test')

plt.xlabel('Model', fontweight='bold')
plt.xticks([r + barWidth for r in range(len(df_filtered))], df_filtered['ModelKey'], rotation=45, ha='right')
plt.ylabel('Accuracy')
plt.ylim(0, 1.0)
plt.title('Train vs Val vs Test Accuracy')
plt.legend()
plt.grid(axis='y', alpha=0.3)
plt.savefig('model_plots/training_validation_test_accuracy.png', bbox_inches='tight')
plt.close()

print("Plots generated successfully!")

