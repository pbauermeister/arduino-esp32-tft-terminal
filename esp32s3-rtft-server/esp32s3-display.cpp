
#include "esp32s3-display.h"

#include <Adafruit_GFX.h>     // Core graphics library
#include <Adafruit_ST7789.h>  // Hardware-specific library for ST7789
#include <Arduino.h>
#include <Button.h>  // Button by Michael Adams https://github.com/madleech/Button
#include <SPI.h>

// Use dedicated hardware SPI pins
Adafruit_ST7789 tft = Adafruit_ST7789(TFT_CS, TFT_DC, TFT_RST);

void testdrawtext(char *text, uint16_t color);

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
  tft.fillScreen(ST77XX_BLACK);
  testdrawtext(
      "*** [4] MOST HAPPY HACKING *** "
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur "
      "adipiscing ante sed nibh tincidunt feugiat. Maecenas enim massa, "
      "fringilla sed malesuada et, malesuada sit amet turpis. Sed porttitor "
      "neque ut ante pretium vitae malesuada nunc bibendum. Nullam aliquet "
      "ultrices massa eu hendrerit. Ut sed nisi lorem. In vestibulum purus a "
      "tortor imperdiet posuere. ",
      ST77XX_WHITE);
}

void testdrawtext(char *text, uint16_t color) {
  tft.setCursor(0, 0);
  tft.setTextColor(color);
  tft.setTextWrap(true);
  tft.print(text);
}

void display_reset() {
  display_clear();
  tft.setCursor(0, 0);
  tft.setTextColor(fg_color);
  tft.setTextWrap(true);
}

void display_clear() { tft.fillScreen(ST77XX_BLACK); }

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

bool test_rgb(uint8_t r, uint8_t g, uint8_t b, uint16_t expected) {
  uint16_t rgb = make_rgb(r, g, b);
  Serial.printf("- %3d / %3d / %3d = %04x =? %04x\n", r, g, b, rgb, expected);
  return rgb == expected;
}

void display_test(char *buffer) {
  // Toggle un/commenting this line: suceeds/fails to boot
  Serial.println("Starting tests");  // reason? code alignment/parity?
  //Serial.println("Starting tests");  // reason? code alignment/parity?

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
  Serial.println("\nColor palette");
  uint16_t w = display_get_width();
  uint16_t h = display_get_height();
  const uint16_t size = 15 * 2;
  for (uint16_t x = 0; x < w; ++x) {
    for (uint16_t y = 0; y < h; ++y) {
      unsigned int r = (x % size) * 256 / size;
      unsigned int g = (y % size) * 256 / size;
      unsigned int b = (((x + y) * 256) / (w + h));
      set_fg_color(r, g, b);
      draw_pixel(x, y, true);
    }
  }

  // inversion
  Serial.println("\nInversion");
  for (int i = 0; i < 4; ++i) {
    delay(1000);
    invert_display((i & 1) == 0);
  }

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

  // drawPixel
  // drawFastVLine, drawFastHLine
  // fillScreen
  // drawLine
  // drawRect, fillRect
  // drawCircle, fillCircle
  // drawTriangle, fillTriangle
  // drawRoundRect, fillRoundRect

  // invertDisplay

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
