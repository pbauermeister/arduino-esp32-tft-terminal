# Boolean options should be designed to be False by default.

# To be adapted for your mechanical setup:
SCREEN_ROTATION = 3

# Will be dynamically updated by asking board, meanwile invalid:
WIDTH = None
HEIGHT = None

COLUMNS = None
ROWS = None

# Communication setup
SERIAL_PORT = "/dev/ttyUSB0"  # adapt dep on your OS
SERIAL_BAUDRATE = 57600  # default baudrate of oled-server.ino
SERIAL_ERROR_RETRY_DELAY = 15

# Misc
DEBUG = False

MONITOR_SKIP = False
MONITOR_HOST_TIMEOUT = 8
MONITOR_CPU_TIMEOUT  = 60*60
MONITOR_CPU_INTERVAL = 2
MONITOR_ONLY = False  # if False, will show demos after monitors
MONITOR_SSH_AUTHORITY = ''

APPS_TIMEOUT = 60

APP_ASTERIODS_AUTOPLAY = False
APP_ASTERIODS_AUTOPLAY_TIMEOUT = 0
APP_ASTERIODS_SKIP = False
