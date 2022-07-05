#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>
#include <Button.h>  // Button by Michael Adams https://github.com/madleech/Button

Adafruit_SH1107 display = Adafruit_SH1107(64, 128, &Wire);

// OLED FeatherWing buttons map to different pins depending on board:
#if defined(ESP8266)
  #define BUTTON_A  0
  #define BUTTON_B 16
  #define BUTTON_C  2
#elif defined(ESP32) && !defined(ARDUINO_ADAFRUIT_FEATHER_ESP32S2)
  #define BOARD_NAME "ARDUINO_ADAFRUIT_FEATHER_ESP32S2"
  #define BUTTON_A 15
  #define BUTTON_B 32
  #define BUTTON_C 14
#elif defined(ARDUINO_STM32_FEATHER)
  #define BOARD_NAME "ARDUINO_STM32_FEATHER"
  #define BUTTON_A PA15
  #define BUTTON_B PC7
  #define BUTTON_C PC5
#elif defined(TEENSYDUINO)
  #define BOARD_NAME "TEENSYDUINO"
  #define BUTTON_A  4
  #define BUTTON_B  3
  #define BUTTON_C  8
#elif defined(ARDUINO_NRF52832_FEATHER)
  #define BOARD_NAME "ARDUINO_NRF52832_FEATHER"
  #define BUTTON_A 31
  #define BUTTON_B 30
  #define BUTTON_C 27
#else // 32u4, M0, M4, nrf52840, esp32-s2 and 328p
  #define BOARD_NAME "Any"
  #define BUTTON_A  9
  #define BUTTON_B  6
  #define BUTTON_C  5
#endif

const char* ERR_EXTRA_ARG = "ERROR extra arg";
const char* ERR_MISSING_ARG = "ERROR missing arg";
const char* ERR_UNKNOWN_CMD = "ERROR unknown cmd";
const char* OK = "OK";
const char* NONE = "NONE";

char buffer[100];  // used for input and output, so use with care!
Button button1(BUTTON_A);
Button button2(BUTTON_B);
Button button3(BUTTON_C);
bool auto_display = true;
bool auto_read_buttons = false;

void setup() {
  //Serial.begin(115200);
  Serial.begin(57600);

  Serial.print("# Board: ");
  Serial.println(BOARD_NAME);

  delay(250); // wait for the OLED to power up
  display.begin(0x3C, true); // Address 0x3C default
  Serial.print("# OLED begun: ");
  Serial.print(display.width());
  Serial.print("x");
  Serial.println(display.height());

  // Show image buffer on the display hardware.
  // Since the buffer is intialized with an Adafruit splashscreen
  // internally, this will display the splashscreen.
  display.display();
  delay(500 / 50);

  // Clear the buffer.
  display.clearDisplay();
  display.display();

  display.setRotation(1);  // horizontal, buttons left
  display.setTextSize(1);
  display.setTextColor(SH110X_WHITE);
  display.setCursor(0,0);
  display.display(); // actually display all of the above

  button1.begin();
  button2.begin();
  button3.begin();

  Serial.println("READY");
}

char* split(char* s) {
  char* rest;
  strtok_r(s, " ", &rest);
  return rest;
}

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

const char* interpret(char* input) {
  char* cmd = input;
  char* rest = split(input);
  char* error = NULL;

  switch (hash(cmd)) {
    case hash("autoDisplay"): {  // autoDisplay 1
      bool on = read_int(&rest, &error);
      if (error) return error;
      auto_display = on;
      return ok();
    }
    case hash("autoReadButtons"): {  // autoReadButtons 1
      bool on = read_int(&rest, &error);
      if (error) return error;
      auto_read_buttons = on;
      return ok();
    }
    case hash("display"): {  // autoDisplay 1
      no_arg(&rest, &error); if (error) return error;
      display.display();
      return ok();
    }
    case hash("print"): {  // print HELLO\n
      display.print(rest);
      if (auto_display) display.display();
      return ok();
    }
    case hash("clearDisplay"): {
      no_arg(&rest, &error); if (error) return error;
      display.clearDisplay();
      if (auto_display) display.display();
      return ok();
    }
    case hash("home"): {
      no_arg(&rest, &error); if (error) return error;
      display.setCursor(0,0);
      if (auto_display) display.display();
      return ok();
    }
    case hash("reset"): {
      no_arg(&rest, &error); if (error) return error;
      display.clearDisplay();
      display.setCursor(0,0);
      if (auto_display) display.display();
      return ok();
    }
    case hash("drawPixel"): {  // drawPixel 100 10 1
      int x = read_int(&rest, &error);
      int y = read_int(&rest, &error);
      int color = read_int(&rest, &error);
      if (error) return error;
      display.drawPixel(x, y, color);
      if (auto_display) display.display();
      return ok();
    }
    case hash("setRotation"): {  // setRotation 0 // ..3
      int x = read_int(&rest, &error);
      if (error) return error;
      display.setRotation(x);
      if (auto_display) display.display();
      return ok();
    }
#if 0
    case hash("invertDisplay"): {  // invertDisplay
      display.invertDisplay();
      if (auto_display) display.display();
      return ok();
    }
#endif
    case hash("drawFastVLine"): {  // drawFastVLine 20 20 50 1
      int x = read_int(&rest, &error);
      int y = read_int(&rest, &error);
      int h = read_int(&rest, &error);
      int color = read_int(&rest, &error);
      if (error) return error;
      display.drawFastVLine(x, y, h, color);
      if (auto_display) display.display();
      return ok();
    }
    case hash("drawFastHLine"): {  // drawFastHLine 20 20 50 1
      int x = read_int(&rest, &error);
      int y = read_int(&rest, &error);
      int w = read_int(&rest, &error);
      int color = read_int(&rest, &error);
      if (error) return error;
      display.drawFastHLine(x, y, w, color);
      if (auto_display) display.display();
      return ok();
  }
    case hash("fillRect"): {  // fillRect 20 10 100 50 1
      int x = read_int(&rest, &error);
      int y = read_int(&rest, &error);
      int w = read_int(&rest, &error);
      int h = read_int(&rest, &error);
      int color = read_int(&rest, &error);
      if (error) return error;
      display.fillRect(x, y, w, h, color);
      if (auto_display) display.display();
      return ok();
    }
    case hash("fillScreen"): {  // fillScreen 1
      int color = read_int(&rest, &error);
      if (error) return error;
      display.fillScreen(color);
      if (auto_display) display.display();
      return ok();
    }
    case hash("drawLine"): {  // drawLine 20 5 100 45 1
      int x0 = read_int(&rest, &error);
      int y0 = read_int(&rest, &error);
      int x1 = read_int(&rest, &error);
      int y1 = read_int(&rest, &error);
      int color = read_int(&rest, &error);
      if (error) return error;
      display.drawLine(x0, y0, x1, y1, color);
      if (auto_display) display.display();
      return ok();
    }
    case hash("drawRect"): {  // drawRect 20 5 100 50 1
      int x = read_int(&rest, &error);
      int y = read_int(&rest, &error);
      int w = read_int(&rest, &error);
      int h = read_int(&rest, &error);
      int color = read_int(&rest, &error);
      if (error) return error;
      display.drawRect(x, y, w, h, color);
      if (auto_display) display.display();
      return ok();
    }
    case hash("drawCircle"): {  // drawCircle 50 30 25 1
      int x0 = read_int(&rest, &error);
      int y0 = read_int(&rest, &error);
      int r = read_int(&rest, &error);
      int color = read_int(&rest, &error);
      if (error) return error;
      display.drawCircle(x0, y0, r, color);
      if (auto_display) display.display();
      return ok();
    }
    case hash("fillCircle"): {  // fillCircle 50 30 25 1
      int x0 = read_int(&rest, &error);
      int y0 = read_int(&rest, &error);
      int r = read_int(&rest, &error);
      int color = read_int(&rest, &error);
      if (error) return error;
      display.fillCircle(x0, y0, r, color);
      if (auto_display) display.display();
      return ok();
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
      if (auto_display) display.display();
      return ok();
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
      if (auto_display) display.display();
      return ok();
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
      if (auto_display) display.display();
      return ok();
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
      if (auto_display) display.display();
      return ok();
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
      if (auto_display) display.display();
      return ok();
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
      snprintf(buffer, sizeof(buffer)-1, "%d %d %d %d", x1, y1, w, h);
      return buffer;
    }
    case hash("setTextSize"): {  // setTextSize 3  / setTextSize 1 4
      int s = read_int(&rest, &error);
      int sy = read_int(&rest, &error, true);
      if (error) return error;
      if (sy == -1)
        display.setTextSize(s);
      else
        display.setTextSize(s, sy);
      return ok();
    }
    case hash("setCursor"): {  // setCursor 50 5
      int x = read_int(&rest, &error);
      int y = read_int(&rest, &error);
      if (error) return error;
      display.setCursor(x, y);
      return ok();
    }
    case hash("setTextColor"): {  // fillScreen 1  /  setTextColor 1  /  print HELLO
      int c = read_int(&rest, &error);
      if (error) return error;
      display.setTextColor(c);
      return ok();
    }
    case hash("setTextWrap"): {  // setTextWrap 0
      int w = read_int(&rest, &error);
      if (error) return error;
      display.setTextWrap((bool)w);
      return ok();
    }
    case hash("width"): {  // width
      return make_resp_buffer(&rest, display.width());
    }
    case hash("height"): {  // height
      return make_resp_buffer(&rest, display.height());
    }
    case hash("getRotation"): {  // getRotation
      return make_resp_buffer(&rest, display.getRotation());
    }
    case hash("getCursorX"): {  // getCursorX
      return make_resp_buffer(&rest, display.getCursorX());
    }
    case hash("getCursorY"): {  // getCursorY
      return make_resp_buffer(&rest, display.getCursorY());
    }
/*
    case hash("monitorButtons"): {  // monitorButtons 60000 / monitorButtons 60000 500
      unsigned int during = read_int(&rest, &error);
      unsigned int interval = read_int(&rest, &error, true, 100);
      if (error) return error;

      unsigned long start = millis();
      unsigned int delta;
      const unsigned long STEP = 10;
      int every = interval < STEP ? 1 : interval / STEP;
      int counter = 0;
      do {
        if (button1.pressed())  print_state("DOWN", 'A');
        if (button1.released()) print_state("UP",   'A');
        if (button2.pressed())  print_state("DOWN", 'B');
        if (button2.released()) print_state("UP",   'B');
        if (button3.pressed())  print_state("DOWN", 'C');
        if (button3.released()) print_state("UP",   'C');

        if (counter % every == 0) {
          if (button1.read() == Button::PRESSED) print_state("PRESSED", 'A');
          if (button2.read() == Button::PRESSED) print_state("PRESSED", 'B');
          if (button3.read() == Button::PRESSED) print_state("PRESSED", 'C');
        }
        counter++;

        delay(STEP);
        yield();
        delta = millis() - start;
      } while(delta < during && Serial.available() == 0);
      return ok();
    }
    case hash("watchButtons"): {  // watchButtons / watchButtons 60000 / watchButtons 60000 500
      unsigned int during = read_int(&rest, &error, true, 0);
      unsigned int interval = read_int(&rest, &error, true, 100);
      if (error) return error;

      unsigned long start = millis();
      unsigned int delta;
      do {
        if (button1.read() == Button::PRESSED) Serial.print('A');
        if (button2.read() == Button::PRESSED) Serial.print('B');
        if (button3.read() == Button::PRESSED) Serial.print('C');

        delay(interval);
        yield();
        delta = millis() - start;
      } while((!during || delta < during) && Serial.available() == 0);
      return "";
    }
*/
    case hash("readButtons"): {  // readButtons
      buffer[0] = 0;
      if (button1.read() == Button::PRESSED) strcat(buffer, "A");
      if (button2.read() == Button::PRESSED) strcat(buffer, "B");
      if (button3.read() == Button::PRESSED) strcat(buffer, "C");
      return strlen(buffer) ? buffer : NONE;
    }
    case hash("waitButton"): { //  waitButton 60000 1
      unsigned int during = read_int(&rest, &error);
      unsigned int up = read_int(&rest, &error);
      if (error) return error;

      unsigned long start = millis();
      unsigned int delta;
      const unsigned long STEP = 10;

      // flush
      button1.released(); button1.pressed();
      button2.released(); button2.pressed();
      button3.released(); button3.pressed();

      do {
        if (up) {
          if (button1.released()) return "A";
          if (button2.released()) return "B";
          if (button3.released()) return "C";
        }
        else {
          if (button1.pressed()) return "A";
          if (button2.pressed()) return "B";
          if (button3.pressed()) return "C";
        }
        delay(STEP);
        yield();
        delta = millis() - start;
      } while(delta < during && Serial.available() == 0);
      return(NONE);
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

const char* ok() {
  strcpy(buffer, OK);
  if (auto_read_buttons) {
    strcat(buffer, " ");
    bool any = false;

    if (button1.read() == Button::PRESSED) {
      strcat(buffer, "A");
      any = true;
    }
    if (button2.read() == Button::PRESSED) {
      strcat(buffer, "B");
      any = true;
    }
    if (button3.read() == Button::PRESSED) {
      strcat(buffer, "C");
      any = true;
    }
    if (!any)
      strcat(buffer, NONE);
  }
  return buffer;
}

/*
void print_state(const char* prefix, char letter) {
  Serial.print(prefix);
  Serial.print(' ');
  Serial.println(letter);
}
*/

const char* make_resp_buffer(const char**rest, int val) {
  char* error;
  no_arg(rest, &error);
  if (error) return error;
  snprintf(buffer, sizeof(buffer)-1, "%d", val);
  return buffer;
}

void unescape_inplace(char* input) {
  for (char *from = input, *to = input;;) {
    if (*from != '\\') {
      *to = *from;
    } else {
      ++from;
      switch(*from) {
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

char* get_input(char* input, size_t len) {
  len = Serial.readBytesUntil('\n', input, len - 1);
  input[len] = 0;
  return input;
}

void loop() {
  if (Serial.available() > 0) {
    //static char input[30];
    get_input(buffer, sizeof(buffer));
    unescape_inplace(buffer);

    const char* result = interpret(buffer);
    if (result) Serial.println(result);
  }
  else {
    delay(10);
  }

  yield();
}