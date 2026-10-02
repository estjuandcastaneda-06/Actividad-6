# Actividad-6
teclado matricial y numeros 

# Teclado I2C + Brazo Robótico (PyBullet) / Reconocimiento de Dígitos (OpenCV + CNN) + SPI + LCD

Proyecto desarrollado para la asignatura de Mecatrónica — Universidad Militar Nueva Granada.
Consta de dos puntos independientes que combinan electrónica embebida (ESP32), visión por
computador y simulación robótica.

---

## Índice

- [Punto 1 — Teclado + LCD + Simulación de brazo robótico](#punto-1)
- [Punto 2 — Reconocimiento de dígitos con cámara + SPI + LCD](#punto-2)
- [Decisiones de diseño y cambios respecto al planteamiento original](#decisiones)
- [Problemas encontrados durante el desarrollo y cómo se resolvieron](#problemas)

---

<a name="punto-1"></a>
## Punto 1 — Teclado + LCD + Simulación de brazo robótico

### Qué hace

Un ESP32 lee un teclado matricial 4x4 y muestra la tecla presionada en una pantalla LCD 16x2.
Cuando la tecla presionada es un dígito (0-9), el ESP32 lo envía por el puerto serie (USB) a un
programa de Python. Ese programa controla un brazo robótico simulado en PyBullet, que traza una
trayectoria sobre un plano virtual imitando la forma del número recibido, dejando un rastro visual.
La tecla `*` funciona como comando para borrar el lienzo y empezar de nuevo.

### Componentes

| Cantidad | Componente |
|---|---|
| 1 | ESP32 DevKit |
| 1 | Teclado matricial 4x4 (membrana) |
| 1 | Pantalla LCD 16x2 con backpack I2C (PCF8574) |
| 1 | Protoboard |
| ~15 | Cables jumper |
| 1 | Cable USB |
| 1 | PC con Python 3 |

### Conexión física

**Teclado (directo a GPIO del ESP32):**

| Teclado | ESP32 |
|---|---|
| Fila 1 | GPIO13 |
| Fila 2 | GPIO12 |
| Fila 3 | GPIO14 |
| Fila 4 | GPIO27 |
| Columna 1 | GPIO26 |
| Columna 2 | GPIO25 |
| Columna 3 | GPIO33 |
| Columna 4 | GPIO32 |

**LCD (I2C):** SDA → GPIO21, SCL → GPIO22, VCC → 5V, GND → GND. Dirección típica: `0x27`.

### Cómo funciona el código

**`ESP32_Teclado_LCD.ino`**
Usa la librería `Keypad` para escanear las 4 filas y 4 columnas del teclado: pone cada fila en
bajo de a una y revisa qué columna responde, identificando así la tecla presionada. Al detectar
una tecla, la muestra en la LCD (librería `LiquidCrystal_I2C`, comunicación I2C). Si la tecla es
un dígito 0-9, lo envía por `Serial.println()` al puerto USB. Si la tecla es `*`, envía ese mismo
carácter como comando de "limpiar".

**`simulacion_pybullet.py`**
Abre una simulación física con el brazo robótico KUKA IIWA (incluido en `pybullet_data`, usado
como brazo genérico de 7 grados de libertad). Cada dígito tiene asociada una lista de puntos
(coordenadas normalizadas 0-1) que describen, a mano alzada, la forma de ese número con un trazo
