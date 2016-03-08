import socket
from Crypto.PublicKey import RSA
from MySQLhandler import MySQL
import os
import sqlite3
import signal

f = open('pri_key', 'r')
key = RSA.importKey(f.read())
f.close()

#Defining DB connection
db = MySQL('devices')

#Getting PID of alarm service
pidDB = sqlite3.connect('/home/pi/System/PID.db')
pidCursor = pidDB.cursor()
pidCursor.execute("""SELECT value FROM PID WHERE name='alarm'""")
alarmPID = pidCursor.fetchone()[0]

ip = "192.168.0.17"
port = 5400
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((ip, port))
print("Server is listening on " + str(ip) +":" + str(port))

server.listen(5)

while True:
        client, address = server.accept()
        print("Client connected on " + str(address))
        response = client.recv(255)
        res = key.decrypt(response)
	code = res[0:2]
	device = db.get('code', code)
	if device:
		print(device['name'])
		if res[2:] == "ALARM":
			print("Alarme")
			os.kill(int(alarmPID), signal.SIGUSR1)		

print("Close")
client.close()
stock.close()

