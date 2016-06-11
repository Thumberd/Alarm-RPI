from celery import Celery
from celery.schedules import crontab
from celery.decorators import periodic_task

from MySQLhandler import MySQL
import Utility

from datetime import datetime

SCRIPT_NAME = "celery"

logger = Utility.initialize_logger(SCRIPT_NAME)

scheduled = MySQL('scheduled')
alarms = MySQL('alarms')

celery = Celery('worker', broker='amqp://guest:guest@localhost')

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
    # Each variables store an object capable of inserting, updating and deleting
    # in the given table
    try:
        db_devices = MySQL('devices')
        db_alarms = MySQL('alarms')
    except:
        error_msg = "Unable to connect to the database"
        logger.fatal(error_msg)
        Utility.launch_fatal_process_alert(SCRIPT_NAME, error_msg)

    # Get all the alarms which are currently ON
    alarm_up = db_alarms.get('state', 1)
    if alarm_up:
        for alarm in alarm_up:
            #Get the time since the alarm's state changed
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