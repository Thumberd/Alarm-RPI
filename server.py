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
from worker import alarm_protocol

SCRIPT_NAME = "server"

logger = Utility.initialize_logger(SCRIPT_NAME)

# Defining DB connection
db_devices = MySQL('devices')
db_alarms = MySQL('alarms')
db_temperatures = MySQL('temperatures')
db_humiditys = MySQL('humiditys')
db_plant_humiditys = MySQL('plantHumiditys')

IP = "192.168.0.17"
PORT = 5400
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((IP, PORT))
logger.info("Server is listening on {}:{}".format(IP, PORT))
server.listen(5)


def handle_request(request, device):
    request = request.split('/')
    if request[0] == "temperature":
        db_temperatures.add([int(request[1]), device['id']])
    elif request[0] == "humiditys":
        db_humiditys.add([int(request[1]), device['id']])
    elif request[0] == "plantHumiditys":
        db_plant_humiditys.add([int(request[1]), device['ip']])
    elif request[0] == "alarm":
        alarm = db_alarms.get('device_id', device['id'])[0]
        if alarm['state'] == 1:
            logger.info("{device} triggered the alarm. Launching protocol.".format(device=device['name']))
            alarm_protocol.delay(device['id'])

while True:
    client, address = server.accept()
    logger.debug("Client connected from {]".format(address))
    response = (client.recv(255)).split('*')
    device = db_devices.get('token_id', response[0])[0]
    if device['token_key'] == response[1] and str(address[0]) == device['ip']:
        logger.info("Client name: {}".format(device['name']))
        req = response[2].split("&&")
        logger.debug(req)
        for order in req:
            handle_request(order, device)
    else:
        logger.warning("Unauthorized access from {}".format(address))
client.close()
server.close()
