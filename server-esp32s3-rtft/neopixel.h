#ifndef NEOPIXEL_H
#define NEOPIXEL_H

#include <stdint.h>

#define NUM float

class NeoPixel {
 public:
  NeoPixel();
  void init();
  void set_color(NUM hue, NUM sat, NUM val);
  void set_color(uint8_t r, uint8_t g, uint8_t b);

 private:
  uint32_t hsv_to_rgb(uint16_t hue, uint8_t sat, uint8_t val);
};

#endif  // NEOPIXEL_H