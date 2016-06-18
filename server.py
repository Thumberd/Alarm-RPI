# Import standard library
import socket
from Crypto.PublicKey import RSA
import os
import sqlite3
import signal

# Application import
from AlarmClass import Alarm
from MySQLhandler import MySQL
import Utility

SCRIPT_NAME = "server"

logger = Utility.initialize_logger(SCRIPT_NAME)

# Defining DB connection
db_devices = MySQL('devices')
db_alarms = MySQL('alarms')

# Get camera PID
camera_pid = Utility.get_camera_PID()

IP = "192.168.0.17"
PORT = 5400
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((IP, PORT))
logger.info("Server is listening on {}:{}".format(IP, PORT))
server.listen(5)

while True:
    client, address = server.accept()
    logger.debug("Client connected from {]".format(address))
    response = client.recv(255)
    code = response[0:2]
    device = db_devices.get('code', code)[0]
    if device:
        logger.debug("Client name: {}".format(device['name']))
        if response[2:] == "ALARM":
            deviceAlarm = db_alarms.get('device_id', device['id'])[0]
            if deviceAlarm['state'] == 1:
                print("Alarme")
                Alarm(device['id']).MotionProtocol()
    else:
        print(res)
print("Close")
client.close()
stock.close()
