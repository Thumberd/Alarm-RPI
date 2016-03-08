#Import logging tool
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
#Define formatter
formatter = logging.Formatter('%(asctime)s :: [%(levelname)s] %(message)s')

#1st handler for file writing
file_handler = RotatingFileHandler('alarm.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
#2nd handler for console
steam_handler = logging.StreamHandler()
steam_handler.setLevel(logging.DEBUG)
logger.addHandler(steam_handler)
#Logging config done

logger.info("Base imports")
import signal
import time
import grovepi
import os
import sqlite3

#PID Updating
logger.info("Updating PID")

pidDB = sqlite3.connect('/home/pi/System/PID.db')
pidCursor = pidDB.cursor()
actualPID = os.getpid()
logger.info("I'm PID " + str(actualPID))
pidCursor.execute("""UPDATE PID SET value = ? WHERE name = ?""", (actualPID, "alarm"))
pidDB.commit()


def AlarmState():
	f = open('/home/dev/alarm/AlarmState', 'r')
	state = f.read()
	f.close()
	if '1' in state:
		return True
	elif '0' in state:
		return False

def WirelessPIR(signum, stack):
	if AlarmState():
		print("Alarm")

signal.signal(signal.SIGUSR1, WirelessPIR)

t = 0
i = 0

while True:
	if AlarmState() == True:
		a = grovepi.digitalRead(2)
		if a ==	1:
			t = t + 1
		if t == 5:
			print("Alarme")
			i = 0
			t = 0
		if i > 50:
			i = 0
			t = 0
		time.sleep(0.5)
	else:
		time.sleep(60)


