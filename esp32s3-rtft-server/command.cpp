#include <Stream.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>

#include "config.h"
#include "esp32s3-display.h"

// constants
const char *ERR_EXTRA_ARG = "ERROR extra arg";
const char *ERR_MISSING_ARG = "ERROR missing arg";
const char *ERR_UNKNOWN_CMD = "ERROR unknown cmd";
const char *OK_MESSAGE = "OK";
const char *NONE_MESSAGE = "NONE";

// variables
bool auto_read_buttons = false;
char buffer[100];

// forward declarations
const char *ok();
const char *make_resp_buffer(char **rest, int val);
void unescape_inplace(char *input);

class ErrorHolder {
 public:
  const char *message;
  ErrorHolder() { message = NULL; }
};

char *split(char *s) {
  char *rest;
  strtok_r(s, " ", &rest);
  return rest;
}

void no_arg(char **rest_p, ErrorHolder &error) {
  if (*rest_p != NULL)
    error.message = ERR_EXTRA_ARG;
  else
    error.message = NULL;
}

int read_int(char **rest_p, ErrorHolder &error, bool optional = false,
             int defval = -1) {
  char *v = *rest_p;
  *rest_p = split(*rest_p);

  if (v == NULL && optional) {
    return defval;
  }

  if (v == NULL)
    error.message = ERR_MISSING_ARG;
  else if (*rest_p != NULL)
    error.message = ERR_EXTRA_ARG;
  else
    error.message = NULL;

  return atoi(v);
}

bool read_bool(char *rest, ErrorHolder &error, bool optional = false,
               bool defval = true) {
  if (!rest) return defval;
  int i = read_int(&rest, error, optional, defval ? 1 : 0);
  if (error.message) return false;
  return i != 0;
}

const char *read_last_str(char **rest_p, ErrorHolder &error) {
  char *v = *rest_p;
  if (v == NULL)
    error.message = ERR_MISSING_ARG;
  else {
    error.message = NULL;
    *rest_p = NULL;
  }
  return v;
}

// https://stackoverflow.com/a/46711735
constexpr unsigned int hash(const char *s, int off = 0) {
  return !s[off] ? 5381 : (hash(s, off + 1) * 33) ^ (s[off] | 0x20);
}

const char *interpret(char *input, const Config &config) {
  unescape_inplace(input);

  char *cmd = input;
  char *rest = split(input);
  // char *error = NULL;
  ErrorHolder error = ErrorHolder();

  switch (hash(cmd)) {
    case hash("autoDisplay"): {  // autoDisplay 1
      bool on = read_int(&rest, error);
      if (error.message) return error.message;
      // auto_display = on;
      return ok();
    }

    case hash("autoReadButtons"): {  // autoReadButtons 1
      bool on = read_int(&rest, error);
      if (error.message) return error.message;
      auto_read_buttons = on;
      return ok();
    }

    case hash("display"): {  // display
      no_arg(&rest, error);
      if (error.message) return error.message;
      return ok();
    }

    case hash("print"): {  // print HELLO\n
      display_print(rest);
      return ok();
    }

    case hash("clearDisplay"): {
      no_arg(&rest, error);
      if (error.message) return error.message;
      display_clear();
      return ok();
    }

    case hash("home"): {
      no_arg(&rest, error);
      if (error.message) return error.message;
      display_set_cursor(0, 0);
      return ok();
    }

    case hash("reset"): {
      no_arg(&rest, error);
      if (error.message) return error.message;
      display_reset();
      return ok();
    }

    case hash("drawPixel"): {  // drawPixel 100 10 1
      int16_t x = read_int(&rest, error);
      int16_t y = read_int(&rest, error);
      int16_t color = read_int(&rest, error);
      if (error.message) return error.message;
      draw_pixel(x, y, color);
      return ok();
    }

    case hash("setRotation"): {  // setRotation 0 // ..3
      int m = read_int(&rest, error);
      if (error.message) return error.message;
      set_rotation(m);
      return ok();
    }

    case hash("invertDisplay"): {  // invertDisplay / invertDisplay 0
      bool inv = read_bool(rest, error, true, true);
      if (error.message) return error.message;
      invert_display(inv);
      return ok();
    }

    case hash("drawFastVLine"): {  // drawFastVLine 20 20 50 1
      int16_t x = read_int(&rest, error);
      int16_t y = read_int(&rest, error);
      int16_t h = read_int(&rest, error);
      int color = read_int(&rest, error);
      if (error.message) return error.message;
      draw_fast_vline(x, y, h, color);
      return ok();
    }

    case hash("drawFastHLine"): {  // drawFastHLine 20 20 50 1
      int16_t x = read_int(&rest, error);
      int16_t y = read_int(&rest, error);
      int16_t w = read_int(&rest, error);
      int color = read_int(&rest, error);
      if (error.message) return error.message;
      draw_fast_hline(x, y, w, color);
      return ok();
    }

    case hash("fillScreen"): {  // fillScreen 1
      int color = read_int(&rest, error);
      if (error.message) return error.message;
      fill_screen(color);
      return ok();
    }

    case hash("drawLine"): {  // drawLine 20 5 100 45 1
      int16_t x0 = read_int(&rest, error);
      int16_t y0 = read_int(&rest, error);
      int16_t x1 = read_int(&rest, error);
      int16_t y1 = read_int(&rest, error);
      int color = read_int(&rest, error);
      if (error.message) return error.message;
      draw_line(x0, y0, x1, y1, color);
      return ok();
    }

    case hash("drawRect"): {  // drawRect 20 5 100 50 1
      int16_t x = read_int(&rest, error);
      int16_t y = read_int(&rest, error);
      int16_t w = read_int(&rest, error);
      int16_t h = read_int(&rest, error);
      int color = read_int(&rest, error);
      if (error.message) return error.message;
      draw_rect(x, y, w, h, color);
      return ok();
    }

    case hash("fillRect"): {  // fillRect 20 10 100 50 1
      int16_t x = read_int(&rest, error);
      int16_t y = read_int(&rest, error);
      int16_t w = read_int(&rest, error);
      int16_t h = read_int(&rest, error);
      int color = read_int(&rest, error);
      if (error.message) return error.message;
      fill_rect(x, y, w, h, color);
      return ok();
    }

    case hash("drawCircle"): {  // drawCircle 50 30 25 1
      int16_t x0 = read_int(&rest, error);
      int16_t y0 = read_int(&rest, error);
      int16_t r = read_int(&rest, error);
      int color = read_int(&rest, error);
      if (error.message) return error.message;
      draw_circle(x0, y0, r, color);
      return ok();
    }

    case hash("fillCircle"): {  // fillCircle 50 30 25 1
      int16_t x0 = read_int(&rest, error);
      int16_t y0 = read_int(&rest, error);
      int16_t r = read_int(&rest, error);
      int color = read_int(&rest, error);
      if (error.message) return error.message;
      fill_circle(x0, y0, r, color);
      return ok();
    }

    case hash("drawTriangle"): {  // drawTriangle 10 25 100 5 120 50 1
      int16_t x0 = read_int(&rest, error);
      int16_t y0 = read_int(&rest, error);
      int16_t x1 = read_int(&rest, error);
      int16_t y1 = read_int(&rest, error);
      int16_t x2 = read_int(&rest, error);
      int16_t y2 = read_int(&rest, error);
      int color = read_int(&rest, error);
      if (error.message) return error.message;
      draw_triangle(x0, y0, x1, y1, x2, y2, color);
      return ok();
    }

    case hash("fillTriangle"): {  // fillTriangle 12 27 102 7 122 52 1
      int16_t x0 = read_int(&rest, error);
      int16_t y0 = read_int(&rest, error);
      int16_t x1 = read_int(&rest, error);
      int16_t y1 = read_int(&rest, error);
      int16_t x2 = read_int(&rest, error);
      int16_t y2 = read_int(&rest, error);
      int color = read_int(&rest, error);
      if (error.message) return error.message;
      fill_triangle(x0, y0, x1, y1, x2, y2, color);
      return ok();
    }

    case hash("drawRoundRect"): {  // drawRoundRect 20 5 100 50 12 1
      int16_t x = read_int(&rest, error);
      int16_t y = read_int(&rest, error);
      int16_t w = read_int(&rest, error);
      int16_t h = read_int(&rest, error);
      int16_t r = read_int(&rest, error);
      int color = read_int(&rest, error);
      if (error.message) return error.message;
      draw_round_rect(x, y, w, h, r, color);
      return ok();
    }

    case hash("fillRoundRect"): {  // fillRoundRect 20 5 100 50 12 1
      int16_t x = read_int(&rest, error);
      int16_t y = read_int(&rest, error);
      int16_t w = read_int(&rest, error);
      int16_t h = read_int(&rest, error);
      int16_t r = read_int(&rest, error);
      int color = read_int(&rest, error);
      if (error.message) return error.message;
      fill_round_rect(x, y, w, h, r, color);
      return ok();
    }

    case hash("drawChar"): {  // drawChar 40 20 65 0 1 3
      int16_t x = read_int(&rest, error);
      int16_t y = read_int(&rest, error);
      unsigned char c = read_int(&rest, error);
      bool fg = read_int(&rest, error);
      bool bg = read_int(&rest, error);
      int8_t size = read_int(&rest, error);
      if (error.message) return error.message;
      draw_char(x, y, c, fg, bg, size);
      return ok();
    }

    case hash("getTextBounds"): {  // getTextBounds 40 20 Hello world
      int16_t x = read_int(&rest, error);
      int16_t y = read_int(&rest, error);
      const char *str = read_last_str(&rest, error);
      if (error.message) return error.message;
      int16_t x1;
      int16_t y1;
      uint16_t w;
      uint16_t h;
      get_text_bounds(str, x, y, &x1, &y1, &w, &h);
      snprintf(buffer, sizeof(buffer) - 1, "%d %d %d %d", x1, y1, w, h);
      return buffer;
    }

    case hash("setTextSize"): {  // setTextSize 3  / setTextSize 1 4
      int s = read_int(&rest, error);
      int sy = read_int(&rest, error, true);
      if (error.message) return error.message;
      set_text_size(s, sy);
      return ok();
    }

    case hash("setCursor"): {  // setCursor 50 5
      int x = read_int(&rest, error);
      int y = read_int(&rest, error);
      if (error.message) return error.message;
      set_cursor(x, y);
      return ok();
    }

    case hash("setTextColor"): {
      // fillScreen 1  /  setTextColor 0  /  print HELLO
      int c = read_int(&rest, error);
      if (error.message) return error.message;
      set_text_color(c);
      return ok();
    }

    case hash("setTextWrap"): {  // setTextWrap 0
      int w = read_int(&rest, error);
      if (error.message) return error.message;
      set_text_wrap((bool)w);
      return ok();
    }

    case hash("width"): {  // width
      return make_resp_buffer(&rest, config.display_width);
    }

    case hash("height"): {  // height
      return make_resp_buffer(&rest, config.display_height);
    }

    case hash("getRotation"): {  // getRotation
      return make_resp_buffer(&rest, get_rotation());
    }

    case hash("getCursorX"): {  // getCursorX
      return make_resp_buffer(&rest, get_cursor_x());
    }

    case hash("getCursorY"): {  // getCursorY
      return make_resp_buffer(&rest, get_cursor_y());
    }

    case hash("monitorButtons"): {
      // monitorButtons 60000 / monitorButtons 60000 500
      unsigned int during = read_int(&rest, error);
      unsigned int interval = read_int(&rest, error, true, 100);
      if (error.message) return error.message;

      monitor_buttons(during, interval);
      return ok();
    }

    case hash("watchButtons"): {
      // watchButtons / watchButtons 60000 / watchButtons 60000 500
      unsigned int during = read_int(&rest, error, true, 0);
      unsigned int interval = read_int(&rest, error, true, 100);
      if (error.message) return error.message;

      watch_buttons(during, interval);
      return "";
    }

    case hash("readButtons"): {  // readButtons
      return read_buttons(buffer);
    }

    case hash("waitButton"): {  //  waitButton 60000 1
      unsigned int during = read_int(&rest, error);
      unsigned int up = read_int(&rest, error);
      if (error.message) return error.message;

      return wait_buttons(during, up);
    }

    case hash("test"): {  //  test
      display_test(buffer);
    }

      /*
        sleep(timeout)

        case hash("drawBitmap"): {  //
        case hash("drawXBitmap"): {  //
        case hash("drawGrayscaleBitmap"): {  //
        case hash("drawRGBBitmap"): {  //
        case hash("setFont"): {  //
      */

    default:
      break;
  }
  return ERR_UNKNOWN_CMD;
}

const char *ok() {
  strcpy(buffer, OK_MESSAGE);
  if (auto_read_buttons) {
    strcat(buffer, " ");
    bool any = false;

    if (button0_pressed()) {
      strcat(buffer, "A");
      any = true;
    }
    if (button1_pressed()) {
      strcat(buffer, "B");
      any = true;
    }
    if (button2_pressed()) {
      strcat(buffer, "C");
      any = true;
    }
    if (!any) strcat(buffer, NONE_MESSAGE);
  }
  return buffer;
}

const char *make_resp_buffer(char **rest, int val) {
  ErrorHolder error = ErrorHolder();
  no_arg(rest, error);
  if (error.message) return error.message;
  snprintf(buffer, sizeof(buffer) - 1, "%d", val);
  return buffer;
}

void unescape_inplace(char *input) {
  for (char *from = input, *to = input;;) {
    if (*from != '\\') {
      *to = *from;
    } else {
      ++from;
      switch (*from) {
        case 'n':
          *to = '\n';
          break;
        case '\\':
          *to = '\\';
          break;
        case 't':
          *to = '\t';
          break;
        default:
          *to = *from;
      }
    }
    if (*from == 0) break;
    ++from;
    ++to;
  }
}
