
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

  /*
    Serial.println(F("Initialized"));

    uint16_t time = millis();
    tft.fillScreen(ST77XX_BLACK);
    time = millis() - time;

    Serial.println(time, DEC);
    delay(500);
  */

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

  /*
    delay(1000);

    // tft print function!
    tftPrintTest();
    delay(4000);

    // a single pixel
    tft.drawPixel(tft.width() / 2, tft.height() / 2, ST77XX_GREEN);
    delay(500);

    // line draw test
    testlines(ST77XX_YELLOW);
    delay(500);

    // optimized lines
    testfastlines(ST77XX_RED, ST77XX_BLUE);
    delay(500);

    testdrawrects(ST77XX_GREEN);
    delay(500);

    testfillrects(ST77XX_YELLOW, ST77XX_MAGENTA);
    delay(500);

    tft.fillScreen(ST77XX_BLACK);
    testfillcircles(10, ST77XX_BLUE);
    testdrawcircles(10, ST77XX_WHITE);
    delay(500);

    testroundrects();
    delay(500);

    testtriangles();
    delay(500);

    mediabuttons();
    delay(500);

    Serial.println("done");
    delay(1000);
    */
}

/*

void testlines(uint16_t color)
{
  tft.fillScreen(ST77XX_BLACK);
  for (int16_t x = 0; x < tft.width(); x += 6)
  {
    tft.drawLine(0, 0, x, tft.height() - 1, color);
    delay(0);
  }
  for (int16_t y = 0; y < tft.height(); y += 6)
  {
    tft.drawLine(0, 0, tft.width() - 1, y, color);
    delay(0);
  }

  tft.fillScreen(ST77XX_BLACK);
  for (int16_t x = 0; x < tft.width(); x += 6)
  {
    tft.drawLine(tft.width() - 1, 0, x, tft.height() - 1, color);
    delay(0);
  }
  for (int16_t y = 0; y < tft.height(); y += 6)
  {
    tft.drawLine(tft.width() - 1, 0, 0, y, color);
    delay(0);
  }

  tft.fillScreen(ST77XX_BLACK);
  for (int16_t x = 0; x < tft.width(); x += 6)
  {
    tft.drawLine(0, tft.height() - 1, x, 0, color);
    delay(0);
  }
  for (int16_t y = 0; y < tft.height(); y += 6)
  {
    tft.drawLine(0, tft.height() - 1, tft.width() - 1, y, color);
    delay(0);
  }

  tft.fillScreen(ST77XX_BLACK);
  for (int16_t x = 0; x < tft.width(); x += 6)
  {
    tft.drawLine(tft.width() - 1, tft.height() - 1, x, 0, color);
    delay(0);
  }
  for (int16_t y = 0; y < tft.height(); y += 6)
  {
    tft.drawLine(tft.width() - 1, tft.height() - 1, 0, y, color);
    delay(0);
  }
}
*/

void testdrawtext(char *text, uint16_t color) {
  tft.setCursor(0, 0);
  tft.setTextColor(color);
  tft.setTextWrap(true);
  tft.print(text);
}

/*
void testfastlines(uint16_t color1, uint16_t color2)
{
  tft.fillScreen(ST77XX_BLACK);
  for (int16_t y = 0; y < tft.height(); y += 5)
  {
    tft.drawFastHLine(0, y, tft.width(), color1);
  }
  for (int16_t x = 0; x < tft.width(); x += 5)
  {
    tft.drawFastVLine(x, 0, tft.height(), color2);
  }
}

void testdrawrects(uint16_t color)
{
  tft.fillScreen(ST77XX_BLACK);
  for (int16_t x = 0; x < tft.width(); x += 6)
  {
    tft.drawRect(tft.width() / 2 - x / 2, tft.height() / 2 - x / 2, x, x,
                 color);
  }
}

void testfillrects(uint16_t color1, uint16_t color2)
{
  tft.fillScreen(ST77XX_BLACK);
  for (int16_t x = tft.width() - 1; x > 6; x -= 6)
  {
    tft.fillRect(tft.width() / 2 - x / 2, tft.height() / 2 - x / 2, x, x,
                 color1);
    tft.drawRect(tft.width() / 2 - x / 2, tft.height() / 2 - x / 2, x, x,
                 color2);
  }
}

void testfillcircles(uint8_t radius, uint16_t color)
{
  for (int16_t x = radius; x < tft.width(); x += radius * 2)
  {
    for (int16_t y = radius; y < tft.height(); y += radius * 2)
    {
      tft.fillCircle(x, y, radius, color);
    }
  }
}

void testdrawcircles(uint8_t radius, uint16_t color)
{
  for (int16_t x = 0; x < tft.width() + radius; x += radius * 2)
  {
    for (int16_t y = 0; y < tft.height() + radius; y += radius * 2)
    {
      tft.drawCircle(x, y, radius, color);
    }
  }
}

void testtriangles()
{
  tft.fillScreen(ST77XX_BLACK);
  uint16_t color = 0xF800;
  int t;
  int w = tft.width() / 2;
  int x = tft.height() - 1;
  int y = 0;
  int z = tft.width();
  for (t = 0; t <= 15; t++)
  {
    tft.drawTriangle(w, y, y, x, z, x, color);
    x -= 4;
    y += 4;
    z -= 4;
    color += 100;
  }
}

void testroundrects()
{
  tft.fillScreen(ST77XX_BLACK);
  uint16_t color = 100;
  int i;
  int t;
  for (t = 0; t <= 4; t += 1)
  {
    int x = 0;
    int y = 0;
    int w = tft.width() - 2;
    int h = tft.height() - 2;
    for (i = 0; i <= 16; i += 1)
    {
      tft.drawRoundRect(x, y, w, h, 5, color);
      x += 2;
      y += 3;
      w -= 4;
      h -= 6;
      color += 1100;
    }
    color += 100;
  }
}

void tftPrintTest()
{
  tft.setTextWrap(false);
  tft.fillScreen(ST77XX_BLACK);
  tft.setCursor(0, 30);
  tft.setTextColor(ST77XX_RED);
  tft.setTextSize(1);
  tft.println("Hello World!");
  tft.setTextColor(ST77XX_YELLOW);
  tft.setTextSize(2);
  tft.println("Hello World!");
  tft.setTextColor(ST77XX_GREEN);
  tft.setTextSize(3);
  tft.println("Hello World!");
  tft.setTextColor(ST77XX_BLUE);
  tft.setTextSize(4);
  tft.print(1234.567);
  delay(1500);
  tft.setCursor(0, 0);
  tft.fillScreen(ST77XX_BLACK);
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(0);
  tft.println("Hello World!");
  tft.setTextSize(1);
  tft.setTextColor(ST77XX_GREEN);
  tft.print(p, 6);
  tft.println(" Want pi?");
  tft.println(" ");
  tft.print(8675309, HEX); // print 8,675,309 out in HEX!
  tft.println(" Print HEX!");
  tft.println(" ");
  tft.setTextColor(ST77XX_WHITE);
  tft.println("Sketch has been");
  tft.println("running for: ");
  tft.setTextColor(ST77XX_MAGENTA);
  tft.print(millis() / 1000);
  tft.setTextColor(ST77XX_WHITE);
  tft.print(" seconds.");
}

void mediabuttons()
{
  // play
  tft.fillScreen(ST77XX_BLACK);
  tft.fillRoundRect(25, 5, 78, 60, 8, ST77XX_WHITE);
  tft.fillTriangle(42, 12, 42, 60, 90, 40, ST77XX_RED);
  delay(500);
  // pause
  tft.fillRoundRect(25, 70, 78, 60, 8, ST77XX_WHITE);
  tft.fillRoundRect(39, 78, 20, 45, 5, ST77XX_GREEN);
  tft.fillRoundRect(69, 78, 20, 45, 5, ST77XX_GREEN);
  delay(500);
  // play color
  tft.fillTriangle(42, 12, 42, 60, 90, 40, ST77XX_BLUE);
  delay(50);
  // pause color
  tft.fillRoundRect(39, 78, 20, 45, 5, ST77XX_RED);
  tft.fillRoundRect(69, 78, 20, 45, 5, ST77XX_RED);
  // play color
  tft.fillTriangle(42, 12, 42, 60, 90, 40, ST77XX_GREEN);
}

*/

uint16_t pen_color = ST77XX_WHITE;

void display_invert(bool inverted) { tft.invertDisplay(inverted); }

void display_reset() {
  display_clear();
  tft.setCursor(0, 0);
  tft.setTextColor(pen_color);
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
  Serial.println("Starting tests");  // reason? code alignment/parity?

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
