// Board: "Adafruit Feather ESP32-S3 Reverse TFT"
// https://learn.adafruit.com/esp32-s3-reverse-tft-feather/arduino-ide-setup-2
//
// Flashing:
// 1. IDE: Click Upload
//    IDE: Wait for "Hard resetting via RTS pin..."
// 2. Board: Click Reset

#include <Adafruit_ST7789.h>
#include <Arduino.h>

#include "command.h"
#include "config.h"
#include "esp32s3-display.h"

#define BOARD_NAME "ARDUINO_ADAFRUIT_FEATHER_ESP32S3_REVERSE_TFT"

Config config;
bool inverted = true;
int counter = 0;
char input_buffer[BUFFER_LENGTH];

void setup(void) {
  // TFT
  display_setup();
  // delay(1000);
  // display_reset();

  // Serial
  Serial.begin(115200);
  Serial.print("# Board: ");
  Serial.println(BOARD_NAME);

  Serial.print("# TFT begun: ");
  Serial.print(display_get_width());
  Serial.print("x");
  Serial.println(display_get_height());

  Serial.println("READY");

  // Pins
  pinMode(LED_BUILTIN, OUTPUT);  // init LED *AFTER* Serial
  buttons_setup();

  config = Config{display_get_width(), display_get_height()};
  // display_test(input_buffer);
}

char *get_input() {
  size_t len = sizeof(input_buffer);
  len = Serial.readBytesUntil('\n', input_buffer, len - 1);
  input_buffer[len] = 0;
  return input_buffer;
}

void loop() {
  if (++counter > 50) {
    // Serial.print(F("Inverted: "));
    // Serial.println(inverted);
    // display_invert(inverted);
    digitalWrite(LED_BUILTIN, inverted ? HIGH : LOW);
    counter = 0;
    inverted = !inverted;
  }

  if (Serial.available() > 0) {
    char *buffer = get_input();
    const char *result = interpret(buffer, config);
    if (result) Serial.println(result);
  } else {
    delay(10);
  }

  yield();
}
