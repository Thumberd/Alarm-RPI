# Standard library import
import time
import socket
from Crypto.PublicKey import RSA
from datetime import datetime

# Application import
from MySQLhandler import MySQL
import Utility

SCRIPT_NAME = "alarmStateHandler"

logger = Utility.initialize_logger(SCRIPT_NAME)


def sendTo(ip, msg):
    f = open('/home/pi/System/up_pub_key', 'r')
    UPkey = RSA.importKey(f.read())
    f.close()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, 5400))
        s.send(UPkey.encrypt('10' + msg, 32)[0])
        s.close()
    except:
        logger.error("Erreur")


# Each variables store an object capable of inserting, updating and deleting
# in the given table
try:
    db_devices = MySQL('devices')
    db_alarms = MySQL('alarms')
except:
    error_msg = "Unable to connect to the database"
    logger.fatal(error_msg)
    Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)

while True:
    # Get all the alarms which are currently ON
    alarm_up = db_alarms.get('state', 1)
    if alarm_up:
        for alarm in alarm_up:
            duree = datetime.now() - alarm['updated_at']
            if duree.total_seconds() < 120.0:
                device = db_devices.get('id', alarm['device_id'])[0]
                if device['ip'] != "":
                    sendTo(device['ip'], "STATE1")

    alarmDOWN = db_alarms.get('state', 0)
    if alarmDOWN:
        for alarm in alarmDOWN:
            duree = datetime.now() - alarm['updated_at']
            if duree.total_seconds() < 120.0:
                device = db_devices.get('id', alarm['device_id'])[0]
                if device['ip'] != "":
                    sendTo(device['ip'], "STATE0")
    time.sleep(60)
