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

  Serial.println("128x64 OLED FeatherWing test");
  delay(250); // wait for the OLED to power up
  display.begin(0x3C, true); // Address 0x3C default
  Serial.println("OLED begun");

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
  Serial.println("Ready.");
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

// https://stackoverflow.com/a/46711735
constexpr unsigned int hash(const char *s, int off = 0) {
    return !s[off] ? 5381 : (hash(s, off+1)*33) ^ (s[off]|0x20);
}

const char* OK = "OK";

const char* interpret(char* input) {
  char* cmd = input;
  char* rest = split(input);

  Serial.print(">>> <");
  Serial.print(cmd);
  Serial.print(",");
  Serial.print(rest);
  Serial.println(">");

  switch (hash(cmd)) {
    case hash("print"): {  // print HELLO\n
      unescape(rest);
      display.print(rest);
      display.display();
      return(OK);
    }
    case hash("clearDisplay"): {
      display.clearDisplay();
      display.display();
      return(OK);
    }
    case hash("home"): {
      display.setCursor(0,0);
      display.display();
      return(OK);
    }
    case hash("reset"): {
      display.clearDisplay();
      display.setCursor(0,0);
      display.display();
      return(OK);
    }
    case hash("drawPixel"): {  // drawPixel 100 10 1
      char* x = rest; rest = split(rest);
      char* y = rest; rest = split(rest);
      char* color = rest;
      display.drawPixel(atoi(x), atoi(y), atoi(color));
      display.display();
      return(OK);
    }
    case hash("setRotation"): {  // setRotation 0 // ..3
      char* x = rest;
      display.setRotation(atoi(x));
      display.display();
      return(OK);
    }
/*
    case hash("invertDisplay"):  // setRotation
    case hash("drawFastVLine"):  // setRotation
    case hash("drawFastHLine"):  // setRotation
    case hash("fillRect"):  // setRotation
    case hash("fillScreen"):  // setRotation
    case hash("drawLine"):  // setRotation
    case hash("drawRect"):  // setRotation
    case hash("drawCircle"):  // setRotation
    case hash("fillCircle"):  // setRotation
    case hash("drawTriangle"):  // setRotation
    case hash("fillTriangle"):  // setRotation
    case hash("drawRoundRect"):  // setRotation
    case hash("fillRoundRect"):  // setRotation
    case hash("drawBitmap"):  // setRotation
    case hash("drawXBitmap"):  // setRotation
    case hash("drawGrayscaleBitmap"):  // setRotation
    case hash("drawRGBBitmap"):  // setRotation
    case hash("drawChar"):  // setRotation
    case hash("getTextBounds"):  // setRotation
    case hash("setTextSize"):  // setRotation
    case hash("setFont"):  // setRotation
    case hash("setCursor"):  // setRotation
    case hash("setTextColor"):  // setRotation
    case hash("setTextWrap"):  // setRotation
    case hash("width"):  // setRotation
    case hash("height"):  // setRotation
    case hash("getRotation"):  // setRotation
    case hash("getCursorX"):  // setRotation
    case hash("getCursorY"):  // setRotation
    */
    default:
      break;
  }
  return "UNKNOWN";
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
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