import time
import grovepi
from MySQLhandler import *
from messaging import *
import os
import signal
import sqlite3

class Alarm:
	def __init__(self, device_id):
		self.DBdevices = MySQL('devices')
		self.buzzer = int(self.DBdevices.get('name', 'Buzzer')[0]['code'])
	def SoundON(self):
        	grovepi.digitalWrite(self.buzzer, 1)
	def SoundOFF(self):
		grovepi.digitalWrite(self.buzzer, 0)
	def MotionProtocol(self):
		#getting camera PID
		pidDB = sqlite3.connect('/home/pi/System/PID.db')
		pidCursor = pidDB.cursor()
		pidCursor.execute("""SELECT value FROM PID WHERE name = 'camera'""")
		camera = pidCursor.fetchone()[0]
		ledInfo = self.DBdevices.get('name', 'ledInfo')[0]['code']
		grovepi.pinMode(int(ledInfo), "OUTPUT")
		grovepi.digitalWrite(int(ledInfo), 1)
		time.sleep(25)
		DBalarms = MySQL('alarms')
		alarms = DBalarms.all()
		isUp = False
		for alarm in alarms:
			if alarm['state'] == 1:
				os.kill(int(camera), signal.SIGUSR1)
				self.SoundON()
				SMS('Alarme declenchee').all()
				a = Mail(' ', 'Alarme', 'L\'alarme s\'est declenchee')
				a.all()
				a.send()
