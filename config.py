
# To be adapted for your mechanical setup:
ROTATION = 3

# Will be dynamically updated by asking board, meanwile invalid:
WIDTH = None
HEIGHT = None

# Communication setup
SERIALPORT = "/dev/ttyUSB0"  # adapt dep on your OS
BAUDRATE = 57600  # default baudrate of oled-server.ino

# Misc
DEBUG = False

MONITOR_HOST_TIMEOUT = 8
MONITOR_CPU_TIMEOUT  = 60*60
MONITOR_CPU_INTERVAL = 2

REMOTE_SSH_AUTHORITY = None
