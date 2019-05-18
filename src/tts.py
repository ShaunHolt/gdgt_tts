#!/usr/bin/python3

import sys
import subprocess
import sqlite3
from sqlite3 import Error
import random
import math
import can
from pygame import mixer
import time
from var_dump import var_dump

CAN_SPEAK = 0x27F
CAN_SHUTDOWN = 0x2FF
CAN_BUMP = 0x000
IDGROUP_BUMP = 2
IDGROUP_SHUTDOWN = 5
IDGROUP_STARTUP = 6

def sqlConnection():
	try:
		con = sqlite3.connect('tts.db')
		con.row_factory = sqlite3.Row
		return con
	except Error:
		print(Error)

def getFromGroup(con, idgroup):
	print("Say from group {}".format(idgroup))
	cur = con.cursor()
	cur.execute("select count(*) from strings where idgroup = ?", (idgroup,))
	row = cur.fetchone()
	if row[0] == 0:
		print("Not found")
		return None
	n = random.randrange(0, math.trunc(row[0] / 2 + 0.5))
	cur.execute("select id, text, last_used from strings where idgroup = ? order by last_used limit 1 offset ?", (idgroup, n))
	row = cur.fetchone()
	if row:
#		print(row['id'])
		cur.execute("update strings set last_used = strftime('%s', 'now') where id = ?", (row['id'],))
		con.commit()
		return row['text']
	else:
		return None

def sayString(str, vol):
# 	print(str)
	cmd = "pico2wave -w /tmp/pico2wave.wav \"{}\"".format(str)
	print(cmd)
	subprocess.run([cmd], shell=True)
	return playWav('/tmp/pico2wave.wav', vol)

def playWav(file, vol):
	sound = mixer.Sound(file)
	sound.set_volume(vol)
	print("Play with vol {}".format(vol))
	return sound.play() # returns channel

def playSoundFromGroup(con, idgroup, vol):
	str = getFromGroup(con, idgroup)
	if str is not None:
		if str.endswith('.wav'):
			print("/home/pi/sounds/{}".format(str))
			return playWav("/home/pi/sounds/{}".format(str), vol)
		else:
			return sayString(str, vol)

def main():
	defaultVol = 0.20

	# setup
	random.seed()
	mixer.init(16000)

	con = sqlConnection()

# 	subprocess.run(["sudo ip link set can0 up type can bitrate 100000"], shell=True)
	bus = can.interface.Bus(bustype='socketcan_native', channel='can0')
	can_filters = [
		{"can_id": CAN_SPEAK, "can_mask": 0x7FF, "extended": False},
		{"can_id": CAN_SHUTDOWN, "can_mask": 0x7FF, "extended": False},
		{"can_id": CAN_BUMP, "can_mask": 0x7FF, "extended": False}
	]
	bus.set_filters(can_filters)
	playSoundFromGroup(con, IDGROUP_STARTUP, defaultVol)

	# loop
	while True:
		msg = bus.recv(0.0)
		if msg is not None:
# 				print(msg)
			var_dump(msg)
			if msg.arbitration_id == CAN_SPEAK:
				if msg.dlc == 1:
					playSoundFromGroup(con, msg.data[0], defaultVol)
				elif msg.dlc > 1:
					if msg.data[0] == 0: # set volume
						defaultVol = msg.data[0] / 512
						# TODO add saving defaultVol to config file and read it back in later
					else:
						d = 0
						for i in range(1, msg.dlc):
							d = d * 256 + msg.data[i]
						if msg.data[0] == 1:
							playSoundFromGroup(con, d, defaultVol)
						else:
							playSoundFromGroup(con, d, msg.data[0] / 512)
			elif msg.arbitration_id == CAN_BUMP:
				channel = playSoundFromGroup(con, IDGROUP_BUMP, defaultVol)
			elif msg.arbitration_id == CAN_SHUTDOWN:
				channel = playSoundFromGroup(con, IDGROUP_SHUTDOWN, defaultVol)
# 				while channel.get_busy():
# 					pass
				time.sleep(3)
				subprocess.run("sudo halt", shell=True)

if __name__ == "__main__":
	main()

"""
CAN data:
DLC == 1 means play sound 0 - 255 at default volume
data[0] == 0 set default volume = data[1]
data[0] == 1 play sound = data[1...n]
data[0] > 1 play sound = data[1...n] at vol = data[0]
"""
