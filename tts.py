#!/usr/bin/python3

import sys
import subprocess
import sqlite3
from sqlite3 import Error
import random
import math
import can
from pprint import pprint

CAN_SPEAK = 0x27F
CAN_SHUTDOWN = 0x2FF
IDGROUP_SHUTDOWN = 5
IDGROUP_STARTUP = 6

random.seed()

def sqlConnection():
	try:
		con = sqlite3.connect('tts.db')
		con.row_factory = sqlite3.Row
		return con
	except Error:
		print(Error)

def getString(con, idgroup):
	cur = con.cursor()
	cur.execute("select count(*) from strings where idgroup = ?", (idgroup,))
	row = cur.fetchone()
	if row[0] == 0:
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

def sayString(str):
# 	print(str)
	cmd = "pico2wave -w /tmp/pico2wave.wav \"{}\" && aplay /tmp/pico2wave.wav".format(str)
# 	print(cmd)
	subprocess.run([cmd], shell=True)

def sayStringFromGroup(con, idgroup):
	str = getString(con, idgroup)
	if str is not None:
		sayString(str)
	return str

def main():
	# setup
	con = sqlConnection()

# 	subprocess.run(["sudo ip link set can0 up type can bitrate 100000"], shell=True)
	bus = can.interface.Bus(bustype='socketcan_native', channel='can0')
	can_filters = [
		{"can_id": CAN_SPEAK, "can_mask": 0x7FF, "extended": False},
		{"can_id": CAN_SHUTDOWN, "can_mask": 0x7FF, "extended": False}
	]
	bus.set_filters(can_filters)
	sayStringFromGroup(con, IDGROUP_STARTUP)

	# loop
	try:
		while True:
			msg = bus.recv(0.0)
			if msg is not None:
# 				print(msg)
				pprint(msg)
				if msg.arbitration_id == CAN_SPEAK and msg.dlc == 1:
					sayStringFromGroup(con, msg.data[0])
				elif msg.arbitration_id == CAN_SHUTDOWN:
					sayStringFromGroup(con, IDGROUP_SHUTDOWN)
					subprocess.run("sudo halt", shell=True)
	except KeyboardInterrupt:
		pass
# 		subprocess.run(["sudo ip link set can0 down"], shell=True)
# 		sayString("Good bye. Talk to you later.")


if __name__ == "__main__":
	main()
