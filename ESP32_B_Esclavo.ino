#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <ESP32SPISlave.h>

#define LCD_ADDR 0x27

LiquidCrystal_I2C lcd(LCD_ADDR, 16, 2);
ESP32SPISlave esclavoSPI;

static const uint32_t TAM_BUFFER = 8;
uint8_t bufferRx[TAM_BUFFER];
uint8_t bufferTx[TAM_BUFFER];

void mostrarDigito(uint8_t digito) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Digito recibido:");
  lcd.setCursor(0, 1);
  lcd.print(digito);
}

void setup() {
  Serial.begin(115200);
  Wire.begin();

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Esperando SPI...");

  esclavoSPI.setDataMode(SPI_MODE0);
  esclavoSPI.begin(HSPI);

  memset(bufferTx, 0, TAM_BUFFER);
  Serial.println("ESP-B listo (esclavo SPI)");
}

void loop() {
  size_t recibidos = esclavoSPI.transfer(bufferTx, bufferRx, TAM_BUFFER);

  if (recibidos > 0) {
    uint8_t digito = bufferRx[0];
    if (digito <= 9) {
      Serial.print("Digito recibido por SPI: ");
      Serial.println(digito);
      mostrarDigito(digito);
    }
  }
}
