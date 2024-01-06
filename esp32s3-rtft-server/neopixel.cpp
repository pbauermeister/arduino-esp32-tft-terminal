#include "neopixel.h"

#include <Adafruit_NeoPixel.h>
#include <Adafruit_TestBed.h>
#include <math.h>
#include <stdint.h>

// for NeoPixel
extern Adafruit_TestBed TB;

NeoPixel::NeoPixel() {}

void NeoPixel::init() {
  TB.neopixelPin = PIN_NEOPIXEL;
  TB.neopixelNum = 1;
  TB.begin();
  TB.setColor(0);
}

uint32_t NeoPixel::hsv_to_rgb(uint16_t hue, uint8_t sat, uint8_t val) {
  hue = fmin(hue, 360);
  sat = fmin(sat, 100);
  val = fmin(val, 100);

  NUM s = sat / (NUM)100;
  NUM v = val / (NUM)100;
  NUM c = s * v;
  NUM x = c * (1 - fabs(fmod(hue / (NUM)60, 2) - 1));
  NUM m = v - c;
  NUM r, g, b;
  if (hue >= 0 && hue < 60) {
    r = c, g = x, b = 0;
  } else if (hue >= 60 && hue < 120) {
    r = x, g = c, b = 0;
  } else if (hue >= 120 && hue < 180) {
    r = 0, g = c, b = x;
  } else if (hue >= 180 && hue < 240) {
    r = 0, g = x, b = c;
  } else if (hue >= 240 && hue < 300) {
    r = x, g = 0, b = c;
  } else {
    r = c, g = 0, b = x;
  }

  int red = (r + m) * 255;
  int green = (g + m) * 255;
  int blue = (b + m) * 255;
  return (red & 0xff) << 16 | (green & 0xff) << 8 | (blue & 0xff);
}

void NeoPixel::set_color(NUM hue, NUM sat, NUM val) {
  uint32_t color = hsv_to_rgb(hue, sat, val);
  TB.setColor(color);
}

void NeoPixel::set_color(uint8_t r, uint8_t g, uint8_t b) {
  uint32_t color = r << 16 | g << 8 | b;
  TB.setColor(color);
}
