#Import logging tool
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
#Define formatter
formatter = logging.Formatter('%(asctime)s :: [%(levelname)s] %(message)s')

#1st handler for file writing
file_handler = RotatingFileHandler('activity.log', 'a', 1000000, 1)
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

def sendTo(ip, msg):
	f = open('up_pub_key', 'r')
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
state = ''

while True:
	DBdevices = MySQL('devices')
	devices = DBdevices.get('type', '2')
	
	previousState = state
	
	f = open('/home/dev/alarm/AlarmState', 'r')
	state = f.read()
	f.close()
	
	if state != previousState:
		for device in devices:
			logger.debug(device['ip'])
			sendTo(device['ip'], 'STATE:'+state)

	time.sleep(60)
