
#include "esp32s3-display.h"

#include <Adafruit_GFX.h>     // Core graphics library
#include <Adafruit_ST7789.h>  // Hardware-specific library for ST7789
#include <Arduino.h>
#include <Button.h>  // Button by Michael Adams https://github.com/madleech/Button
#include <SPI.h>

#include "logo.c"

// Use dedicated hardware SPI pins
Adafruit_ST7789 tft = Adafruit_ST7789(TFT_CS, TFT_DC, TFT_RST);

void test_lorem();
void test_draw_text(char *text, uint16_t color);
void test_color_palette();
void test_logo();

void display_setup(void) {
  // turn on backlite
  pinMode(TFT_BACKLITE, OUTPUT);
  digitalWrite(TFT_BACKLITE, HIGH);

  // turn on the TFT / I2C power supply
  pinMode(TFT_I2C_POWER, OUTPUT);
  digitalWrite(TFT_I2C_POWER, HIGH);
  delay(10);

  // initialize TFT
  tft.init(135, 240);  // Init ST7789 240x135
  tft.setRotation(3);
  tft.fillScreen(ST77XX_BLACK);

  // large block of text
  // test_color_palette();
  test_logo();
}

void test_lorem() {
  tft.fillScreen(ST77XX_BLACK);
  test_draw_text(
      "*** [4] MOST HAPPY HACKING *** "
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur "
      "adipiscing ante sed nibh tincidunt feugiat. Maecenas enim massa, "
      "fringilla sed malesuada et, malesuada sit amet turpis. Sed porttitor "
      "neque ut ante pretium vitae malesuada nunc bibendum. Nullam aliquet "
      "ultrices massa eu hendrerit. Ut sed nisi lorem. In vestibulum purus a "
      "tortor imperdiet posuere. ",
      ST77XX_WHITE);
}

void test_draw_text(char *text, uint16_t color) {
  tft.setCursor(0, 0);
  tft.setTextColor(color);
  tft.setTextWrap(true);
  tft.print(text);
}

void display_reset() {
  bg_color = ST77XX_BLACK;
  fg_color = ST77XX_WHITE;
  display_clear();
  tft.setCursor(0, 0);
  tft.setTextColor(fg_color);
  tft.setTextWrap(true);
  tft.setTextSize(1, 1);
  tft.setRotation(3);
}

void display_clear() { tft.fillScreen(bg_color); }

void display_print(char *text) { tft.print(text); }

void display_set_cursor(int16_t x, int16_t y) { tft.setCursor(x, y); }

////////////////////////////////////////////////////////////////////////////////
// Buttons

Button button0(0);
Button button1(1);
Button button2(2);

// button 0 has normal polarity
bool button0_down() { return button0.pressed(); }
bool button0_up() { return button0.released(); }
bool button0_pressed() { return button0.read() == Button::PRESSED; }

// button 1 has inverted polarity
bool button1_down() { return button1.released(); }
bool button1_up() { return button1.pressed(); }
bool button1_pressed() { return button1.read() != Button::PRESSED; }

// button 2 has inverted polarity
bool button2_down() { return button2.released(); }
bool button2_up() { return button2.pressed(); }
bool button2_pressed() { return button2.read() != Button::PRESSED; }

// buttons management

void buttons_flush() {
  button0_up();
  button0_down();
  button1_up();
  button1_down();
  button2_up();
  button2_down();
}

void buttons_setup() {
  pinMode(0, INPUT_PULLUP);
  pinMode(1, INPUT_PULLDOWN);
  pinMode(2, INPUT_PULLDOWN);
  buttons_flush();  // flush unsynched inverted initial state
}

static const char *NONE_MESSAGE = "NONE";

const char *wait_buttons(unsigned int during, bool up) {
  unsigned long start = millis();
  unsigned int delta;
  const unsigned long STEP = 10;

  buttons_flush();

  do {
    if (up) {
      if (button0_up()) return "A";
      if (button1_up()) return "B";
      if (button2_up()) return "C";
    } else {
      if (button0_down()) return "A";
      if (button1_down()) return "B";
      if (button2_down()) return "C";
    }
    delay(STEP);
    yield();
    delta = millis() - start;
  } while (delta < during && Serial.available() == 0);
  return NONE_MESSAGE;
}

const char *read_buttons(char *buffer) {
  buffer[0] = 0;
  if (button0_pressed()) strcat(buffer, "A");
  if (button1_pressed()) strcat(buffer, "B");
  if (button2_pressed()) strcat(buffer, "C");
  return strlen(buffer) ? buffer : NONE_MESSAGE;
}

void watch_buttons(unsigned int during, unsigned int interval) {
  unsigned long start = millis();
  unsigned int delta;
  do {
    if (button0_pressed()) Serial.print('A');
    if (button1_pressed()) Serial.print('B');
    if (button2_pressed()) Serial.print('C');

    delay(interval);
    yield();
    delta = millis() - start;
  } while ((!during || delta < during) && Serial.available() == 0);
}

void print_state(const char *prefix, char letter) {
  Serial.print(prefix);
  Serial.print(' ');
  Serial.println(letter);
}

void monitor_buttons(unsigned int during, unsigned int interval) {
  unsigned long start = millis();
  unsigned int delta;
  const unsigned long STEP = 10;
  int every = interval < STEP ? 1 : interval / STEP;
  int counter = 0;
  do {
    if (button0_down()) print_state("DOWN", 'A');
    if (button0_up()) print_state("UP", 'A');
    if (button1_down()) print_state("DOWN", 'B');
    if (button1_up()) print_state("UP", 'B');
    if (button2_down()) print_state("DOWN", 'C');
    if (button2_up()) print_state("UP", 'C');

    if (counter % every == 0) {
      if (button0_pressed()) print_state("PRESSED", 'A');
      if (button1_pressed()) print_state("PRESSED", 'B');
      if (button2_pressed()) print_state("PRESSED", 'C');
    }
    counter++;

    delay(STEP);
    yield();
    delta = millis() - start;
  } while (delta < during && Serial.available() == 0);
}

////////////////////////////////////////////////////////////////////////////////
// color
uint16_t fg_color = ST77XX_WHITE;
uint16_t bg_color = ST77XX_BLACK;

////////////////////////////////////////////////////////////////////////////////
// test

struct Image {
  unsigned int width;
  unsigned int height;
  unsigned int bytes_per_pixel; /* 2:RGB16, 3:RGB, 4:RGBA */
  unsigned char pixel_data[240 * 135 * 2 + 1];
};

// extern Image gimp_image;

void test_logo() {
  const uint16_t *bitmap = (const uint16_t *)(gimp_image.pixel_data);
  tft.drawRGBBitmap(0, 0, bitmap, (int16_t)gimp_image.width,
                    (int16_t)gimp_image.height);
}

void test_color_palette_draw_pixel() {
  // color palette
  uint16_t w = display_get_width();
  uint16_t h = display_get_height();
  const uint16_t size = 15 * 2;
  const bool transactional = false;  // both same speed!
  if (transactional) tft.startWrite();
  for (uint16_t x = 0; x < w; ++x) {
    for (uint16_t y = 0; y < h; ++y) {
      unsigned int r = (x % size) * 256 / size;
      unsigned int g = (y % size) * 256 / size;
      unsigned int b = (((x + y) * 256) / (w + h));
      set_fg_color(r, g, b);
      if (transactional)
        tft.writePixel(x, y, fg_color);
      else
        draw_pixel(x, y, true);
    }
  }
  if (transactional) tft.endWrite();
}

bool test_rgb(uint8_t r, uint8_t g, uint8_t b, uint16_t expected) {
  uint16_t rgb = make_rgb(r, g, b);
  Serial.printf("- %3d / %3d / %3d = %04x =? %04x\n", r, g, b, rgb, expected);
  return rgb == expected;
}

void next_tile(uint16_t *x, uint16_t *y, uint16_t width, uint16_t height,
               uint16_t tile_size) {
  *y += tile_size;
  if (*y + tile_size > height - tile_size) {
    *y = 0;
    *x += tile_size;
    if (*x + tile_size > width) {
      *x = 0;
    }
  }

  set_fg_color(128, 128, 128);
  draw_rect(*x, *y, tile_size, tile_size, true);
}

void display_test(char *buffer) {
  // Toggle un/commenting this line: suceeds/fails to boot
  // Serial.println("Starting tests");  // reason? code alignment/parity?
  // Serial.println("Starting tests");  // reason? code alignment/parity?
  // Serial.println("Starting tests");  // reason? code alignment/parity?

  // Test color conversion
  // ---------------------
  // RGB16 is:
  // MSB rrrr.rggg gggr.rrrr LSB

  Serial.println("\nRGB conversion:");
  bool ok = true;

  ok = ok && test_rgb(255, 255, 255, 0xffff);
  ok = ok && test_rgb(255 - 7, 255 - 3, 255 - 7, 0xffff);
  ok = ok && test_rgb(255 - 8, 255 - 4, 255 - 8, 0xf7de);
  ok = ok && test_rgb(255, 0, 0, 0xf800);
  ok = ok && test_rgb(0, 255, 0, 0x07e0);
  ok = ok && test_rgb(0, 0, 255, 0x001f);

  ok = ok && test_rgb(8, 4, 8, 0x0821);
  ok = ok && test_rgb(8 + 7, 4 + 3, 8 + 7, 0x0821);
  ok = ok && test_rgb(7, 3, 7, 0x0000);
  ok = ok && test_rgb(8, 0, 0, 0x0800);
  ok = ok && test_rgb(0, 4, 0, 0x0020);
  ok = ok && test_rgb(0, 0, 8, 0x0001);

  if (!ok) {
    Serial.println("RGB conversion: TEST FAILED");
    return;
  }
  Serial.println("RGB conversion: success");

  // color palette
  // Serial.println("\nColor palette");
  // test_color_palette_draw_pixel();

  // rotation
  // width / height
  // cursor

  // reset home  clearDisplay

  // setRotation

  // print
  // draw char
  // text bounds
  // text wrap
  // text color
  // text size

  // fillScreen

  const uint16_t size = 45;
  uint16_t width = tft.width();
  uint16_t height = tft.height();
  uint16_t ox = width;
  uint16_t oy = height;

  set_bg_color(0, 0, 0);
  display_clear();

  // drawPixel
  next_tile(&ox, &oy, width, height, size);
  for (uint8_t x = 1; x < size - 1; ++x) {
    for (uint8_t y = 1; y < size - 1; ++y) {
      uint8_t u = (x - 1) * 256 / (size - 2);
      uint8_t v = (y - 1) * 256 / (size - 2);
      set_fg_color(u, v, (u + v) / 2);
      draw_pixel(ox + x, oy + y, true);
    }
  }
  next_tile(&ox, &oy, width, height, size);
  for (uint8_t x = 1; x < size - 1; ++x) {
    for (uint8_t y = 1; y < size - 1; ++y) {
      uint8_t u = (x - 1) * 256 / (size - 2);
      uint8_t v = (y - 1) * 256 / (size - 2);
      set_fg_color(255 - u, 255 - (u + v) / 2, 255 - v);
      draw_pixel(ox + x, oy + y, true);
    }
  }

  // fillCircle
  next_tile(&ox, &oy, width, height, size);
  for (uint16_t r = size / 2 - 1; r > 5; r -= 5) {
    int v = 255 - r * 9;
    set_fg_color(v, v, v);
    Serial.printf("v: %d / fg: %04x\n", v, fg_color);
    fill_circle(ox + size / 2, oy + size / 2, r, true);
  }

  // drawCircle
  next_tile(&ox, &oy, width, height, size);
  uint16_t r = size / 2 - 1;
  set_fg_color(255, 0, 0);
  draw_circle(ox + size / 2, oy + size / 2, r, true);

  set_fg_color(0, 255, 0);
  draw_circle(ox + size / 2, oy + size / 2, r * 2 / 3, true);

  set_fg_color(0, 0, 255);
  draw_circle(ox + size / 2, oy + size / 2, r / 3, true);

  // drawLine
  next_tile(&ox, &oy, width, height, size);
  for (uint16_t i = 0; i < size - 1; i += 4) {
    int v = i * 5;
    set_fg_color(255 - v, v, v);
    draw_line(ox + 1, oy + 1, ox + 1 + i, oy + size - 2, true);
  }

  // drawFastVLine, drawFastHLine
  next_tile(&ox, &oy, width, height, size);
  for (uint16_t i = 0; i < size - 1; i += 5) {
    int v = i * 5;
    set_fg_color(255 - v, v, v);
    draw_fast_vline(ox + 1 + i, oy + 1, i, true);

    set_fg_color(v, v, 255 - v);
    draw_fast_hline(ox + 1, oy + 1 + i, i, true);
  }

  // fillRect, drawRect
  next_tile(&ox, &oy, width, height, size);
  uint16_t d = 2;
  set_fg_color(0, 64, 64);
  for (uint16_t i = 1; i < size; i += d, d *= 2) {
    if (i + d >= size) d = size - i - 1;
    fill_rect(ox + i, oy + i, d, d, true);
    if (i + d == size - 1) break;
  }
  d = 2;
  set_fg_color(255, 0, 0);
  for (uint16_t i = 1; i < size; i += d, d *= 2) {
    if (i + d >= size) d = size - i - 1;
    draw_rect(ox + i, oy + i, d, d, true);
    if (i + d == size - 1) break;
  }

  // drawTriangle, fillTriangle
  next_tile(&ox, &oy, width, height, size);
  for (uint16_t i = 1; i < size; i += size / 5) {
    int16_t x0 = ox + 1;
    int16_t y0 = oy + 1 + i / 2;
    int16_t x1 = ox + 1 + i;
    int16_t y1 = oy + size - 2;
    int16_t x2 = i < size / 2 ? ox + size - 2 : ox + size - 1 - (i * 2 - size);
    int16_t y2 = i < size / 2 ? oy + size - 2 - i * 2 : oy + 1;

    int v = i * 4;
    set_fg_color(255 - v / 2, 255 - 64 - v / 2, 128 + v / 2);
    fill_triangle(x0, y0, x1, y1, x2, y2, true);

    set_fg_color(255, 255, 255);
    draw_triangle(x0, y0, x1, y1, x2, y2, true);
  }

  // drawRoundRect, fillRoundRect
  next_tile(&ox, &oy, width, height, size);
  for (uint16_t r = 1, b = 0, a = 0;  //
       r < size / 2 && a < size / 2;  //
       r += 2, a += 4, b = !b) {
    int v = b ? r * 4 : 255 - r * 8;

    int16_t x = ox + 1 + a;
    int16_t y = oy + 1 + a;
    int16_t w = size - 2 - a * 2;
    int16_t h = size - 2 - a * 2;

    set_fg_color(255 - v / 2, 255 - 64 - v / 2, 128 + v / 2);
    fill_round_rect(x, y, w, h, r, true);

    set_fg_color(255, 255, 255);
    draw_round_rect(x, y, w, h, r, true);
  }

  // invertDisplay
  Serial.println("\nInversion");
  for (int i = 1; i < 10; ++i) {
    delay(50 * i);
    invert_display((i & 1) == 0);
  }

  // Test buttons
  // ------------
  Serial.println("\nButtons");
  while (1) {
    // monitor buttons
    Serial.printf("Monitoring buttons for 30 seconds: ");
    // monitor_buttons(30000, 100);
    Serial.println("");

    // watch buttons
    Serial.printf("Watching buttons for 30 seconds: ");
    watch_buttons(30000, 100);
    Serial.println("");

    // read buttons
    Serial.printf("Reading buttons for some time:");
    for (int i = 0; i < 1000; ++i) {
      const char *res = read_buttons(buffer);
      Serial.printf(" %s", res);
      delay(10);
    }
    Serial.println("");

    // wait buttons
    bool up = true;
    for (int i = 6; i; --i) {
      Serial.printf("(%d to go) Waiting 10 seconds for button %s: ", i,
                    up ? "up" : "down");
      const char *res = wait_buttons(10 * 1000, up);
      Serial.println(res);
      if (!up) wait_buttons(5 * 1000, true);  // if press, wait for release
      up = !up;
    }
  }
}
