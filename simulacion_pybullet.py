import time
import numpy as np
import pybullet as p
import pybullet_data
import serial

PUERTO_SERIAL = "COM3"
BAUDRATE = 115200

TRAYECTORIAS_DIGITOS = {
    '0': [(0.5, 1), (0.8, 0.8), (0.8, 0.2), (0.5, 0), (0.2, 0.2), (0.2, 0.8), (0.5, 1)],
    '1': [(0.5, 1), (0.5, 0)],
    '2': [(0.2, 0.8), (0.5, 1), (0.8, 0.8), (0.8, 0.6), (0.2, 0.1), (0.8, 0.1)],
    '3': [(0.2, 1), (0.8, 1), (0.5, 0.55), (0.8, 0.4), (0.8, 0.1), (0.2, 0)],
    '4': [(0.7, 1), (0.2, 0.35), (0.8, 0.35), (0.6, 1), (0.6, 0)],
    '5': [(0.8, 1), (0.2, 1), (0.2, 0.55), (0.7, 0.55), (0.8, 0.3), (0.6, 0), (0.2, 0.1)],
    '6': [(0.7, 1), (0.3, 0.5), (0.2, 0.2), (0.4, 0), (0.8, 0.15), (0.7, 0.45), (0.3, 0.5)],
    '7': [(0.2, 1), (0.8, 1), (0.4, 0)],
    '8': [(0.5, 0.55), (0.25, 0.75), (0.5, 1), (0.75, 0.75), (0.5, 0.55),
          (0.2, 0.25), (0.5, 0), (0.8, 0.25), (0.5, 0.55)],
    '9': [(0.7, 0.5), (0.3, 0.55), (0.2, 0.8), (0.4, 1), (0.7, 0.85), (0.7, 0.5), (0.5, 0)],
}


def conectar_esp32():
    try:
        ser = serial.Serial(PUERTO_SERIAL, BAUDRATE, timeout=1)
        time.sleep(2)
        print("Conectado al ESP32 en", PUERTO_SERIAL)
        return ser
    except Exception as e:
        print("No se pudo abrir el puerto serie:", e)
        print("La simulación seguirá abierta; revisa el puerto y reinicia el script.")
        return None


def iniciar_simulacion():
    p.connect(p.GUI)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)
    p.loadURDF("plane.urdf")
    brazo_id = p.loadURDF("kuka_iiwa/model.urdf", [0, 0, 0], useFixedBase=True)
    p.addUserDebugText("Lienzo de dibujo", [0.5, -0.2, 0.65], textSize=1.2)
    return brazo_id


def limpiar_lienzo():
    p.removeAllUserDebugItems()
    p.addUserDebugText("Lienzo de dibujo", [0.5, -0.2, 0.65], textSize=1.2)
    print("Lienzo limpiado")


def dibujar_digito(brazo_id, digito):
    if digito not in TRAYECTORIAS_DIGITOS:
        return

    id_efector = 6
    origen = np.array([0.5, 0.0, 0.3])
    ancho, alto = 0.25, 0.35

    punto_previo = None
    for (u, v) in TRAYECTORIAS_DIGITOS[digito]:
        objetivo = origen + np.array([0.0, (u - 0.5) * ancho, v * alto])
        angulos = p.calculateInverseKinematics(brazo_id, id_efector, objetivo.tolist())

        for i in range(len(angulos)):
            p.setJointMotorControl2(brazo_id, i, p.POSITION_CONTROL,
                                     targetPosition=angulos[i], force=200)

        for _ in range(60):
            p.stepSimulation()
            time.sleep(1.0 / 240.0)

        estado = p.getLinkState(brazo_id, id_efector)
        posicion_actual = estado[0]

        if punto_previo is not None:
            p.addUserDebugLine(punto_previo, posicion_actual, [1, 0, 0],
                                lineWidth=3, lifeTime=0)
        punto_previo = posicion_actual


def main():
    brazo_id = iniciar_simulacion()
    ser = conectar_esp32()
    print("Esperando dígitos desde el ESP32 (teclado I2C)... Ctrl+C para salir.")

    try:
        while True:
            p.stepSimulation()
            if ser and ser.in_waiting:
                linea = ser.readline().decode(errors="ignore").strip()
                if linea == "*":
                    limpiar_lienzo()
                elif linea and linea[0] in TRAYECTORIAS_DIGITOS:
                    print("Dígito recibido:", linea[0])
                    dibujar_digito(brazo_id, linea[0])
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        if ser:
            ser.close()
        p.disconnect()


if __name__ == "__main__":
    main()
