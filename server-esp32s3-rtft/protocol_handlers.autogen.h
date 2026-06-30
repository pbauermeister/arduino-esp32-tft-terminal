// AUTO-GENERATED from protocol/protocol.yaml — DO NOT EDIT.
// Regenerate with: make protocol-gen

#ifndef PROTOCOL_HANDLERS_AUTOGEN_H
#define PROTOCOL_HANDLERS_AUTOGEN_H

#include <stdint.h>

// Buffered replay handlers — the TFT binding for each draw command.
// Hand-written in transaction.cpp; a missing one is a link error.
void replay_print(const char *text);
void replay_clearDisplay();
void replay_clear();
void replay_home();
void replay_setFgColor(int r, int g, int b);
void replay_setBgColor(int r, int g, int b);
void replay_drawPixel(int16_t x, int16_t y, int16_t color);
void replay_setRotation(int m);
void replay_invertDisplay(bool inv);
void replay_drawFastVLine(int16_t x, int16_t y, int16_t h, int color);
void replay_drawFastHLine(int16_t x, int16_t y, int16_t w, int color);
void replay_fillScreen(int color);
void replay_drawLine(int16_t x0, int16_t y0, int16_t x1, int16_t y1, int color);
void replay_drawRect(int16_t x, int16_t y, int16_t w, int16_t h, int color);
void replay_fillRect(int16_t x, int16_t y, int16_t w, int16_t h, int color);
void replay_drawCircle(int16_t x, int16_t y, int16_t r, int color);
void replay_fillCircle(int16_t x, int16_t y, int16_t r, int color);
void replay_drawTriangle(int16_t x0, int16_t y0, int16_t x1, int16_t y1,
                         int16_t x2, int16_t y2, int color);
void replay_fillTriangle(int16_t x0, int16_t y0, int16_t x1, int16_t y1,
                         int16_t x2, int16_t y2, int color);
void replay_drawRoundRect(int16_t x, int16_t y, int16_t w, int16_t h, int16_t r,
                          int color);
void replay_fillRoundRect(int16_t x, int16_t y, int16_t w, int16_t h, int16_t r,
                          int color);
void replay_drawChar(int16_t x, int16_t y, unsigned char c, bool fg, bool bg,
                     int8_t size);
void replay_setTextSize(int sx, int sy);
void replay_setCursor(int16_t x, int16_t y);
void replay_setTextColor(int r, int g, int b);
void replay_setTextWrap(bool w);

// Immediate command handlers — return the response string.
// Hand-written in command.cpp.
const char *handle_reboot();
const char *handle_reset();
const char *handle_display();
const char *handle_autoDisplay(bool on);
const char *handle_autoReadButtons(bool on);
const char *handle_version();
const char *handle_width();
const char *handle_height();
const char *handle_getPrintMaxLength();
const char *handle_getRotation();
const char *handle_getCursorX();
const char *handle_getCursorY();
const char *handle_getTextBounds(int16_t x, int16_t y, const char *text);
const char *handle_readButtons();
const char *handle_waitButton(int during, int up);
const char *handle_monitorButtons(int during, int interval);
const char *handle_watchButtons(int during, int interval);
const char *handle_test();
const char *handle_hardcopy();

#endif  // PROTOCOL_HANDLERS_AUTOGEN_H
