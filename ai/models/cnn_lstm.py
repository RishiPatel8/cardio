import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, MaxPooling1D, LSTM, Dense, Dropout, Flatten

def build_cnn(input_shape, num_classes=2):
    model = Sequential([
        Conv1D(filters=32, kernel_size=5, activation='relu', input_shape=input_shape),
        MaxPooling1D(pool_size=2),
        Conv1D(filters=64, kernel_size=3, activation='relu'),
        MaxPooling1D(pool_size=2),
        Flatten(),
        Dropout(0.5),
        Dense(32, activation='relu'),
        Dense(num_classes, activation='softmax' if num_classes > 1 else 'sigmoid')
    ])
    
    model.compile(optimizer='adam', 
                  loss='sparse_categorical_crossentropy' if num_classes > 2 else 'binary_crossentropy',
                  metrics=['accuracy'])
    return model

def build_lstm(input_shape, num_classes=2):
    model = Sequential([
        LSTM(64, return_sequences=False, input_shape=input_shape),
        Dropout(0.5),
        Dense(32, activation='relu'),
        Dense(num_classes, activation='softmax' if num_classes > 1 else 'sigmoid')
    ])
    
    model.compile(optimizer='adam', 
                  loss='sparse_categorical_crossentropy' if num_classes > 2 else 'binary_crossentropy',
                  metrics=['accuracy'])
    return model

def build_cnn_lstm(input_shape, num_classes=2):
    model = Sequential([
        Conv1D(filters=32, kernel_size=5, activation='relu', input_shape=input_shape),
        MaxPooling1D(pool_size=2),
        Conv1D(filters=64, kernel_size=3, activation='relu'),
        MaxPooling1D(pool_size=2),
        LSTM(64, return_sequences=False),
        Dropout(0.5),
        Dense(32, activation='relu'),
        Dense(num_classes, activation='softmax' if num_classes > 1 else 'sigmoid')
    ])
    
    model.compile(optimizer='adam', 
                  loss='sparse_categorical_crossentropy' if num_classes > 2 else 'binary_crossentropy',
                  metrics=['accuracy'])
    return model
