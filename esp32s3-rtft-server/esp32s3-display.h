#ifndef ESP32S3_DISPLAY_H
#define ESP32S3_DISPLAY_H

#include <Adafruit_ST7789.h>  // Hardware-specific library for ST7789
#include <Button.h>  // Button by Michael Adams https://github.com/madleech/Button
#include <stdint.h>

extern Adafruit_ST7789 tft;
extern uint16_t fg_color;
extern uint16_t bg_color;

void display_setup(void);
void display_invert(bool inverted);
int16_t display_get_width();
int16_t display_get_height();

void display_reset();
void display_clear();
void display_print(char *text);

void display_set_cursor(int16_t x, int16_t y);

void buttons_setup();
void buttons_flush();

bool button0_down();
bool button0_up();
bool button0_pressed();

bool button1_down();
bool button1_up();
bool button1_pressed();

bool button2_down();
bool button2_up();
bool button2_pressed();

inline void drawPixel(int16_t x, int16_t y, bool fg) {
  tft.drawPixel(x, y, fg ? fg_color : bg_color);
}

inline void setRotation(uint8_t m) { tft.setRotation(m); }

inline void drawFastVLine(int16_t x, int16_t y, int16_t h, bool fg) {
  tft.drawFastVLine(x, y, h, fg ? fg_color : bg_color);
}

inline void drawFastHLine(int16_t x, int16_t y, int16_t w, bool fg) {
  tft.drawFastHLine(x, y, w, fg ? fg_color : bg_color);
}

inline void fillRect(int16_t x, int16_t y, int16_t w, int16_t h, bool fg) {
  tft.fillRect(x, y, w, h, fg ? fg_color : bg_color);
}

inline void fillScreen(bool fg) { tft.fillScreen(fg ? fg_color : bg_color); }

inline void drawLine(int16_t x0, int16_t y0, int16_t x1, int16_t y1, bool fg) {
  tft.drawLine(x0, y0, x1, y1, fg ? fg_color : bg_color);
}

inline void drawRect(int16_t x, int16_t y, int16_t w, int16_t h, bool fg) {
  tft.drawRect(x, y, w, h, fg ? fg_color : bg_color);
}

#endif