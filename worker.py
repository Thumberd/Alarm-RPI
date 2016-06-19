# Standard library imports
import socket
import grovepi
import time
import os
import signal
import picamera
import shutil

# Third party imports
from celery import Celery
from celery.schedules import crontab
from celery.decorators import periodic_task

# Application imports
from MySQLhandler import MySQL
import Utility
from messaging import *

from datetime import datetime

SCRIPT_NAME = "celery"
SALT = "first"
TIME_BEFORE_ALARM = 500
EVENT_IDENTIFIER = 1

STRING_ALARM_TITLE = "Alarme declenchee"
STRING_ALARM_CONTENT = "Le capteur {sensor} s'est declenchee a {hour}:{minute}."

logger = Utility.initialize_logger(SCRIPT_NAME)

scheduled = MySQL('scheduled')
alarms = MySQL('alarms')

celery = Celery('worker', broker='amqp://guest:guest@localhost')


def send_to(ip, msg):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, 5400))
        s.send(SALT + msg)
        s.close()
    except:
        logger.error("Error: ")

# Each variables store an object capable of inserting, updating and deleting
# in the given table
try:
   db_devices = MySQL('devices')
   db_alarms = MySQL('alarms')
except:
   error_msg = "Unable to connect to the database"
   logger.fatal(error_msg)
   Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)

@periodic_task(run_every=crontab(hour='*', minute='*'))
def check_for_alarm_scheduled():
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    for aScheduled in scheduled.all():
        if int(aScheduled['beginHour']) == hour and int(aScheduled['beginMinute']) == minute:
            alarm = alarms.get('id', aScheduled['alarm_id'])[0]
            alarms.modify(alarm['id'], 'state', True)
        elif int(aScheduled['endHour']) == hour and int(aScheduled['endMinute']) == minute:
            alarm = alarms.get('id', aScheduled['alarm_id'])[0]
            alarms.modify(alarm['id'], 'state', False)


@periodic_task(run_every=crontab(hour='*', minute='*'))
def check_for_alarm_notifications():
    # Get all the alarms which are currently ON
    alarm_up = db_alarms.get('state', 1)
    if alarm_up:
        for alarm in alarm_up:
            # Get the time since the alarm's state changed
            duree = datetime.now() - alarm['updated_at']
            if duree.total_seconds() < 120.0:
                device = db_devices.get('id', alarm['device_id'])[0]
                if device['ip'] != "":
                    send_to(device['ip'], "STATE1")
    # Get all the alarm which are currently OFF
    alarmDOWN = db_alarms.get('state', 0)
    if alarmDOWN:
        for alarm in alarmDOWN:
            duree = datetime.now() - alarm['updated_at']
            if duree.total_seconds() < 120.0:
                device = db_devices.get('id', alarm['device_id'])[0]
                if device['ip'] != "":
                    send_to(device['ip'], "STATE0")


@periodic_task(run_every=crontab(hour='*', minute='*/3'))
def check_for_alarm_led_status():
    alarm = db_alarms.all()[0]
    if alarm['state'] == False:
        Utility.switch_led_info(0)


# Asynchronous process triggered when the motion sensor detects activity
# and only if the alarm is set to ON
@celery.task
def alarm_protocol(alarm_id):
    Utility.switch_led_info(1)
    time.sleep(TIME_BEFORE_ALARM)  # Wait [TIME_BEFORE_ALARM]/60 minutes
    alarms = db_alarms.all()
    device = db_devices.get('id', int(alarm_id))  # Get the device specified
    db_events = MySQL('events')
    db_users = MySQL('users')
    for alarm in alarms:
        if alarm['state'] == 1:
            now = datetime.now()
            # Send a notification to each user
            Utility.sound(1)
            SMS(STRING_ALARM_CONTENT.format(sensor=device[0]['name'], hour=now.hour, minute=now.minute)).all()
            for user in db_users.all():
                db_events.add([STRING_ALARM_TITLE,
                               STRING_ALARM_CONTENT.format(sensor=device[0]['name'], hour=now.hour, minute=now.minute),
                               " ",
                               EVENT_IDENTIFIER,
                               user['id'],
                               0])
            timelapse.delay()
            break


@celery.task
def timelapse():
    logger.debug("Beginning timelapse")
    with picamera.PiCamera() as camera:
        camera.start_preview()
        camera.annotate_text = time.strftime('%Y-%m-%d %H:%M:%S')
        time.sleep(1)
        shutil.rmtree('/home/dev/www/public/media/')
        os.mkdir('/home/dev/www/public/media')
        i = 0
        for filename in camera.capture_continuous('/home/dev/www/public/media/img{counter:03d}.jpg'):
            if i < 20:
                time.sleep(0.5)
                i += 1
            else:
                break
        logger.info("Timelapse captured")
