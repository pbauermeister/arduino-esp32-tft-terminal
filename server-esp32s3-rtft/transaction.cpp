#include "transaction.h"

#include "command.h"
#include "esp32s3-display.h"
#include "protocol_handlers.autogen.h"

// --- Buffered replay handlers (declared in protocol_handlers.autogen.h) -----
// Each maps a buffered command's stored args to its TFT binding. Bodies are
// hand-written; the generated dispatch below calls them.

void replay_print(const char *text) { display_print((char *)text); }
void replay_clearDisplay() { display_clear(); }
void replay_clear() { display_clear(); }
void replay_home() { set_cursor(0, 0); }
void replay_setFgColor(int r, int g, int b) { set_fg_color(r, g, b); }
void replay_setBgColor(int r, int g, int b) { set_bg_color(r, g, b); }
void replay_drawPixel(int16_t x, int16_t y, int16_t color) {
    draw_pixel(x, y, color);
}
void replay_setRotation(int m) { set_rotation(m); }
void replay_invertDisplay(bool inv) { invert_display(inv); }
void replay_drawFastVLine(int16_t x, int16_t y, int16_t h, int color) {
    draw_fast_vline(x, y, h, color);
}
void replay_drawFastHLine(int16_t x, int16_t y, int16_t w, int color) {
    draw_fast_hline(x, y, w, color);
}
void replay_fillScreen(int color) { fill_screen(color); }
void replay_drawLine(int16_t x0, int16_t y0, int16_t x1, int16_t y1,
                     int color) {
    draw_line(x0, y0, x1, y1, color);
}
void replay_drawRect(int16_t x, int16_t y, int16_t w, int16_t h, int color) {
    draw_rect(x, y, w, h, color);
}
void replay_fillRect(int16_t x, int16_t y, int16_t w, int16_t h, int color) {
    fill_rect(x, y, w, h, color);
}
void replay_drawCircle(int16_t x, int16_t y, int16_t r, int color) {
    draw_circle(x, y, r, color);
}
void replay_fillCircle(int16_t x, int16_t y, int16_t r, int color) {
    fill_circle(x, y, r, color);
}
void replay_drawTriangle(int16_t x0, int16_t y0, int16_t x1, int16_t y1,
                         int16_t x2, int16_t y2, int color) {
    draw_triangle(x0, y0, x1, y1, x2, y2, color);
}
void replay_fillTriangle(int16_t x0, int16_t y0, int16_t x1, int16_t y1,
                         int16_t x2, int16_t y2, int color) {
    fill_triangle(x0, y0, x1, y1, x2, y2, color);
}
void replay_drawRoundRect(int16_t x, int16_t y, int16_t w, int16_t h, int16_t r,
                          int color) {
    draw_round_rect(x, y, w, h, r, color);
}
void replay_fillRoundRect(int16_t x, int16_t y, int16_t w, int16_t h, int16_t r,
                          int color) {
    fill_round_rect(x, y, w, h, r, color);
}
void replay_drawChar(int16_t x, int16_t y, unsigned char c, bool fg, bool bg,
                     int8_t size) {
    draw_char(x, y, c, fg, bg, size);
}
void replay_setTextSize(int sx, int sy) { set_text_size(sx, sy); }
void replay_setCursor(int16_t x, int16_t y) { set_cursor(x, y); }
void replay_setTextColor(int r, int g, int b) { set_text_color(r, g, b); }
void replay_setTextWrap(bool w) { set_text_wrap(w); }

void Transaction::do_action(Action *action) {
    switch (action->hash) {
#include "replay_dispatch.autogen.inc"

        default:
            break;
    }
}

void Transaction::commit() {
    for (int i = 0; i < next; ++i) {
        Action *action = &actions[i];
        do_action(action);
    }
    next = 0;
}

void Transaction::add() {
    if (!enabled) {
        do_action(&actions[next]);
        return;
    }

    next++;  // full-buffer flush is handled in action() (flush, then reuse slot
             // 0)
}
