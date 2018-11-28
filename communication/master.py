 # server.py 
import socket
import time
import psutil
# create a socket object
mastersocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# get local machine name
host = socket.gethostname()
# host = '10.102.7.123'
print(host)
port = 9999
# bind to the port
mastersocket.bind((host, port))
# queue up to 5 requests
mastersocket.listen(5)

while True:
	# establish a connection
	clientsocket,addr = mastersocket.accept()
	print("Got a connection from %s" % str(addr))
	currentTime = time.strftime("%Y/%m/%d %H:%M:%S +0000", time.gmtime())
	orchastrator_pid = None
	for proc in psutil.process_iter():
	    if proc.name() == "Orchastrator":
	    	orchastrator_pid = proc
	# orchastrator_pid = 1
	if orchastrator_pid:		
		message = "I am master orchastrator {}".format(currentTime)
		clientsocket.sendall(message.encode('utf-8'))
		clientsocket.close()
	else:
		message = "There is no orchastrator here on {} => {}".format(host, currentTime)
		clientsocket.sendall(message.encode('utf-8'))
		clientsocket.close()

	time.sleep(30)