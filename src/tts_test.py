#!/usr/bin/python3

import sys
import subprocess
import sqlite3
from sqlite3 import Error
import random
import math

# if len(sys.argv) < 2:
# 	sys.exit('Group ID required')

random.seed()

def sqlConnection():
	try:
		con = sqlite3.connect('tts.db')
		con.row_factory = sqlite3.Row
		return con
	except Error:
		print(Error)

def getStrings(con, idgroup):
	cur = con.cursor()
	cur.execute("select id, text, last_used from strings where idgroup = ? order by last_used", (idgroup,))
	rows = cur.fetchall()
	for row in rows:
		print(row)
	print(cur.rowcount)

# def getString(con, idgroup):
# 	cur = con.cursor()
# 	cur.execute("select count(*) from strings where idgroup = ?", (idgroup,))
# 	row = cur.fetchone()
# 	n = random.randrange(0, math.trunc(row[0] / 2 + 0.5))
# 	cur.execute("select id, text, last_used from strings where idgroup = ? order by last_used", (idgroup,))
# 	row = None
# 	while n >= 0:
# 		row = cur.fetchone()
# 		n -= 1
# 	print(row)
# 	if row:
# 		print(row['id'])
# 		cur.execute("update strings set last_used = strftime('\%s', 'now') where id = ?", (row['id'],))
# 		con.commit()
# 		return row['text']
# 	else:
# 		return ""

def getString(con, idgroup):
	cur = con.cursor()
	cur.execute("select count(*) from strings where idgroup = ?", (idgroup,))
	row = cur.fetchone()
	if row[0] == 0:
		return "Speech group not found."
	n = random.randrange(0, math.trunc(row[0] / 2 + 0.5))
	cur.execute("select id, text, last_used from strings where idgroup = ? order by last_used limit 1 offset ?", (idgroup, n))
	row = cur.fetchone()
	if row:
# 		print(row['id'])
		cur.execute("update strings set last_used = strftime('\%s', 'now') where id = ?", (row['id'],))
		con.commit()
		return row['text']
	else:
		return ""

def saySomething(str):
	print(str)
	cmd = "pico2wave -w /tmp/pico2wave.wav \"{}\" && aplay /tmp/pico2wave.wav".format(str)
	print(cmd)
	subprocess.run([cmd], shell=True)

def main():
	con = sqlConnection()
	saySomething("gidget is ready to go")
	while True:
		try:
			n = input('Input:')
			if n == 'q' or n == 'Q':
				saySomething("good bye")
				sys.exit()
			n = int(n)
			print(n)
			if n:
				str = getString(con, n)
				saySomething(str)
				n = 0
		except ValueError:
			print("Not a number")

if __name__ == "__main__":
    main()
