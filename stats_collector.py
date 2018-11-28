import socket
import json
import pickle
import sys
import re

###custom lib
from lib.stats import StatsCollector

HOST = 'localhost'
PORT = 11000

while True:
	# stats_collector = StatsCollector()
	# containers_stats = stats_collector.parsed_stats()
	# encoded_stats = json.dumps(containers_stats).encode('utf-8')
	# stats_socket_for_sending = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# stats_socket_for_sending.connect((HOST, PORT))
	# stats_socket_for_sending.sendall(encoded_stats)




	received_message = ''
	try:
		stats_socket_for_sending = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		stats_socket_for_sending.connect((HOST, PORT))
		received_message = stats_socket_for_sending.recv(1024).decode()
		# stats_socket_for_sending.close()

	except socket.error as e:
		print("error while connecting, master doesn't respond :: {}".format(e))

	if re.search(r'Give me stats', received_message):
		stats_collector = StatsCollector()
		containers_stats = stats_collector.parsed_stats()
		encoded_stats = json.dumps(containers_stats).encode('utf-8')
		# stats_socket_for_sending.connect((HOST, PORT))
		stats_socket_for_sending.sendall(encoded_stats)