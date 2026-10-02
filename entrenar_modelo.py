from tensorflow.keras import layers, models
from tensorflow.keras.datasets import mnist

(x_train, y_train), (x_test, y_test) = mnist.load_data()
x_train = x_train.reshape(-1, 28, 28, 1).astype("float32") / 255.0
x_test = x_test.reshape(-1, 28, 28, 1).astype("float32") / 255.0

modelo = models.Sequential([
    layers.Conv2D(32, (3, 3), activation="relu", input_shape=(28, 28, 1)),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation="relu"),
    layers.MaxPooling2D((2, 2)),
    layers.Flatten(),
    layers.Dense(64, activation="relu"),
    layers.Dropout(0.3),
    layers.Dense(10, activation="softmax"),
])

modelo.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

modelo.summary()

modelo.fit(x_train, y_train, epochs=8, batch_size=64, validation_data=(x_test, y_test))

perdida, exactitud = modelo.evaluate(x_test, y_test, verbose=0)
print(f"\nExactitud en el set de prueba: {exactitud * 100:.2f}%")

modelo.save("modelo_digitos.h5")
print("Modelo guardado como modelo_digitos.h5")
