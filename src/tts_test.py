#!/usr/bin/python3

import sys
import subprocess
import sqlite3
from sqlite3 import Error
import random
import math
from pygame import mixer
import time
from var_dump import var_dump

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
# 	cmd = "pico2wave -w /tmp/pico2wave.wav \"{}\" && aplay /tmp/pico2wave.wav".format(str)
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

	playSoundFromGroup(con, IDGROUP_STARTUP, defaultVol)

	# loop
	while True:
		try:
			n = input('Input:')
			if n == 'q' or n == 'Q':
				channel = playSoundFromGroup(con, IDGROUP_SHUTDOWN, defaultVol)
# 				while channel.get_busy():
# 					pass
				time.sleep(3)
				sys.exit()
			if n.startswith('v') or n.startswith('V'):
				n = int(n[1:])
# 				print(n)
				if n >= 0 and n <= 255:
					defaultVol = int(n / 512 * 100) / 100
					var_dump(defaultVol)
					sayString("Volume set to {}.".format(defaultVol), defaultVol)
			else:
				n = int(n)
# 				print(n)
				if n:
					playSoundFromGroup(con, n, defaultVol)
		except ValueError:
			print("Not a number")

if __name__ == "__main__":
	main()

