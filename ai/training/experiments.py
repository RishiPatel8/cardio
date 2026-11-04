import tensorflow as tf
from tensorflow.keras.layers import Input, Conv1D, MaxPooling1D, LSTM, Dense, Flatten, Dropout, Bidirectional, BatchNormalization, Add, GlobalAveragePooling1D, Activation, LayerNormalization, MultiHeadAttention
from tensorflow.keras.models import Model, Sequential

def get_base_model(name, input_shape=(1000, 1), num_classes=4):
    if name == "resnet_v5":
        # 1. Current V5 ResNet baseline
        inputs = Input(shape=input_shape)
        x = Conv1D(32, 7, padding='same')(inputs)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        
        shortcut = Conv1D(64, 1, padding='same')(x)
        x = Conv1D(64, 5, padding='same')(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = Conv1D(64, 5, padding='same')(x)
        x = BatchNormalization()(x)
        x = Add()([shortcut, x])
        x = Activation('relu')(x)
        x = MaxPooling1D(2)(x)
        
        shortcut = Conv1D(128, 1, padding='same')(x)
        x = Conv1D(128, 3, padding='same')(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = Conv1D(128, 3, padding='same')(x)
        x = BatchNormalization()(x)
        x = Add()([shortcut, x])
        x = Activation('relu')(x)
        x = GlobalAveragePooling1D()(x)
        
        x = Dense(128, activation='relu')(x)
        x = Dropout(0.5)(x)
        outputs = Dense(num_classes, activation='softmax')(x)
        return Model(inputs, outputs, name="resnet_v5")

    elif name == "resnet_improved":
        # 2. Improved 1D ResNet (Deeper, More Filters)
        inputs = Input(shape=input_shape)
        x = Conv1D(64, 7, strides=2, padding='same')(inputs)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = MaxPooling1D(3, strides=2, padding='same')(x)
        
        for filters in [64, 128, 256]:
            shortcut = Conv1D(filters, 1, strides=2, padding='same')(x)
            x = Conv1D(filters, 3, padding='same')(x)
            x = BatchNormalization()(x)
            x = Activation('relu')(x)
            x = Conv1D(filters, 3, padding='same', strides=2)(x)
            x = BatchNormalization()(x)
            x = Add()([shortcut, x])
            x = Activation('relu')(x)
            
        x = GlobalAveragePooling1D()(x)
        x = Dense(256, activation='relu')(x)
        x = Dropout(0.5)(x)
        outputs = Dense(num_classes, activation='softmax')(x)
        return Model(inputs, outputs, name="resnet_improved")

    elif name == "cnn_lstm":
        # 3. CNN-LSTM
        model = Sequential(name="cnn_lstm")
        model.add(Conv1D(filters=32, kernel_size=5, activation='relu', input_shape=input_shape))
        model.add(BatchNormalization())
        model.add(MaxPooling1D(pool_size=2))
        model.add(Conv1D(filters=64, kernel_size=5, activation='relu'))
        model.add(BatchNormalization())
        model.add(MaxPooling1D(pool_size=2))
        model.add(LSTM(64, return_sequences=False))
        model.add(Dropout(0.5))
        model.add(Dense(64, activation='relu'))
        model.add(Dense(num_classes, activation='softmax'))
        return model

    elif name == "cnn_bilstm":
        # 4. CNN-BiLSTM
        model = Sequential(name="cnn_bilstm")
        model.add(Conv1D(filters=32, kernel_size=5, activation='relu', input_shape=input_shape))
        model.add(BatchNormalization())
        model.add(MaxPooling1D(pool_size=2))
        model.add(Conv1D(filters=64, kernel_size=5, activation='relu'))
        model.add(BatchNormalization())
        model.add(MaxPooling1D(pool_size=2))
        model.add(Bidirectional(LSTM(64, return_sequences=False)))
        model.add(Dropout(0.5))
        model.add(Dense(64, activation='relu'))
        model.add(Dense(num_classes, activation='softmax'))
        return model

    elif name == "tcn":
        # 5. TCN
        inputs = Input(shape=input_shape)
        x = inputs
        for dilation_rate in [1, 2, 4, 8, 16]:
            x = Conv1D(filters=64, kernel_size=3, padding='causal', dilation_rate=dilation_rate, activation='relu')(x)
            x = BatchNormalization()(x)
        x = GlobalAveragePooling1D()(x)
        x = Dense(64, activation='relu')(x)
        x = Dropout(0.5)(x)
        outputs = Dense(num_classes, activation='softmax')(x)
        return Model(inputs, outputs, name="tcn")

    elif name == "resnet_attention":
        # 6. ResNet + temporal attention
        inputs = Input(shape=input_shape)
        x = Conv1D(32, 7, padding='same')(inputs)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        
        shortcut = Conv1D(64, 1, padding='same')(x)
        x = Conv1D(64, 5, padding='same')(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = Conv1D(64, 5, padding='same')(x)
        x = BatchNormalization()(x)
        x = Add()([shortcut, x])
        x = Activation('relu')(x)
        x = MaxPooling1D(2)(x)
        
        # Temporal Attention
        attn_out = MultiHeadAttention(num_heads=2, key_dim=64)(x, x)
        x = Add()([x, attn_out])
        x = LayerNormalization()(x)
        
        x = GlobalAveragePooling1D()(x)
        x = Dense(128, activation='relu')(x)
        x = Dropout(0.5)(x)
        outputs = Dense(num_classes, activation='softmax')(x)
        return Model(inputs, outputs, name="resnet_attention")

    elif name == "transformer":
        # 7. Lightweight Transformer / temporal attention model
        inputs = Input(shape=input_shape)
        x = Conv1D(64, kernel_size=15, strides=2, padding='same', activation='relu')(inputs)
        x = LayerNormalization(epsilon=1e-6)(x)
        
        attn_output1 = MultiHeadAttention(num_heads=4, key_dim=64)(x, x)
        x = Add()([x, attn_output1])
        x = LayerNormalization(epsilon=1e-6)(x)
        ffn_output1 = Dense(64, activation='relu')(x)
        x = Add()([x, ffn_output1])
        x = LayerNormalization(epsilon=1e-6)(x)
        
        x = MaxPooling1D(pool_size=4)(x)
        
        attn_output2 = MultiHeadAttention(num_heads=4, key_dim=64)(x, x)
        x = Add()([x, attn_output2])
        x = LayerNormalization(epsilon=1e-6)(x)
        ffn_output2 = Dense(64, activation='relu')(x)
        x = Add()([x, ffn_output2])
        x = LayerNormalization(epsilon=1e-6)(x)
        
        x = GlobalAveragePooling1D()(x)
        x = Dropout(0.3)(x)
        x = Dense(128, activation='relu')(x)
        x = Dropout(0.3)(x)
        outputs = Dense(num_classes, activation='softmax')(x)
        return Model(inputs, outputs, name="transformer")
    
    elif name == "tabular_mlp":
        # 8. Tabular MLP Baseline
        inputs = Input(shape=(4,))
        x = Dense(64, activation='relu')(inputs)
        x = BatchNormalization()(x)
        x = Dense(32, activation='relu')(x)
        x = Dropout(0.3)(x)
        outputs = Dense(num_classes, activation='softmax')(x)
        return Model(inputs, outputs, name="tabular_mlp")

    elif name == "tcn_multimodal":
        # 9. Multimodal Fusion (TCN + Tabular MLP)
        # ECG Branch (TCN)
        ecg_inputs = Input(shape=(1000, 1), name="ecg_input")
        x = ecg_inputs
        for dilation_rate in [1, 2, 4, 8, 16]:
            x = Conv1D(filters=64, kernel_size=3, padding='causal', dilation_rate=dilation_rate, activation='relu')(x)
            x = BatchNormalization()(x)
        x = GlobalAveragePooling1D()(x)
        ecg_embedding = Dense(64, activation='relu')(x)
        
        # Tabular Branch
        tab_inputs = Input(shape=(4,), name="tabular_input")
        y = Dense(32, activation='relu')(tab_inputs)
        y = BatchNormalization()(y)
        tab_embedding = Dense(16, activation='relu')(y)
        
        # Fusion
        fused = tf.keras.layers.Concatenate()([ecg_embedding, tab_embedding])
        fused = Dense(64, activation='relu')(fused)
        fused = Dropout(0.5)(fused)
        outputs = Dense(num_classes, activation='softmax')(fused)
        
        return Model(inputs=[ecg_inputs, tab_inputs], outputs=outputs, name="tcn_multimodal")
        
    else:
        raise ValueError(f"Unknown architecture {name}")

ARCHITECTURES = {
    'resnet_v5': lambda input_shape, num_classes: get_base_model("resnet_v5", input_shape, num_classes),
    'resnet_improved': lambda input_shape, num_classes: get_base_model("resnet_improved", input_shape, num_classes),
    'cnn_lstm': lambda input_shape, num_classes: get_base_model("cnn_lstm", input_shape, num_classes),
    'cnn_bilstm': lambda input_shape, num_classes: get_base_model("cnn_bilstm", input_shape, num_classes),
    'tcn': lambda input_shape, num_classes: get_base_model("tcn", input_shape, num_classes),
    'resnet_attention': lambda input_shape, num_classes: get_base_model("resnet_attention", input_shape, num_classes),
    'transformer': lambda input_shape, num_classes: get_base_model("transformer", input_shape, num_classes),
    'tabular_mlp': lambda input_shape, num_classes: get_base_model("tabular_mlp", input_shape, num_classes),
    'tcn_multimodal': lambda input_shape, num_classes: get_base_model("tcn_multimodal", input_shape, num_classes)
}
