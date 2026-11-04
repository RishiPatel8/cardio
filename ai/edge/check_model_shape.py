import tensorflow as tf
model = tf.keras.models.load_model("d:/cardiogaurd/ai/artifacts/models/cnn_lstm/cnn_lstm.h5")
print(model.input_shape)
