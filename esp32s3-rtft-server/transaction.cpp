#include "transaction.h"

#include "command.h"
#include "esp32s3-display.h"

void Transaction::do_action(Action *action) {
  switch (action->hash) {
    case hash("print"): {  // print HELLO\n
      display_print(action->str);
      break;
    }

    case hash("clearDisplay"): {  // clearDisplay
      display_clear();
      break;
    }

    case hash("clear"): {  // clear
      display_clear();
      break;
    }

    case hash("home"): {  // home
      display_set_cursor(0, 0);
      break;
    }

    case hash("setFgColor"): {  // setFgColor 255 128 128
      int r = (int)action->args[0];
      int g = (int)action->args[1];
      int b = (int)action->args[2];
      set_fg_color(r, g, b);
      break;
    }

    case hash("setBgColor"): {  // setBgColor 255 128 128
      int r = (int)action->args[0];
      int g = (int)action->args[1];
      int b = (int)action->args[2];
      set_bg_color(r, g, b);
      break;
    }

    case hash("drawPixel"): {  // drawPixel 100 10 1
      int16_t x = (int16_t)action->args[0];
      int16_t y = (int16_t)action->args[1];
      int16_t color = (int16_t)action->args[2];
      draw_pixel(x, y, color);
      break;
    }

    case hash("setRotation"): {  // setRotation 0 // ..3
      int m = (int)action->args[0];
      set_rotation(m);
      break;
    }

    case hash("invertDisplay"): {  // invertDisplay / invertDisplay 0
      bool inv = (bool)action->args[0];
      invert_display(inv);
      break;
    }

    case hash("drawFastVLine"): {  // drawFastVLine 20 20 50 1
      int16_t x = (int16_t)action->args[0];
      int16_t y = (int16_t)action->args[1];
      int16_t h = (int16_t)action->args[2];
      int color = (int)action->args[3];
      draw_fast_vline(x, y, h, color);
      break;
    }

    case hash("drawFastHLine"): {  // drawFastHLine 20 20 50 1
      int16_t x = (int16_t)action->args[0];
      int16_t y = (int16_t)action->args[1];
      int16_t w = (int16_t)action->args[2];
      int color = (int)action->args[3];
      draw_fast_hline(x, y, w, color);
      break;
    }

    case hash("fillScreen"): {  // fillScreen 1
      int color = (int)action->args[0];
      fill_screen(color);
      break;
    }

    case hash("drawLine"): {  // drawLine 20 5 100 45 1
      int16_t x0 = (int16_t)action->args[0];
      int16_t y0 = (int16_t)action->args[1];
      int16_t x1 = (int16_t)action->args[2];
      int16_t y1 = (int16_t)action->args[3];
      int color = (int)action->args[4];
      draw_line(x0, y0, x1, y1, color);
      break;
    }

    case hash("drawRect"): {  // drawRect 20 5 100 50 1
      int16_t x = (int16_t)action->args[0];
      int16_t y = (int16_t)action->args[1];
      int16_t w = (int16_t)action->args[2];
      int16_t h = (int16_t)action->args[3];
      int color = (int)action->args[4];
      draw_rect(x, y, w, h, color);
      break;
    }

    case hash("fillRect"): {  // fillRect 20 10 100 50 1
      int16_t x = (int16_t)action->args[0];
      int16_t y = (int16_t)action->args[1];
      int16_t w = (int16_t)action->args[2];
      int16_t h = (int16_t)action->args[3];
      int color = (int)action->args[4];
      fill_rect(x, y, w, h, color);
      break;
    }

    case hash("drawCircle"): {  // drawCircle 50 30 25 1
      int16_t x = (int16_t)action->args[0];
      int16_t y = (int16_t)action->args[1];
      int16_t r = (int16_t)action->args[2];
      int color = (int)action->args[3];
      draw_circle(x, y, r, color);
      break;
    }

    case hash("fillCircle"): {  // fillCircle 50 30 25 1
      int16_t x = (int16_t)action->args[0];
      int16_t y = (int16_t)action->args[1];
      int16_t r = (int16_t)action->args[2];
      int color = (int)action->args[3];
      fill_circle(x, y, r, color);
      break;
    }

    case hash("drawTriangle"): {  // drawTriangle 10 25 100 5 120 50 1
      int16_t x0 = (int16_t)action->args[0];
      int16_t y0 = (int16_t)action->args[1];
      int16_t x1 = (int16_t)action->args[2];
      int16_t y1 = (int16_t)action->args[3];
      int16_t x2 = (int16_t)action->args[4];
      int16_t y2 = (int16_t)action->args[5];
      int color = (int)action->args[6];
      draw_triangle(x0, y0, x1, y1, x2, y2, color);
      break;
    }

    case hash("fillTriangle"): {  // fillTriangle 12 27 102 7 122 52 1
      int16_t x0 = (int16_t)action->args[0];
      int16_t y0 = (int16_t)action->args[1];
      int16_t x1 = (int16_t)action->args[2];
      int16_t y1 = (int16_t)action->args[3];
      int16_t x2 = (int16_t)action->args[4];
      int16_t y2 = (int16_t)action->args[5];
      int color = (int)action->args[6];
      fill_triangle(x0, y0, x1, y1, x2, y2, color);
      break;
    }

    case hash("drawRoundRect"): {  // drawRoundRect 20 5 100 50 12 1
      int16_t x = (int16_t)action->args[0];
      int16_t y = (int16_t)action->args[1];
      int16_t w = (int16_t)action->args[2];
      int16_t h = (int16_t)action->args[3];
      int16_t r = (int16_t)action->args[4];
      int color = (int)action->args[5];
      draw_round_rect(x, y, w, h, r, color);
      break;
    }

    case hash("fillRoundRect"): {  // fillRoundRect 20 5 100 50 12 1
      int16_t x = (int16_t)action->args[0];
      int16_t y = (int16_t)action->args[1];
      int16_t w = (int16_t)action->args[2];
      int16_t h = (int16_t)action->args[3];
      int16_t r = (int16_t)action->args[4];
      int color = (int)action->args[5];
      fill_round_rect(x, y, w, h, r, color);
      break;
    }

    case hash("drawChar"): {  // drawChar 40 20 65 0 1 3
      int16_t x = (int16_t)action->args[0];
      int16_t y = (int16_t)action->args[1];
      unsigned char c = (unsigned char)action->args[2];
      bool fg = (bool)action->args[3];
      bool bg = (bool)action->args[4];
      int8_t size = (int8_t)action->args[5];
      draw_char(x, y, c, fg, bg, size);
      break;
    }

    case hash("setTextSize"): {  // setTextSize 3  / setTextSize 1 4
      int sx = (int)action->args[0];
      int sy = (int)action->args[1];
      set_text_size(sx, sy);
      break;
    }

    case hash("setCursor"): {  // setCursor 50 5
      int16_t x = (int16_t)action->args[0];
      int16_t y = (int16_t)action->args[1];
      set_cursor(x, y);
      break;
    }

    case hash("setTextColor"): {
      // fillScreen 1  /  setTextColor 0  /  print HELLO
      bool c = (bool)action->args[0];
      set_text_color(c);
      break;
    }

    case hash("setTextWrap"): {  // setTextWrap 0
      bool w = (bool)action->args[0];
      set_text_wrap(w);
      break;
    }

      // Non-transactional commands, should not occur

    case hash("getTextBounds"): {  // getTextBounds 40 20 Hello world
      break;
    }
    case hash("reset"): {
      break;
    }

    case hash("width"): {  // width
      break;
    }

    case hash("height"): {  // height
      break;
    }

    case hash("getRotation"): {  // getRotation
      break;
    }

    case hash("getCursorX"): {  // getCursorX
      break;
    }

    case hash("getCursorY"): {  // getCursorY
      break;
    }

    default:
      break;
  }
}

void Transaction::commit() {
  // if (!next) return;
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

  if (next == sizeof(actions) - 1) {
    commit();
  } else {
    next++;
  }
}
