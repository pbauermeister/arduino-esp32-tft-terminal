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
void display_test();

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

inline void invertDisplay(bool inv) { tft.invertDisplay(!inv); }

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

inline void drawCircle(int16_t x, int16_t y, int16_t r, bool fg) {
  tft.drawCircle(x, y, r, fg ? fg_color : bg_color);
}

inline void fillCircle(int16_t x, int16_t y, int16_t r, bool fg) {
  tft.fillCircle(x, y, r, fg ? fg_color : bg_color);
}

inline void drawTriangle(int16_t x0, int16_t y0, int16_t x1, int16_t y1,
                         int16_t x2, int16_t y2, bool fg) {
  tft.drawTriangle(x0, y0, x1, y1, x2, y2, fg ? fg_color : bg_color);
}

inline void fillTriangle(int16_t x0, int16_t y0, int16_t x1, int16_t y1,
                         int16_t x2, int16_t y2, bool fg) {
  tft.fillTriangle(x0, y0, x1, y1, x2, y2, fg ? fg_color : bg_color);
}

inline void drawRoundRect(int16_t x, int16_t y, int16_t w, int16_t h, int16_t r,
                          bool fg) {
  tft.drawRoundRect(x, y, w, h, r, fg ? fg_color : bg_color);
}

inline void fillRoundRect(int16_t x, int16_t y, int16_t w, int16_t h, int16_t r,
                          bool fg) {
  tft.fillRoundRect(x, y, w, h, r, fg ? fg_color : bg_color);
}

inline void drawChar(int16_t x, int16_t y, unsigned char c, bool fg, bool bg,
                     uint8_t size) {
  uint16_t fgc = fg ? fg_color : bg_color;
  uint16_t bgc = bg ? fg_color : bg_color;
  tft.drawChar(x, y, c, fgc, bgc, size);
}

inline void getTextBounds(const char *str, int16_t x, int16_t y, int16_t *x1,
                          int16_t *y1, uint16_t *w, uint16_t *h) {
  //  tft.getTextBounds(str, x, y, x1, y1, w, h);
}

inline void setTextSize(uint8_t s, uint8_t sy) {
  if (sy == -1) {
    tft.setTextSize(s);
  } else {
    tft.setTextSize(s, sy);
  }
}

inline void setCursor(int16_t x, int16_t y) { tft.setCursor(x, y); }

inline void setTextColor(bool fg) {
  tft.setTextColor(fg ? fg_color : bg_color);
}

inline void setTextWrap(bool enabled) { tft.setTextWrap(enabled); }

inline uint8_t getRotation() { return tft.getRotation(); }

inline int16_t getCursorX() { return tft.getCursorX(); }

inline int16_t getCursorY() { return tft.getCursorY(); }

#endif