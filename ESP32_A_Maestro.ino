#include <SPI.h>

#define PIN_CS 5

void enviarPorSPI(uint8_t dato) {
  SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
  digitalWrite(PIN_CS, LOW);
  SPI.transfer(dato);
  digitalWrite(PIN_CS, HIGH);
  SPI.endTransaction();
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_CS, OUTPUT);
  digitalWrite(PIN_CS, HIGH);
  SPI.begin();
  Serial.println("ESP-A listo (maestro SPI)");
}

void loop() {
  if (Serial.available()) {
    String linea = Serial.readStringUntil('\n');
    linea.trim();

    if (linea.length() > 0 && isDigit(linea[0])) {
      uint8_t digito = linea[0] - '0';
      enviarPorSPI(digito);
      Serial.print("Enviado por SPI: ");
      Serial.println(digito);
    }
  }
}
