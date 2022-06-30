/*

TODO:
- command to inquire buttons states
- indication of reboot (may be unrequested)
- command to wait for a button change
*/


#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>
#include <Button.h>  // Button by Michael Adams https://github.com/madleech/Button
#include <ArduinoJson.h>  // https://github.com/bblanchon/ArduinoJson

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

  Serial.println("128x64 OLED FeatherWing ************");
  delay(250); // wait for the OLED to power up
  display.begin(0x3C, true); // Address 0x3C default
  Serial.println("OLED begun");

  // Show image buffer on the display hardware.
  // Since the buffer is intialized with an Adafruit splashscreen
  // internally, this will display the splashscreen.
  display.display();
  delay(500);

  // Clear the buffer.
  display.clearDisplay();
  display.display();

  display.setRotation(1);
  Serial.println("Ready");

/*
  pinMode(BUTTON_A, INPUT_PULLUP);
  pinMode(BUTTON_B, INPUT_PULLUP);
  pinMode(BUTTON_C, INPUT_PULLUP);
*/
  button1.begin();
  button2.begin();
  button3.begin();
 
  display.setTextSize(1);
  display.setTextColor(SH110X_WHITE);
  display.setCursor(0,0);
  display.println("              ");
  display.setCursor(0,0);
  display.display(); // actually display all of the above
}

// https://stackoverflow.com/a/46711735
constexpr unsigned int hash(const char *s, int off = 0) {                        
    return !s[off] ? 5381 : (hash(s, off+1)*33) ^ s[off];                           
}

bool parse_void(JsonDocument &doc) {
  if (doc.size() != 1) return false;
  return true;
}

bool parse_str(JsonDocument &doc, const char* *str) {
  if (doc.size() != 2
      || !doc[1].is<const char*>()) return false;
  *str = doc[1].as<const char*>();
  return true;
}

bool parse_int(JsonDocument &doc, int* a) {
  if (doc.size() != 2
      || !doc[1].is<int>()
      ) return false;
  *a = doc[1].as<int>();
  return true;
}

bool parse_int_int_int(JsonDocument &doc, int* a, int* b, int* c) {
  if (doc.size() != 4
      || !doc[1].is<int>()
      || !doc[2].is<int>()
      || !doc[3].is<int>()
      ) return false;
  *a = doc[1].as<int>();
  *b = doc[2].as<int>();
  *c = doc[3].as<int>();
  return true;
}

bool interpret(JsonDocument &doc) {
  switch (hash(doc[0].as<const char*>())) {
  case hash("print"):  // ["print","HELLO\n"]
    const char* text;
    if (!parse_str(doc, &text)) return false;
    display.print(text);
    break;
  case hash("clearDisplay"):  // ["clearDisplay"] <== crashes
    if (!parse_void(doc)) return false;
    display.clearDisplay();
    break;
  case hash("drawPixel"):  // ["drawPixel", 10, 10, 1]
    int x, y, color;
    if (!parse_int_int_int(doc, &x, &y, &color)) return false;
    display.drawPixel(x, y, color);
    break;
  case hash("setRotation"):  // ["setRotation", 2]
    int r;
    if (!parse_int(doc, &r)) return false;
    display.setRotation(r);
    break;
  default:
    return false;
  }
  display.display();
  return true;
}

//DynamicJsonDocument doc(200);

void loop() {
  if (Serial.available() > 0) {
    StaticJsonDocument<256> doc;
    deserializeJson(doc, Serial);
    if (doc.size() > 0) {
      bool ok = false;
      if (doc[0].is<const char*>()) {
        ok = interpret(doc);
      }
      if (ok) {
        Serial.println("OK");
      }
      else {
        Serial.println("ERROR");
      }
    }
  }
  else {
    delay(10);
  }
  yield();
  return;

/*****

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
  *****/
}