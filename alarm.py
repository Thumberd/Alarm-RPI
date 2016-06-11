# Standard library import
import signal
import time
import grovepi
import os
import sqlite3

# Application import
from MySQLhandler import MySQL
from AlarmClass import Alarm
import Utility

SCRIPT_NAME = "alarm"
CYCLE = 50
REFRESH_FREQUENCY = 0.5
IS_REAL_MOTION_BY = 5

# Logger initialisation
logger = Utility.initialize_logger(SCRIPT_NAME)

logger.info("Updating PID")
Utility.update_PID(SCRIPT_NAME, os.getpid())

# Each variables store an object capable of inserting, updating and deleting
# in the given table
try:
    db_events = MySQL('events')
    db_devices = MySQL('devices')
    db_alarms = MySQL('alarms')
    db_users = MySQL('users')
except:
    error_msg = "Unable to connect to the database"
    logger.fatal(error_msg)
    Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)


# Get all the devices that run an alarm
home_device = None
try:
    devices = db_devices.get('type', 2)
    # Choose the PIR sensor that is directly connected to the Raspberry Pi
    for device in devices:
        if device['ip'] == '':
            homeDevice = device[0]
except:
    error_msg = "Can't read devices database"
    logger.fatal(error_msg)
    Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)

if home_device:
    t = 0    # Time the PIR sensor returned one in a cycle
    i = 0    # Number of fetching in a cycle

    while True:
        # If the alarm is set to ON
        if Utility.get_alarm_state(home_device['id']):
            # Read the sensor value
            a = grovepi.digitalRead(int(homeDevice['code']))
            logger.debug("Value returned by sensor: {]".format(a))
            if a == 1:
                t += 1
            if t == IS_REAL_MOTION_BY:
                Alarm(homeDevice['id']).MotionProtocol()
                i = 0
                t = 0
            if i > CYCLE:
                i = 0
                t = 0
            time.sleep(REFRESH_FREQUENCY)
        else:
            time.sleep(60)
