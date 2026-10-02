import time

import cv2
import numpy as np
from tensorflow.keras.models import load_model

try:
    import serial
except ImportError:
    serial = None

PUERTO_SERIAL = "COM4"
BAUDRATE = 115200

modelo = load_model("modelo_digitos.h5")


def conectar_serial():
    if serial is None:
        print("pyserial no está instalado; se ejecutará sin enviar datos.")
        return None
    try:
        ser = serial.Serial(PUERTO_SERIAL, BAUDRATE, timeout=1)
        time.sleep(2)
        print("Conectado a ESP-A en", PUERTO_SERIAL)
        return ser
    except Exception as e:
        print("No se pudo abrir el puerto serie:", e)
        return None


def preprocesar_roi(roi_binaria):
    alto, ancho = roi_binaria.shape
    if alto == 0 or ancho == 0:
        return None

    kernel = np.ones((3, 3), np.uint8)
    roi_binaria = cv2.dilate(roi_binaria, kernel, iterations=1)

    if alto > ancho:
        nuevo_alto = 20
        nuevo_ancho = max(1, round(ancho * (20.0 / alto)))
    else:
        nuevo_ancho = 20
        nuevo_alto = max(1, round(alto * (20.0 / ancho)))

    redimensionado = cv2.resize(roi_binaria, (nuevo_ancho, nuevo_alto),
                                 interpolation=cv2.INTER_AREA)

    lienzo = np.zeros((28, 28), dtype=np.uint8)
    y_offset = (28 - nuevo_alto) // 2
    x_offset = (28 - nuevo_ancho) // 2
    lienzo[y_offset:y_offset + nuevo_alto, x_offset:x_offset + nuevo_ancho] = redimensionado

    entrada = lienzo.astype("float32") / 255.0
    return entrada.reshape(1, 28, 28, 1)


def main():
    ser = conectar_serial()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("No se pudo abrir la cámara.")
        return

    ultimo_envio = 0.0

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        borroso = cv2.GaussianBlur(gris, (5, 5), 0)
        _, binaria = cv2.threshold(
            borroso, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )

        contornos, _ = cv2.findContours(
            binaria, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if contornos:
            c = max(contornos, key=cv2.contourArea)
            if cv2.contourArea(c) > 800:
                x, y, w, h = cv2.boundingRect(c)
                margen = 20
                x0 = max(0, x - margen)
                y0 = max(0, y - margen)
                x1 = min(binaria.shape[1], x + w + margen)
                y1 = min(binaria.shape[0], y + h + margen)
                roi = binaria[y0:y1, x0:x1]

                if roi.size > 0:
                    entrada = preprocesar_roi(roi)
                    prediccion = modelo.predict(entrada, verbose=0)[0]
                    digito = int(np.argmax(prediccion))
                    confianza = float(np.max(prediccion)) * 100

                    cv2.rectangle(frame, (x0, y0), (x1, y1), (0, 255, 0), 2)
                    texto = f"Numero: {digito} ({confianza:.1f}%)"
                    cv2.putText(
                        frame, texto, (x0, max(0, y0 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2,
                    )

                    ahora = time.time()
                    if confianza > 80 and (ahora - ultimo_envio) > 1.5:
                        if ser:
                            ser.write(f"{digito}\n".encode())
                        print(f"Enviado: {digito} ({confianza:.1f}%)")
                        ultimo_envio = ahora

        cv2.imshow("Reconocimiento de digitos - presiona q para salir", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    if ser:
        ser.close()


if __name__ == "__main__":
    main()
