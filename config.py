# Boolean options should be designed to be False by default.

# To be adapted for your mechanical setup:
SCREEN_ROTATION = 3

TEXT_SCALING = 2
GFX_SCALING = 1

# Will be dynamically updated by asking board, meanwile invalid:
WIDTH: int = 0
HEIGHT: int = 0

COLUMNS: int = 0
ROWS: int = 0

# Communication setup
SERIAL_PORT_BASE = "/dev/ttyACM"  # adapt dep on your OS
SERIAL_BAUDRATE = 115200  # default baudrate of oled-server.ino
SERIAL_ERROR_RETRY_DELAY = .1
SERIAL_ERROR_RETRY_DELAY_2 = 1
SERIAL_TIMEOUT = 5.0
# Misc
DEBUG = False

MONITOR_CPU_INTERVAL = 2
MONITOR_SSH_AUTHORITY = ''

APPS_TIMEOUT = 60 * 3
APPS_ONCE_TIMEOUT = 10

APP_ASTERIODS_AUTOPLAY = False
APP_ASTERIODS_AUTOPLAY_TIMEOUT = 0  # 0 means until L=0
APP_ASTERIODS_SHOOT_EVERY = 4
