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
from datetime import datetime
import socket


# Third party imports
from celery import Celery
from celery.schedules import crontab
from celery.decorators import periodic_task

# Application imports
from MySQLhandler import MySQL
import Utility
from messaging import *


SCRIPT_NAME = "Celery"
SALT = "first"
TIME_BEFORE_ALARM = 60 * 5
MAX_TIME_FOR_VALIDATION_CODE = 60 * 130
EVENT_IDENTIFIER = 1
EVENT_IDENTIFIER_PLANT = 2

STRING_ALARM_TITLE = "Alarme declenchee"
STRING_ALARM_CONTENT = "Le capteur {sensor} s'est declenchee a {hour}:{minute}."

STRING_PLANT_WATERING = "Une plante a besoin de vous !"
STRING_PLANT_WATERING_CONTENT = "La plante {plant} a besoin d'eau !"

BASE_URL = "http://apod.nasa.gov/"
PAGE = "apod/astropix.html"

alarms = MySQL('alarms')

celery = Celery('worker', broker='amqp://guest:guest@localhost:5672//')

def send_to(ip, msg):
    r = requests.get("http://{ip}:3540/alarm/{state}".format(ip=ip, state=msg))
    


@periodic_task(run_every=crontab(hour='*', minute='*/5'))
def checkBaseTemperature():
    try:
        try:
            db_datas = MySQL('datas')
            db_devices = MySQL('devices')
        except:
            error_msg = "Unable to connect to the database"
            print(error_msg)
            Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)
        for device in db_devices.all():
            try:
                code = int(device['code'])
            except:
                print("")
            else:
                if device['type'] == 4 and code > 0 and code < 3:
                    try:
                        temp = grovepi.temp(code)
                    except ValueError as e:
                        print("Received ValueError")
                        print(e)
                    else:
                        db_datas.add([1, round(temp, 2), device['id']])
                        print("Temperature / {} / {}".format(device['name'],temp))
        db_datas.close()
        db_devices.close()
    except Exception as e:
        print("Something has gone dirty fetching the temperature.")

@periodic_task(run_every=crontab(hour='*', minute='*/2'))
def checkPlantWatering():
    try:
        db_datas = MySQL('datas')
        db_events = MySQL('events')
        db_users = MySQL('users')
        db_devices = MySQL('devices')
    except:
        error_msg = "Unable to connect to the database"
        print(error_msg)
        Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)
    for device in db_devices.all():
        if device['type'] == 4:
            cursor = db_datas.connection.cursor()
            cursor.execute("SELECT * FROM datas WHERE device_id = {id} AND data_type = 3 ORDER BY created_at DESC LIMIT 0,2".format(id=device['id']))
            result = cursor.fetchall()
            if result:
                if not result[1]['value'] > 55:
                    if result[0]['value'] > 55:
                        for user in db_users.all():
                            db_events.add([STRING_PLANT_WATERING,
                                       STRING_PLANT_WATERING_CONTENT.format(plant=device['name']),
                                       " ",
                                       EVENT_IDENTIFIER_PLANT,
                                       user['id'],
                                       0])



@periodic_task(run_every=crontab(hour='*', minute='*'))
def check_for_alarm_scheduled():
    try:
        db_scheduled = MySQL('scheduled')
        db_alarms = MySQL('alarms')
    except:
        error_msg = "Unable to connect to the database"
        print(error_msg)
        Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    for aScheduled in db_scheduled.all():
        if int(aScheduled['beginHour']) == hour and int(aScheduled['beginMinute']) == minute:
            alarm = db_alarms.get('id', aScheduled['alarm_id'])[0]
            if bool(alarm['state']) == False:
                db_alarms.modify(alarm['id'], 'state', True)
        elif int(aScheduled['endHour']) == hour and int(aScheduled['endMinute']) == minute:
            alarm = db_alarms.get('id', aScheduled['alarm_id'])[0]
            # Checking if the alarm was already activated before the scheduled
            # So if the guy is in holidays the alarm don't go off
            t1 = datetime.strptime(str(aScheduled['beginHour']) +':' + str(aScheduled['beginMinute']), '%H:%M')
            t2 = datetime.strptime(str(aScheduled['endHour']) + ':' + str(aScheduled['endMinute']), '%H:%M')
            delta = (t2 - t1)  # Difference between the activation time and deactivation
            # Now checking the difference between the alarm real activation time
            activation_time = alarm['updated_at']
            delta_activation = (now - activation_time)
            if delta_activation.total_seconds() < delta.total_seconds() - 1000 and delta_activation.total_seconds() > delta.total_seconds() + 1000:
                print("Activated before the scheduled, do nothing")
            else:
                db_alarms.modify(alarm['id'], 'state', False)
    db_alarms.close()
    db_scheduled.close()


@periodic_task(run_every=crontab(hour='*', minute='*'))
def check_for_alarm_notifications():
    try:
        db_alarms = MySQL('alarms')
        db_devices = MySQL('devices')
    except Exception as e:
        error_msg = "Unable to connect to the database"
        print(error_msg)
        Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)
    else:
        # Get all the alarms which are currently ON
        alarm_up = db_alarms.get('state', 1)
        if alarm_up:
            for alarm in alarm_up:
                # Get the time since the alarm's state changed
                duree = datetime.now() - alarm['updated_at']
                if duree.total_seconds() < 60 * 6:
                    device = db_devices.get('id', alarm['device_id'])[0]
                    if device['ip'] != "":
                        try:
                            send_to(device['ip'], "ON")
                        except Exception as e:
                            print(e)
                            error_msg = "Problem sending the new state to the devices."
                            Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)
        # Get all the alarm which are currently OFF
        alarmDOWN = db_alarms.get('state', 0)
        if alarmDOWN:
            for alarm in alarmDOWN:
                duree = datetime.now() - alarm['updated_at']
                if duree.total_seconds() < 60 * 6:
                    device = db_devices.get('id', alarm['device_id'])[0]
                    if device['ip'] != "":
                        try:
                            send_to(device['ip'], "OFF")
                        except Exception as e:
                            error_msg = "Problem sending the new state to the devices."
                            print(e)
                            Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)
        db_alarms.close()
        db_devices.close()


@periodic_task(run_every=crontab(hour='*', minute='*'))
def monitoring_pi():
    try:
        db_devices = MySQL('devices')
    except:
        error_msg = "Unable to connect to the database"
        print(error_msg)
        Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)
    else:
        for device in db_devices.all():
            if device['type'] == 2 and device['ip'] != '':
                try:
                    r = requests.get("http://{}:3540/ping".format(device['ip']))
                    if r.text != "Pong":
                        error_msg = "Unable to ping the Pi"
                        print(error_msg)
                        Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)
                        reboot.delay(device['ip'])
                except Exception as e:
                    error_msg = "Unable to ping the Pi"
                    print(e)
                    print(error_msg)
                    Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)
                    reboot.delay(device['ip'])
    db_devices.close()
        

@periodic_task(run_every=crontab(hour='*', minute='*/3'))
def check_for_alarm_led_status():
    try:
        db_alarms = MySQL('alarms')
    except:
        error_msg = "Unable to connect to the database"
        print(error_msg)
        Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)
    alarm = db_alarms.all()[0]
    if alarm['state'] == False:
        Utility.switch_led_info(0)
    db_alarms.close()


@periodic_task(run_every=crontab(hour='*', minute='10'))
def remove_old_codes():
    i = 0
    try:
        db = sqlite3.connect("code.db")
        c = db.cursor()
        c.execute("SELECT * FROM code ")
        for data in c.fetchall():
            time_code = datetime.strptime(data[2], "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            difference = now - time_code
            if difference.total_seconds() > MAX_TIME_FOR_VALIDATION_CODE:
                i += 1
                c.execute("DELETE FROM code WHERE id= ?", (data[0], ))
                db.commit()
        db.close()
        if i > 0:
            print("Deleted {} old codes".format(i))
    except Exception as e:
        error_msg = "Error during the delete of the old codes"
        print(e)
        Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)


@celery.task
def reboot(ip):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, 5400))
    s.send(u'{}*RBT'.format(SALT))
    s.close()


# Asynchronous process triggered when the motion sensor detects activity
# and only if the alarm is set to ON
@celery.task
def alarm_protocol(alarm_id):
    try:
        print("Alarm protocol launched")
        try:
            db_alarms = MySQL('alarms')
            db_devices = MySQL('devices')
            db_events = MySQL('events')
            db_users = MySQL('users')
        except:
            error_msg = "Unable to connect to the database"
            print(error_msg)
            Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)
        try:
            Utility.switch_led_info(1)
        except:
            error_msg = "Unable to switch lamp"
            print(error_msg)
            Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)
        time.sleep(TIME_BEFORE_ALARM)  # Wait [TIME_BEFORE_ALARM]/60 minutes
        alarms = db_alarms.all()
        device = db_devices.get('id', int(alarm_id))  # Get the device specified
        for alarm in alarms:
            if alarm['state'] == 1:
                now = datetime.now()
                # Send a notification to each user
                try:
                    SMS(STRING_ALARM_CONTENT.format(sensor=device[0]['name'], hour=now.hour, minute=now.minute)).all()
                except Exception as e:
                    error_msg = "Can't send SMS"
                    print(error_msg)
                    Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)
                try:
                    for user in db_users.all():
                        db_events.add([STRING_ALARM_TITLE,
                                       STRING_ALARM_CONTENT.format(sensor=device[0]['name'], hour=now.hour, minute=now.minute),
                                       " ",
                                       EVENT_IDENTIFIER,
                                       user['id'],
                                       0])
                except Exception as e:
                    error_msg = "Can't inform user"
                    print(e)
                    Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)
                timelapse.delay()
                Utility.sound(1)
                break
        db_devices.close()
        db_alarms.close()
        db_events.close()
        db_users.close()
    except Exception as e:
        print(e)
        Utility.launch_fatal_process_alert(SCRIPT_NAME, e)


@celery.task
def timelapse():
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
    print("Timelapse captured")


@celery.task
def send_code_garage(garage_id, ip, user_id):
    db = sqlite3.connect("code.db")
    c = db.cursor()
    code = ""
    for i in range(0, 8):
        code += str(random.randrange(0,9))
    print(code)
    c.execute("INSERT INTO 'code'('code', 'garage_id', 'time', 'user_id', 'ip') VALUES (?, ?, datetime(), ?, ?)", (code, garage_id, user_id, ip))
    db.commit()
    SMS(code).byID(user_id)
    db.close()


@celery.task
def garage_authorized(garage_id, ip, user_id):
    try:
        db_devices = MySQL('devices')
        db_users = MySQL('users')
    except:
        error_msg = "Unable to connect to the database"
        print(error_msg)
        Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)
    user = db_users.get('id', user_id)
    if "192.168" in ip and user != None:
        r = requests.get("http://192.168.0.50:3540/garage/{}".format(garage_id))
        print("Go up garage {}".format(garage_id))
    db_devices.close()
    db_users.close()


@celery.task
def send_validation_code(code, ip, user_id):
    db = sqlite3.connect("code.db")
    c = db.cursor()
    print("Received validation code {}".format(code))
    c.execute("SELECT * FROM code WHERE code = ?", (code, ))
    data = c.fetchone()
    if int(data[1]) == int(code):
        time_code = datetime.strptime(data[2], "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        difference = now - time_code
        print(difference.total_seconds())
        if difference.total_seconds() < MAX_TIME_FOR_VALIDATION_CODE:
            if ip == data[5] and data[4] == user_id:
                print("Go up garage ! {}".format(data[3]))
                r = requests.get("http://192.168.0.50:3540/garage/{}".format(data[3]))
    db.close()
