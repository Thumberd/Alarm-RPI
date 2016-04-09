#Import logging tool
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
#Define formatter
formatter = logging.Formatter('%(asctime)s :: [%(levelname)s] %(message)s')

#1st handler for file writing
file_handler = RotatingFileHandler('/home/pi/System/logs/alarmStateHandler.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
#2nd handler for console
steam_handler = logging.StreamHandler()
steam_handler.setLevel(logging.DEBUG)
logger.addHandler(steam_handler)
#Logging config done

from MySQLhandler import MySQL
import time
import socket
from Crypto.PublicKey import RSA
from datetime import datetime

def sendTo(ip, msg):
	f = open('/home/pi/System/up_pub_key', 'r')
	UPkey = RSA.importKey(f.read())
	f.close()

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		s.connect((ip, 5400))
		s.send(UPkey.encrypt('10'+msg, 32)[0])
		s.close()
	except:
		logger.error("Erreur")

#Initialize database connection
DBdevices = MySQL('devices')
DBalarm = MySQL('alarms')

while True:
	alarmUP = DBalarm.get('state', 1)
	if alarmUP:
		for alarm in alarmUP:
			duree = datetime.now() - alarm['updated_at']
			if duree.total_seconds() < 120.0:
				device = DBdevices.get('id', alarm['device_id'])[0]
				if device['ip'] != "":
					sendTo(device['ip'], "STATE1")

	alarmDOWN = DBalarm.get('state', 0)
	if alarmDOWN:
		for alarm in alarmDOWN:
			duree = datetime.now() - alarm['updated_at']
			if duree.total_seconds() < 120.0:
				device = DBdevices.get('id', alarm['device_id'])[0]
				if device['ip'] != "":
					sendTo(device['ip'], "STATE0")
	time.sleep(60)
