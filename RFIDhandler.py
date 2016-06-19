# Standard library imports
import serial
import grovepi
import time
import sys
import zerorpc

# Application library imports
from MySQLhandler import *
import Utility

SCRIPT_NAME = "RFIDhandler"
TIME_BEFORE_ACTIVATION = 120

# Logger initialisation
logger = Utility.initialize_logger(SCRIPT_NAME)

logger.info("Initialize serial connection with Arduino")
try:
    s = serial.Serial('/dev/ttyACM0', 9600)
except:
    error_msg = "Unable to connect to the Arduino"
    logger.critical(error_msg)
    Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)
    time.sleep(50000)  # Wait a moment for a possible fix
    sys.exit()  # Close the process and hope for a restart (-> supervisor)

# Each variables store an object capable of inserting, updating and deleting
# in the given table
try:
    db_devices = MySQL('devices')
    db_alarms = MySQL('alarms')
    db_users = MySQL('users')
except:
    error_msg = "Unable to connect to the database"
    logger.fatal(error_msg)
    Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)
    time.sleep(50000)
    sys.exit()

timeshot = 0

while True:
    line = s.readline()  # Get the line sent by the Arduino
    logger.debug(line.split('\r'))
    user = db_users.get('RFID', line.split('\r')[0])
    # [user] represents the owner's row of the RFID tag passed
    # if it exists
    if user:
        Utility.switch_led_info(0)
        Utility.sound(0)
        c = zerorpc.Client()
        c.connect("tcp://127.0.0.1:4242")
        c.RFID()
        alarms = db_alarms.all()
        state = bool(alarms[0]['state'])
        if not state:
            logger.debug("Waiting {} sec before activation".format(TIME_BEFORE_ACTIVATION))
            time.sleep(TIME_BEFORE_ACTIVATION)
        for alarm in alarms:
            db_alarms.modify(alarm['id'], 'state', not state)
    else:
        logger.warning("Unauthorized tag")
        c = zerorpc.Client()
        c.connect("tcp://127.0.0.1:4242")
        c.RFIDError()
