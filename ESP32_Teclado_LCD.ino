#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Keypad.h>

#define LCD_ADDR 0x27

LiquidCrystal_I2C lcd(LCD_ADDR, 16, 2);

const byte FILAS = 4;
const byte COLUMNAS = 4;

char teclas[FILAS][COLUMNAS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};

byte pinesFilas[FILAS] = {13, 12, 14, 27};
byte pinesColumnas[COLUMNAS] = {26, 25, 33, 32};

Keypad teclado = Keypad(makeKeymap(teclas), pinesFilas, pinesColumnas, FILAS, COLUMNAS);

void setup() {
  Serial.begin(115200);
  Wire.begin();

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Ingrese digito:");
}

void loop() {
  char tecla = teclado.getKey();

  if (tecla) {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Tecla: ");
    lcd.print(tecla);

    if (tecla >= '0' && tecla <= '9') {
      Serial.println(tecla);
      lcd.setCursor(0, 1);
      lcd.print("Enviado a PC");
    } else if (tecla == '*') {
      Serial.println('*');
      lcd.setCursor(0, 1);
      lcd.print("Lienzo limpio");
    }
  }
}
