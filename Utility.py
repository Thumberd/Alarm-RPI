# Standard library import
import logging
from logging.handlers import RotatingFileHandler
import sqlite3
import os
import grovepi
import socket
from messaging import SMS
# Application import
from MySQLhandler import MySQL

LOG_DIR = "/home/pi/System/logs/"
PID_FILE = "/home/pi/System/PID.db"


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
    SMS(error).to_staff()
    return None


def get_alarm_state(m_id):
    db_alarms = MySQL('alarms')
    alarm = db_alarms.get('device_id', m_id)[0]
    state = alarm['state']
    db_alarms.close()
    return state


# Function used to change the state of the led plugged in the Raspberry
# @params
# @state int 1 or 0
def switch_led_info(state):
    db_devices = MySQL('devices')
    info_led = int(db_devices.get('name', 'ledInfo')[0]['code'])
    grovepi.pinMode(info_led, "OUTPUT")
    grovepi.digitalWrite(info_led, state)
    db_devices.close()

def sound(state):
    db_devices = MySQL('devices')
    buzzer = int(db_devices.get('name', 'Buzzer')[0]['code'])
    grovepi.digitalWrite(buzzer, state)
    if state == 1:    
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('192.168.0.47', 3458))
        s.send("SOUNDGOON".encode())
        print("Okkkk")
    db_devices.close()
