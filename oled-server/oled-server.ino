#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>
#include <Button.h>  // Button by Michael Adams https://github.com/madleech/Button
#include "button.h"

Adafruit_SH1107 display = Adafruit_SH1107(64, 128, &Wire);

// OLED FeatherWing buttons map to different pins depending on board:
#if defined(ESP8266)
  #define BUTTON_A  0
  #define BUTTON_B 16
  #define BUTTON_C  2
#elif defined(ESP32) && !defined(ARDUINO_ADAFRUIT_FEATHER_ESP32S2)
  #define BUTTON_A 15
  #define BUTTON_B 32
  #define BUTTON_C 14
#elif defined(ARDUINO_STM32_FEATHER)
  #define BUTTON_A PA15
  #define BUTTON_B PC7
  #define BUTTON_C PC5
#elif defined(TEENSYDUINO)
  #define BUTTON_A  4
  #define BUTTON_B  3
  #define BUTTON_C  8
#elif defined(ARDUINO_NRF52832_FEATHER)
  #define BUTTON_A 31
  #define BUTTON_B 30
  #define BUTTON_C 27
#else // 32u4, M0, M4, nrf52840, esp32-s2 and 328p
  #define BUTTON_A  9
  #define BUTTON_B  6
  #define BUTTON_C  5
#endif


Button button1(BUTTON_A); // Connect your button between pin 2 and GND
Button button2(BUTTON_B); // Connect your button between pin 3 and GND
Button button3(BUTTON_C); // Connect your button between pin 4 and GND


void setup() {
  //Serial.begin(115200);
  Serial.begin(9600);

  //Serial.println("128x64 OLED FeatherWing test");
  delay(250); // wait for the OLED to power up
  display.begin(0x3C, true); // Address 0x3C default
  Serial.println("# OLED begun");

  // Show image buffer on the display hardware.
  // Since the buffer is intialized with an Adafruit splashscreen
  // internally, this will display the splashscreen.
  display.display();
  delay(500 / 50);

  // Clear the buffer.
  display.clearDisplay();
  display.display();

  display.setRotation(1);
  display.setTextSize(1);
  display.setTextColor(SH110X_WHITE);
  display.setCursor(0,0);
  display.display(); // actually display all of the above

/*
  pinMode(BUTTON_A, INPUT_PULLUP);
  pinMode(BUTTON_B, INPUT_PULLUP);
  pinMode(BUTTON_C, INPUT_PULLUP);
*/
  button1.begin();
  button2.begin();
  button3.begin();

  Serial.println("READY");
}
/*
void unescape(String &s) {
  s.replace("\\n", "\n");
  s.replace("\\t", "\t");
  s.replace("\\\\", "\\");
}
*/
void unescape(char*) {

}

char* split(char* s) {
  char* rest;
  strtok_r(s, " ", &rest);
  return rest;
} 

const char* ERR_EXTRA_ARG = "ERROR extraneous argument";
const char* ERR_MISSING_ARG = "ERROR extraneous argument";
const char* OK = "OK";

void no_arg(char**rest_p, char** error_p) {
  if (*rest_p != NULL)
    *error_p = ERR_EXTRA_ARG;
  else
    *error_p = NULL;
}

int read_int(char**rest_p, char** error_p, bool optional=false, int defval=-1) {
  char* v = *rest_p;
  *rest_p = split(*rest_p);

  if (v == NULL && optional) {
    return defval;
  }

  if (v == NULL)
    *error_p = ERR_MISSING_ARG;
  else if (*rest_p != NULL)
    *error_p = ERR_EXTRA_ARG;
  else
    *error_p = NULL;

  return atoi(v);
}

const char* read_last_str(char**rest_p, char** error_p) {
  char* v = *rest_p;
  if (v == NULL)
    *error_p = ERR_MISSING_ARG;
  else {
    *error_p = NULL;
    *rest_p = NULL;
  }
  return v;
}
// https://stackoverflow.com/a/46711735
constexpr unsigned int hash(const char *s, int off = 0) {
    return !s[off] ? 5381 : (hash(s, off+1)*33) ^ (s[off]|0x20);
}

char response[64];

const char* interpret(char* input) {
  char* cmd = input;
  char* rest = split(input);
  char* error = NULL;
/*
  Serial.print(">>> <");
  Serial.print(cmd);
  Serial.print(",");
  Serial.print(rest);
  Serial.println(">");
*/

  switch (hash(cmd)) {
    case hash("print"): {  // print HELLO\n
      unescape(rest);
      display.print(rest);
      display.display();
      return(OK);
    }
    case hash("clearDisplay"): {
      no_arg(&rest, &error); if (error) return error;
      display.clearDisplay();
      display.display();
      return(OK);
    }
    case hash("home"): {
      no_arg(&rest, &error); if (error) return error;
      display.setCursor(0,0);
      display.display();
      return(OK);
    }
    case hash("reset"): {
      no_arg(&rest, &error); if (error) return error;
      display.clearDisplay();
      display.setCursor(0,0);
      display.display();
      return(OK);
    }
    case hash("drawPixel"): {  // drawPixel 100 10 1
      int x = read_int(&rest, &error);
      int y = read_int(&rest, &error);
      int color = read_int(&rest, &error);
      if (error) return error;
      display.drawPixel(x, y, color);
      display.display();
      return(OK);
    }
    case hash("setRotation"): {  // setRotation 0 // ..3
      int x = read_int(&rest, &error);
      if (error) return error;
      display.setRotation(x);
      display.display();
      return(OK);
    }
#if 0
    case hash("invertDisplay"): {  // invertDisplay
      display.invertDisplay();
      display.display();
      return(OK);
    }
#endif
    case hash("drawFastVLine"): {  // drawFastVLine 20 20 50 1
      int x = read_int(&rest, &error);
      int y = read_int(&rest, &error);
      int h = read_int(&rest, &error);
      int color = read_int(&rest, &error);
      if (error) return error;
      display.drawFastVLine(x, y, h, color);
      display.display();
      return(OK);
    }
    case hash("drawFastHLine"): {  // drawFastHLine 20 20 50 1
      int x = read_int(&rest, &error);
      int y = read_int(&rest, &error);
      int w = read_int(&rest, &error);
      int color = read_int(&rest, &error);
      if (error) return error;
      display.drawFastHLine(x, y, w, color);
      display.display();
      return(OK);
  }
    case hash("fillRect"): {  // fillRect 20 10 100 50 1
      int x = read_int(&rest, &error);
      int y = read_int(&rest, &error);
      int w = read_int(&rest, &error);
      int h = read_int(&rest, &error);
      int color = read_int(&rest, &error);
      if (error) return error;
      display.fillRect(x, y, w, h, color);
      display.display();
      return(OK);
    }
    case hash("fillScreen"): {  // fillScreen 1
      int color = read_int(&rest, &error);
      if (error) return error;
      display.fillScreen(color);
      display.display();
      return(OK);
    }
    case hash("drawLine"): {  // drawLine 20 5 100 45 1
      int x0 = read_int(&rest, &error);
      int y0 = read_int(&rest, &error);
      int x1 = read_int(&rest, &error);
      int y1 = read_int(&rest, &error);
      int color = read_int(&rest, &error);
      if (error) return error;
      display.drawLine(x0, y0, x1, y1, color);
      display.display();
      return(OK);
    }
    case hash("drawRect"): {  // drawRect 20 5 100 50 1
      int x = read_int(&rest, &error);
      int y = read_int(&rest, &error);
      int w = read_int(&rest, &error);
      int h = read_int(&rest, &error);
      int color = read_int(&rest, &error);
      if (error) return error;
      display.drawRect(x, y, w, h, color);
      display.display();
      return(OK);
    }
    case hash("drawCircle"): {  // drawCircle 50 30 25 1
      int x0 = read_int(&rest, &error);
      int y0 = read_int(&rest, &error);
      int r = read_int(&rest, &error);
      int color = read_int(&rest, &error);
      if (error) return error;
      display.drawCircle(x0, y0, r, color);
      display.display();
      return(OK);
    }
    case hash("fillCircle"): {  // fillCircle 50 30 25 1
      int x0 = read_int(&rest, &error);
      int y0 = read_int(&rest, &error);
      int r = read_int(&rest, &error);
      int color = read_int(&rest, &error);
      if (error) return error;
      display.fillCircle(x0, y0, r, color);
      display.display();
      return(OK);
    }
    case hash("drawTriangle"): {  // drawTriangle 10 25 100 5 120 50 1
      int x0 = read_int(&rest, &error);
      int y0 = read_int(&rest, &error);
      int x1 = read_int(&rest, &error);
      int y1 = read_int(&rest, &error);
      int x2 = read_int(&rest, &error);
      int y2 = read_int(&rest, &error);
      int color = read_int(&rest, &error);
      if (error) return error;
      display.drawTriangle(x0, y0, x1, y1, x2, y2, color);
      display.display();
      return(OK);
    }
    case hash("fillTriangle"): {  // fillTriangle 12 27 102 7 122 52 1
      int x0 = read_int(&rest, &error);
      int y0 = read_int(&rest, &error);
      int x1 = read_int(&rest, &error);
      int y1 = read_int(&rest, &error);
      int x2 = read_int(&rest, &error);
      int y2 = read_int(&rest, &error);
      int color = read_int(&rest, &error);
      if (error) return error;
      display.fillTriangle(x0, y0, x1, y1, x2, y2, color);
      display.display();
      return(OK);
    }
    case hash("drawRoundRect"): {  // drawRoundRect 20 5 100 50 12 1
      int x = read_int(&rest, &error);
      int y = read_int(&rest, &error);
      int w = read_int(&rest, &error);
      int h = read_int(&rest, &error);
      int r = read_int(&rest, &error);
      int color = read_int(&rest, &error);
      if (error) return error;
      display.drawRoundRect(x, y, w, h, r, color);
      display.display();
      return(OK);
    }
    case hash("fillRoundRect"): {  // fillRoundRect 20 5 100 50 12 1
      int x = read_int(&rest, &error);
      int y = read_int(&rest, &error);
      int w = read_int(&rest, &error);
      int h = read_int(&rest, &error);
      int r = read_int(&rest, &error);
      int color = read_int(&rest, &error);
      if (error) return error;
      display.fillRoundRect(x, y, w, h, r, color);
      display.display();
      return(OK);
    }
    case hash("drawChar"): {  // drawChar 40 20 65 0 1 3
      int x = read_int(&rest, &error);
      int y = read_int(&rest, &error);
      unsigned char c = read_int(&rest, &error);
      int color = read_int(&rest, &error);
      int bg = read_int(&rest, &error);
      int size = read_int(&rest, &error);
      if (error) return error;
      display.drawChar(x, y, c, color, bg, size);
      display.display();
      return(OK);
    }
    case hash("getTextBounds"): {  // getTextBounds 40 20 Hello world
      int x = read_int(&rest, &error);
      int y = read_int(&rest, &error);
      const char* str = read_last_str(&rest, &error);
      if (error) return error;
      int16_t x1;
      int16_t y1;
      uint16_t w;
      uint16_t h;
      display.getTextBounds(str, x, y, &x1, &y1, &w, &h);
      snprintf(response, sizeof(response)-1, "%d %d %d %d", x1, y1, w, h);
      return response;
    }
    case hash("setTextSize"): {  // setTextSize 3  / setTextSize 1 4
      int s = read_int(&rest, &error);
      int sy = read_int(&rest, &error, true);
      if (error) return error;
      if (sy == -1)
        display.setTextSize(s);
      else
        display.setTextSize(s, sy);
      return(OK);
    }
    case hash("setCursor"): {  // setCursor 50 5
      int x = read_int(&rest, &error);
      int y = read_int(&rest, &error);
      if (error) return error;
      display.setCursor(x, y);
      return(OK);
    }
    case hash("setTextColor"): {  // fillScreen 1  /  setTextColor 1  /  print HELLO
      int c = read_int(&rest, &error);
      if (error) return error;
      display.setTextColor(c);
      return(OK);
    }
    case hash("setTextWrap"): {  // setTextWrap 0
      int w = read_int(&rest, &error);
      if (error) return error;
      display.setTextWrap((bool)w);
      return(OK);
    }
    case hash("width"): {  // width
      return handle_get(&rest, display.width());
    }
    case hash("height"): {  // height
      return handle_get(&rest, display.height());
    }
    case hash("getRotation"): {  // getRotation
      return handle_get(&rest, display.getRotation());
    }
    case hash("getCursorX"): {  // getCursorX
      return handle_get(&rest, display.getCursorX());
    }
    case hash("getCursorY"): {  // getCursorY
      return handle_get(&rest, display.getCursorY());
    }
    case hash("monitorButtons"): {  // monitorButtons 60000 / monitorButtons 60000 1000
      unsigned int during = read_int(&rest, &error);
      unsigned int interval = read_int(&rest, &error, true, 100);
      if (error) return error;

      unsigned long start = millis();
      unsigned int delta;
      const unsigned long STEP = 10;
      int every = interval < STEP ? 1 : interval / STEP;
      int counter = 0;
      do {
        if (button1.pressed()) Serial.println("DOWN A");
        if (button1.released()) Serial.println("UP A");
//        if (button2.pressed()) Serial.println("DOWN B");
//        if (button2.released()) Serial.println("UP B");
//        if (button3.pressed()) Serial.println("DOWN C");
//        if (button3.released()) Serial.println("UP C");

        if (counter % every == 0) {
          if (button1.read() == Button::PRESSED) Serial.println("PRESSED A");
//          if (button2.read() == Button::PRESSED) Serial.println("PRESSED B");
//          if (button3.read() == Button::PRESSED) Serial.println("PRESSED C");
        }
        counter++;

        delay(STEP);
        yield();
        delta = millis() - start;
      } while(delta < during && Serial.available() == 0);
      return(OK);
    }
  /*
    monitorButtons()
    readButtons()
    readButtonsChanges()
    awaitButtonsChanges(timeout)
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
  return "UNKNOWN";
}

const char* handle_get(const char**rest, int val) {
  char* error;
  no_arg(rest, &error); 
  if (error) return error;
  snprintf(response, sizeof(response)-1, "%d", val);
  return response;
}

void loop() {
  if (Serial.available() > 0) {
    String input;  // String sucks, do lower-level
    input.reserve(30);
    input = Serial.readStringUntil('\n');
    const char* result = interpret(input.c_str());
    Serial.println(result);
  }
  else {
    delay(10);
  }

  yield();
  return;

/***

  Serial.print("?");
  String incoming = Serial.readStringUntil('\n');
  Serial.print("> ");
  Serial.println(incoming);  

  return;

  if(!digitalRead(BUTTON_A)) display.print("A");
  if(!digitalRead(BUTTON_B)) display.print("B");
  if(!digitalRead(BUTTON_C)) display.print("C");

  if (button1.pressed())
    display.print("A");
  if (button1.released())
    display.print("a");

  if (button1.read() == Button::PRESSED)
    display.print("_");

  delay(10);
  yield();
  display.display();
***/
}