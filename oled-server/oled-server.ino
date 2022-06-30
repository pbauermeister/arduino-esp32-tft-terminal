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
  delay(500/10);

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
}

const int MAX_TERMS = 10;

int parse(char* str, const char* terms[]) {
    // FIXME: strtok_r modifies the string, but should not
    char* rest = str;
    char* token = strtok_r(str," ", &rest);
    int nb_terms = 0;

    while (token != NULL && nb_terms < MAX_TERMS) {
      terms[nb_terms] = token;
      nb_terms++;
      token = strtok_r(NULL, " ", &rest);
    }

    /*
    for (int i = 0; i < nb_terms; ++i) {
      Serial.print(i);
      Serial.print(": ");
      Serial.println(terms[i]);
    }
    */

    return nb_terms;
}

// https://stackoverflow.com/a/46711735
constexpr unsigned int hash(const char *s, int off = 0) {                        
    return !s[off] ? 5381 : (hash(s, off+1)*33) ^ s[off];                           
}

void error(const char* terms[], int nb_terms, int required_nb_args) {
  Serial.print("ERROR ");
  Serial.print(terms[0]);
  Serial.print(" takes ");
  Serial.print(required_nb_args);
  Serial.print(" argument(s), but ");
  Serial.print(nb_terms-1);
  Serial.println(" were given");
}

bool check_str(const char* terms[], int nb_terms) {
  if (nb_terms!= 2) {
    error(terms, nb_terms, 1);
    return false;
  }
  return true;
}

void interpret(const char* terms[], int nb_terms) {
  switch (hash(terms[0])) {
  case hash("print"):
    if (check_str(terms, nb_terms)) {
      display.print(terms[1]);
      display.display();
    }
    break;
  default:
    Serial.println("UNKNOWN");
  }
}

const char* terms[MAX_TERMS];

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    int nb_terms = parse((char*)command.c_str(), terms);
    if (nb_terms > 0)
      interpret(terms, nb_terms);
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