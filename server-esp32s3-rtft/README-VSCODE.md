# Project setup under VSCode

## Arduino C++ formatting

1. Preferences -> Settings
2. Search for C_Cpp.clang_format_fallbackStyle
3. Change from "Visual Studio" to "{ BasedOnStyle: Google, IndentWidth: 4 }"

## Arduino Plugin

- Install plugin Arduino from Microsoft

## Add board support

- In plugin Arduino from Microsoft, visit its Extension Settings:

  - In Arduino: Additional Urls click Add Item and paste

    https://adafruit.github.io/arduino-board-index/package_adafruit_index.json

  - In Arduino: Additional Urls click Add Item and paste

	  https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json

## Select board

- F1: Arduino: Board Manager
	- Type: ESP32
	- Locate esp32 by Espressif Systems, click install

- F1: Arduino: Change board type
    - Paste: Adafruit Feather ESP32-S3 Reverse TFT

- F1 Arduino: Library Manager:
  - Locate and add:
    - Adafruit ST7789
    - Button by Michael Adams
    - Adafruit neopixel
    - Adafruit testbed

## Compile / upload

- Visit your *.ino file
- Click icon "Arduino: Verify" associated with file
- Click icon "Arduino: Upload" associated with file
    - The Output console shall indicate "[Starting] Uploading sketch"
      then "[Done] Uploading sketch"
- Press the Reset button on the board
