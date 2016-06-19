# Standard library import
import logging
from logging.handlers import RotatingFileHandler
import sqlite3
import os
import grovepi

# Application import
from MySQLhandler import MySQL

LOG_DIR = "/home/pi/System/logs/"
PID_FILE = "/home/pi/System/PID.db"

db_devices = MySQL('devices')

def initialize_logger(name_of_script):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    # Define formatter
    formatter = logging.Formatter('%(asctime)s :: [%(levelname)s] %(message)s')

    # 1st handler for file writing
    file_handler = RotatingFileHandler(LOG_DIR + "{}.log".format(name_of_script), 'a', 1000000, 1)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    # 2nd handler for console
    steam_handler = logging.StreamHandler()
    steam_handler.setLevel(logging.DEBUG)
    logger.addHandler(steam_handler)
    # Logging config done

    # Return the logger object
    return logger


def update_PID(name_of_script, pid):
    pid_db = sqlite3.connect(PID_FILE)
    pid_cursor = pid_db.cursor()
    pid_cursor.execute("""UPDATE PID SET value = ? WHERE name = ?""", (pid, name_of_script))
    pid_db.commit()
    pid_db.close()


def get_camera_PID():
    pid_db = sqlite3.connect(PID_FILE)
    pid_cursor = pid_db.cursor()
    pid_cursor.execute("""SELECT value FROM pid WHERE name = 'camera'""")
    camera = pid_cursor.fetchone()[0]
    pid_db.close()
    return int(camera)


def launch_fatal_process_alert(script_name, error):
    # TODO: send SMS to staff
    return None


def get_alarm_state(m_id):
    db_alarms = MySQL('alarms')
    alarm = db_alarms.get('device_id', m_id)[0]
    state = alarm['state']
    return state


# Function used to change the state of the led plugged in the Raspberry
# @params
# @state int 1 or 0
def switch_led_info(state):
    info_led = int(db_devices.get('name', 'ledInfo')[0]['code'])
    grovepi.pinMode(info_led, "OUTPUT")
    grovepi.digitalWrite(info_led, state)

def sound(state):
    buzzer = int(db_devices.get('name', 'Buzzer')[0]['code'])
    grovepi.digitalWrite(buzzer, state)