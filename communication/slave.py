import socket
import re
import time
# create a socket object
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# get local machine name
host = str(input("Type master ip : "))
port = 9999
# connection to hostname on the port.
# s.connect((host, port))

while True:
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	received_message = ''
	try:
		s.connect((host, port))
		received_message = s.recv(1024).decode()
		s.close()
	except socket.error as e:
		print("error while connecting, master doesn't respond :: {}".format(e))
	if re.search(r'I am master', received_message):
		print("I am continuing to be slave")
	elif re.search(r'There is no orchastrator', received_message):
		print("I will become master")
	else:
		print("I should become master")

	time.sleep(10)