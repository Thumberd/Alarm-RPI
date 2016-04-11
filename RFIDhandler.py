#Import logging tool
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
#Define formatter
formatter = logging.Formatter('%(asctime)s :: [%(levelname)s] %(message)s')

#1st handler for file writing
file_handler = RotatingFileHandler('/home/pi/System/logs/RFIDhandler.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
#2nd handler for console
steam_handler = logging.StreamHandler()
steam_handler.setLevel(logging.DEBUG)
logger.addHandler(steam_handler)
#Logging config done

logger.info("Base imports")
import serial
import time
from MySQLhandler import *
import sys
from messaging import *
from AlarmClass import *
import zerorpc
from AlarmClass import Alarm
import grovepi

logger.info("Intialize serial connection with Arduino")
try:
	s = serial.Serial('/dev/ttyACM0', 9600)
except:
	logger.critical("Can't connect to the Arduino")
	sys.exit()

DBdevices = MySQL('devices')
DBalarm = MySQL('alarms')
usersDB = MySQL('users')
timeshot = 0

while True:
	line = s.readline()
	logger.debug(line.split('\r'))
	a = usersDB.get('RFID', line.split('\r')[0])
	if a != None:
		ledInfo = DBdevices.get('name', 'ledInfo')[0]['code']
		grovepi.pinMode(int(ledInfo), "OUTPUT")
		grovepi.digitalWrite(int(ledInfo), 0)
		c = zerorpc.Client()
		c.connect("tcp://127.0.0.1:4242")
		logger.debug(c.RFID())
		Alarm().SoundOFF()
		if time.time() - timeshot < 10 and time.time() - timeshot > 1:
			alarms = DBalarm.all()
			state = bool(alarms[0]['state'])
			if state == False:
				print("Waiting")
				time.sleep(120)
			for alarm in alarms:
				print(alarm['id'])
				DBalarm.modify(alarm['id'], 'state', not state)
			logger.info("Alarme modifiee partout")
		else:
			timeshot = 0
		timeshot = time.time()
	else:
		logger.warning("Unauthorized tag")
		c = zerorpc.Client()
		c.connect("tcp://127.0.0.1:4242")
		print(c.RFIDError())
