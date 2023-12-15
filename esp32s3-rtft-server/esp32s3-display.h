#ifndef ESP32S3_DISPLAY_H
#define ESP32S3_DISPLAY_H

#include <Button.h>  // Button by Michael Adams https://github.com/madleech/Button
#include <stdint.h>

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

void setRotation(uint8_t m);

void drawPixel(int16_t x, int16_t heyight, bool fg);

void drawFastVLine(int16_t x, int16_t y, int16_t h, bool fg);
void drawFastHLine(int16_t x, int16_t y, int16_t w, bool fg);

void fillRect(int16_t x, int16_t y, int16_t w, int16_t h, bool fg);

#endif