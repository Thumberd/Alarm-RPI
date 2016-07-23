# Standard library imports
import socket
import grovepi
import time
import os
import signal
import picamera
import shutil
import requests
import bs4
import sqlite3
import random

# Third party imports
from celery import Celery
from celery.schedules import crontab
from celery.decorators import periodic_task

# Application imports
from MySQLhandler import MySQL
import Utility
from messaging import *

from datetime import datetime

SCRIPT_NAME = "Celery2"
SALT = "first"
TIME_BEFORE_ALARM = 60 * 5
EVENT_IDENTIFIER = 1

STRING_ALARM_TITLE = "Alarme declenchee"
STRING_ALARM_CONTENT = "Le capteur {sensor} s est declenchee a {hour}:{minute}."

logger = Utility.initialize_logger(SCRIPT_NAME)

scheduled = MySQL('scheduled')
alarms = MySQL('alarms')

celery = Celery('worker', broker='amqp://guest:guest@localhost')

db = sqlite3.connect("code.db")
c = db.cursor()

def send_to(ip, msg):
    r = requests.get("http://{ip}:3540/alarm/{state}".format(ip=ip, state=msg))
    

# Each variables store an object capable of inserting, updating and deleting
# in the given table
try:
   db_devices = MySQL('devices')
   db_alarms = MySQL('alarms')
   db_temperatures = MySQL('temperatures')
except:
   error_msg = "Unable to connect to the database"
   logger.fatal(error_msg)
   Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)

@periodic_task(run_every=crontab(hour='*', minute='*/5'))
def checkBaseTemperature():
    temp = grovepi.temp(1)
    db_temperatures.add([round(temp,2), 21])

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
    print("tets")
    logger.info("Checking alarm")
    # Get all the alarms which are currently ON
    alarm_up = db_alarms.get('state', 1)
    if alarm_up:
        for alarm in alarm_up:
            # Get the time since the alarm's state changed
            duree = datetime.now() - alarm['updated_at']
            if duree.total_seconds() < 120.0:
                device = db_devices.get('id', alarm['device_id'])[0]
                if device['ip'] != "":
                    send_to(device['ip'], "ON")
    # Get all the alarm which are currently OFF
    alarmDOWN = db_alarms.get('state', 0)
    if alarmDOWN:
        for alarm in alarmDOWN:
            duree = datetime.now() - alarm['updated_at']
            if duree.total_seconds() < 120.0:
                device = db_devices.get('id', alarm['device_id'])[0]
                if device['ip'] != "":
                    send_to(device['ip'], "OFF")


@periodic_task(run_every=crontab(hour='*', minute='*/3'))
def check_for_alarm_led_status():
    alarm = db_alarms.all()[0]
    if alarm['state'] == False:
        Utility.switch_led_info(0)

@periodic_task(run_every=crontab(hour='3', minute='0'))
def change_UI_background():
    BASE_URL = "http://apod.nasa.gov/"
    PAGE = "apod/astropix.html"
    nasa_page = requests.get(BASE_URL + PAGE)
    if nasa_page.status_code == 200:
        soup = bs4.BeautifulSoup(nasa_page.text)
        img_link = soup.body.center.find_all('p')[1].find('img')['src']
        img_r = requests.get(BASE_URL + img_link, stream=True)
        if img_r.status_code == 200:
            with open('/home/pi/ElectronUI-RPI/iotd.jpg', 'wb') as f:
                img_r.decode_content = True
                shutil.copyfileobj(img_r.raw, f)
    
# Asynchronous process triggered when the motion sensor detects activity
# and only if the alarm is set to ON
@celery.task
def alarm_protocol(alarm_id):
    print("aLaunv")
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
        #os.mkdir('/home/dev/www/public/media')
        i = 0
        for filename in camera.capture_continuous('/home/dev/www/public/media/img{counter:03d}.jpg'):
            if i < 20:
                time.sleep(0.5)
                i += 1
            else:
                break
        logger.info("Timelapse captured")

@celery.task
def send_code_garage(garage_id, ip, user_id):
    code = ""
    for i in range(0, 8):
        code += str(random.randrange(0,9))
    c.execute("INSERT INTO 'code'('code', 'garage_id', 'time', 'user_id', 'ip') VALUES (?, ?, datetime(), ?, ?)", (code, garage_id, user_id, ip))
    db.commit()
