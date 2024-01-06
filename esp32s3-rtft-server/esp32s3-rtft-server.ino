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
#include "neopixel.h"

#define BOARD_NAME "ARDUINO_ADAFRUIT_FEATHER_ESP32S3_REVERSE_TFT"

Config config;
bool inverted = true;
int counter = 0;
char input_buffer[BUFFER_LENGTH];

NeoPixel np = NeoPixel();

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
  np.init();

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
  if (++counter % 50 == 0) {
    digitalWrite(LED_BUILTIN, inverted ? HIGH : LOW);
    inverted = !inverted;
  }

  if (Serial.available() > 0) {
    char *buffer = get_input();
    const char *result = interpret(buffer, config);
    if (result) Serial.println(result);
  } else {
    delay(10);
  }

  // rotate hue and pusate value
  const NUM k = (NUM)200 / (NUM)360;
  const NUM val_period = 2.00 * k;
  const NUM hue_period = .002 / k;
  int v = (int)(counter * val_period) % 200;
  if (v > 100) v = 200 - v;
  int h = (int)(counter * hue_period) % 360;
  np.set_color((NUM)h, (NUM)100, (NUM)v / 2 + 1);

  // cycle r, g, b
  // uint8_t r = triangle(counter / 1);
  // uint8_t g = triangle(counter / 3);
  // uint8_t b = triangle(counter / 5);
  // np.set_color(r, g, b);

  yield();
}

uint8_t triangle(int x) {
  int y = x % 512;
  return y <= 255 ? y : 511 - y;
}