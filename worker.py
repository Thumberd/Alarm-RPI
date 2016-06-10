from celery import Celery
from celery.schedules import crontab
from celery.decorators import periodic_task

from MySQLhandler import MySQL

from datetime import datetime

scheduled = MySQL('scheduled')
alarms = MySQL('alarms')

celery = Celery('worker', broker='amqp://guest:guest@localhost')

@periodic_task(run_every=crontab(hour='*', minute='*'))
def checkForAlarms():
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

