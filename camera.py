
import time
import picamera
import sqlite3
import signal
import os
import shutil

pidDB = sqlite3.connect('/home/pi/System/PID.db')
pidCursor = pidDB.cursor()
actualPID = os.getpid()
print("I'm PID " + str(actualPID))
pidCursor.execute("""UPDATE PID SET value = ? WHERE name = ?""", (actualPID, "camera"))
pidDB.commit()

"""Function to take timelapse"""
def CameraFootage(signum, stack):
	print("Received:" + str(signum))
	if signum == 10:
		print("Beginning timelapse")
		with picamera.PiCamera() as camera:
			camera.start_preview()
			camera.annotate_text = time.strftime('%Y-%m-%d %H:%M:%S')
			time.sleep(1)
			shutil.rmtree('/home/dev/www/public/media/')
			os.mkdir('/home/dev/www/public/media')
			i = 0
			for filename in camera.capture_continuous('/home/dev/www/public/media/img{counter:03d}.jpg'):
				if i < 20:
					print("Captured %s" %filename)
					time.sleep(1)
					i = i +1
				else:
					i = 0
					break

signal.signal(signal.SIGUSR1, CameraFootage)

while True:
	time.sleep(3)
