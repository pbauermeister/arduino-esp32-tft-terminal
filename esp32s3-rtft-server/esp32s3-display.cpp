
#include "esp32s3-display.h"

#include <Adafruit_GFX.h>     // Core graphics library
#include <Adafruit_ST7789.h>  // Hardware-specific library for ST7789
#include <Arduino.h>
#include <Button.h>  // Button by Michael Adams https://github.com/madleech/Button
#include <SPI.h>

// Use dedicated hardware SPI pins
Adafruit_ST7789 tft = Adafruit_ST7789(TFT_CS, TFT_DC, TFT_RST);

void testdrawtext(char *text, uint16_t color);

int16_t display_get_width() { return tft.width(); }
int16_t display_get_height() { return tft.height(); }

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
