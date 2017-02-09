# Standard library imports
import serial
import time
import sys
import zerorpc
import datetime

# Application library imports
from MySQLhandler import *
import Utility

SCRIPT_NAME = "RFIDhandler"
TIME_BEFORE_ACTIVATION = 60 * 5


print("Initialize serial connection with Arduino")
try:
    s = serial.Serial('/dev/ttyACM0', 9600)
except:
    error_msg = "Unable to connect to the Arduino"
    print(error_msg)
    Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)
    time.sleep(50000)  # Wait a moment for a possible fix
    sys.exit()  # Close the process and hope for a restart (-> supervisor)

# Each variables store an object capable of inserting, updating and deleting
# in the given t
timeshot = 0

while True:
    line = s.readline()  # Get the line sent by the Arduino
    try:
        db_devices = MySQL('devices')
        db_alarms = MySQL('alarms')
        db_users = MySQL('users')
    except:
        error_msg = "Unable to connect to the database"
        print(error_msg)
        Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)
        time.sleep(50000)
        sys.exit()
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
        is_one_alarm_up = False
        for alarm in alarms:
            is_one_alarm_up = is_one_alarm_up or bool(alarm['state'])
        if is_one_alarm_up and not state:
            for alarm in alarms:
                db_alarms.modify(alarm['id'], 'state', state)
        elif not state:
            print("[{}]: Waiting {} sec before activation".format(datetime.datetime.now().strftime("%d/%b/%Y %H:%M:%S"), TIME_BEFORE_ACTIVATION))
            time.sleep(TIME_BEFORE_ACTIVATION)
            for alarm in alarms:
                db_alarms.modify(alarm['id'], 'state', not state)
        elif state:
            print("[{}]: Deactivating".format(datetime.datetime.now().strftime("%d/%b/%Y %H:%M:%S")))
            for alarm in alarms:
                db_alarms.modify(alarm['id'], 'state', not state)
    else:
        print("[{}]: Unauthorized tag".format(datetime.datetime.now().strftime("%d/%b/%Y %H:%M:%S")))
        c = zerorpc.Client()
        c.connect("tcp://127.0.0.1:4242")
        c.RFIDError()
