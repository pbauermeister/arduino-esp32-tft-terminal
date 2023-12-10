#ifndef ESP32S3_DISPLAY_H
#define ESP32S3_DISPLAY_H

#include <stdint.h>

void display_setup(void);
void display_invert(bool inverted);
int16_t display_get_width();
int16_t display_get_height();

void display_reset();
void display_clear();
void display_print(char *text);

void display_set_cursor(int16_t x, int16_t y);

#endif