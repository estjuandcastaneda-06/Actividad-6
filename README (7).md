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
continuo. Al recibir un dígito por el puerto serie, el script recorre esos puntos: para cada uno,
calcula la cinemática inversa (`calculateInverseKinematics`) para saber qué ángulos deben tomar las
articulaciones del brazo para que el efector final llegue a esa posición, mueve los motores hacia
esos ángulos, y dibuja una línea roja (`addUserDebugLine`) entre la posición anterior y la actual
del efector, simulando el trazo del dibujo. Al recibir el comando `*`, borra todas las líneas
dibujadas (`removeAllUserDebugItems`).

### Cómo se ejecuta

```bash
# 1. Cargar ESP32_Teclado_LCD.ino al ESP32 desde Arduino IDE
#    (requiere las librerías Keypad y LiquidCrystal_I2C)

# 2. En el PC:
pip install pybullet pyserial numpy

# 3. Editar PUERTO_SERIAL en simulacion_pybullet.py con el puerto del ESP32

# 4. Ejecutar:
python simulacion_pybullet.py
```

---

<a name="punto-2"></a>
## Punto 2 — Reconocimiento de dígitos con cámara + SPI + LCD

### Qué hace

Un programa de Python usa la cámara del PC para capturar un dígito escrito a mano sobre papel,
lo aísla con OpenCV, lo clasifica con una red neuronal convolucional (CNN) entrenada sobre el
dataset MNIST, y envía el resultado por el puerto serie a un primer ESP32 (maestro SPI). Este lo
retransmite por el bus SPI a un segundo ESP32 (esclavo SPI), que muestra el número en una pantalla
LCD 16x2 I2C.

### Componentes

| Cantidad | Componente |
|---|---|
| 2 | ESP32 DevKit (ESP-A: maestro SPI, ESP-B: esclavo SPI) |
| 1 | Pantalla LCD 16x2 con backpack I2C |
| 1 | Protoboard |
| ~10 | Cables jumper |
| 2 | Cables USB |
| 1 | PC con cámara web |

### Conexión física

**SPI entre ESP-A (maestro) y ESP-B (esclavo):**

| ESP-A | ESP-B |
|---|---|
| GPIO18 (SCK) | GPIO14 (SCK) |
| GPIO19 (MISO) | GPIO12 (MISO) |
| GPIO23 (MOSI) | GPIO13 (MOSI) |
| GPIO5 (CS) | GPIO15 (CS) |
| GND | GND (obligatorio: referencia de tierra común) |

**LCD (I2C) en el ESP-B:** SDA → GPIO21, SCL → GPIO22, VCC → 5V, GND → GND. Dirección: `0x27`.

### Cómo funciona el código

**`entrenar_modelo.py`**
Carga el dataset MNIST (70.000 imágenes de dígitos escritos a mano, 28x28 píxeles en escala de
grises). Define una CNN con dos bloques de convolución + max pooling (para extraer características
visuales como bordes y curvas) seguidos de capas densas que clasifican la imagen en una de 10
categorías (0-9). Entrena el modelo durante 8 épocas y lo guarda como `modelo_digitos.h5`. Este
script solo se corre una vez.

**`reconocimiento_digitos.py`**
Captura video de la cámara en un bucle continuo. Por cada cuadro:
1. Convierte la imagen a escala de grises y aplica desenfoque gaussiano (reduce ruido).
2. Aplica umbralización binaria invertida con el método de Otsu (`THRESH_BINARY_INV + THRESH_OTSU`),
   que separa automáticamente el trazo oscuro del fondo claro, dejando el dígito en blanco sobre
   fondo negro — igual que las imágenes de MNIST.
3. Busca contornos y toma el de mayor área (asumiendo que es el dígito).
4. Recorta esa región con un margen de seguridad alrededor.
5. **Preprocesa el recorte para que coincida con el formato de entrenamiento**: redimensiona
   manteniendo la proporción (el lado más largo queda en 20 píxeles, nunca se deforma el número),
   engrosa levemente el trazo (los trazos de pluma en cámara son más delgados que los de MNIST), y
   centra el resultado dentro de un lienzo negro de 28x28 píxeles. Este paso fue clave: redimensionar
   directo a 28x28 sin mantener proporción ni centrar distorsionaba el número y la red siempre
   terminaba prediciendo la misma clase.
6. Pasa la imagen preprocesada al modelo (`modelo.predict`) y obtiene el dígito con mayor
   probabilidad y su porcentaje de confianza.
7. Si la confianza supera 80% y han pasado más de 1.5 segundos desde el último envío (para no saturar
   el puerto serie), envía el dígito como texto por `pyserial` al ESP-A.

**`ESP32_A_Maestro.ino`**
Escucha el puerto Serial (USB) de forma continua. Al recibir una línea de texto que empieza con un
dígito, la convierte a número y la envía por el bus SPI usando la librería `SPI` estándar del
ESP32, actuando como maestro: abre la transacción, activa el Chip Select, transfiere el byte, y
cierra la transacción.

**`ESP32_B_Esclavo.ino`**
Usa la librería `ESP32SPISlave` para operar como esclavo SPI, ya que el ESP32 no soporta modo
esclavo con la librería `SPI` estándar de Arduino. El método `transfer()` de esta librería se queda
esperando (bloqueado) hasta que el maestro inicia una transacción, y devuelve cuántos bytes se
recibieron realmente. Al recibir un byte válido (0-9), lo muestra en la LCD I2C.

### Cómo se ejecuta

```bash
# 1. Entrenar el modelo (una sola vez):
pip install tensorflow numpy
python entrenar_modelo.py

# 2. Cargar ESP32_B_Esclavo.ino al ESP-B desde Arduino IDE
#    (requiere las librerías ESP32SPISlave y LiquidCrystal_I2C)

# 3. Cargar ESP32_A_Maestro.ino al ESP-A

# 4. Editar PUERTO_SERIAL en reconocimiento_digitos.py con el puerto del ESP-A

# 5. Ejecutar:
pip install opencv-python pyserial
python reconocimiento_digitos.py
```

---

<a name="decisiones"></a>
## Decisiones de diseño y cambios respecto al planteamiento original

El enunciado original de la actividad especificaba un teclado conectado por un módulo expansor I2C
(PCF8574) y una pantalla OLED I2C para el Punto 2. Por disponibilidad de material, se hicieron dos
adaptaciones:

- **Teclado**: en vez de leerlo a través de un PCF8574, se conectó directo a 8 pines GPIO del ESP32
  y se leyó con la librería `Keypad`. El LCD sí se mantuvo por I2C.
- **Pantalla del Punto 2**: se reemplazó la OLED por la misma LCD 16x2 I2C usada en el Punto 1, para
  no depender de un componente adicional.

Ambos cambios se hicieron con el visto bueno de que, si el criterio de evaluación exige
específicamente esos componentes, se debe confirmar con el docente si la adaptación es aceptable.

<a name="problemas"></a>
## Problemas encontrados durante el desarrollo y cómo se resolvieron

- **`pybullet` no instalaba en Windows** (pedía Microsoft C++ Build Tools): causado por usar una
  versión de Python (3.14) demasiado nueva, sin instalador precompilado todavía. Se resolvió creando
  un ambiente de Anaconda con Python 3.11 e instalando `pybullet` desde el canal `conda-forge`.
- **Puerto serie bloqueado (`PermissionError: Access is denied`)**: ocurre cuando dos programas
  intentan abrir el mismo puerto COM a la vez (típicamente el Monitor Serial de Arduino IDE abierto
  junto con el script de Python). Se resuelve cerrando cualquier otro programa que tenga el puerto
  abierto antes de correr el script.
- **`ESP32SPISlave.available()` no existe**: la versión de la librería instalada desde el gestor de
  librerías de Arduino cambió su API respecto a versiones anteriores. Se resolvió usando directamente
  `transfer()`, que bloquea la ejecución hasta que el maestro envía datos, en vez de sondear con
  `available()`.
- **TensorFlow bloqueado por Windows (`Application Control policy has blocked this file`)**: causado
  por la función "Smart App Control" de Windows 11, que bloquea archivos no reconocidos aunque sean
  legítimos. Se resolvió desactivando esa función desde Seguridad de Windows → Control de aplicaciones
  y navegador.
- **El modelo siempre predecía el mismo dígito (6 o 7) sin importar lo que se mostrara**: causado por
  un preprocesamiento de imagen que no coincidía con el formato de entrenamiento de MNIST (se
  redimensionaba el recorte directo a 28x28 sin mantener la proporción, deformando el número, y sin
  centrarlo con margen como sí tienen las imágenes originales). Se corrigió el preprocesamiento para
  redimensionar manteniendo la proporción y centrar el resultado en un lienzo de 28x28, replicando
  el proceso real usado para construir el dataset MNIST.
