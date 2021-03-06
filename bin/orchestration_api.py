import time
import sys
import re
import os
import fcntl
import socket
import select
import json
from random import randint
from collections import deque
from ast import literal_eval
###custom libs
sys.path.append('/opt/containers/orchestrator/')
from lib.decision_maker import DecisionMaker
from lib.ConfigSupervisor import ConfigSupervisor
from lib.stats import StatsCollector
# from lib.swarming import SwarmManagment
from lib.containering import ContainerManagement
from lib.containering import parse_config
from lib.containering import update_config
sys.path.append('/opt/containers/ocpytools/lib/')
from logger import Logger
from etcd3_client import EtcdManagement




def get_initial_obj_instances():
	"""
	Returns:
		tuple
	"""
	return (DecisionMaker(), \
			EtcdManagement(), \
	        ConfigSupervisor(),\
			ContainerManagement())


def get_obj_instances():
	"""
	Returns:
		tuple
	"""
	return (Logger(filename = "orchestrator", logger_name="Orchestrator API", \
					dirname="/aux1/ocorchestrator/"))


def processing_admin_requests(admin_socket, decision_maker, container_manager, logger):
	flag = True
	admin_requests = []
	while flag:
		admin_request = None
		try:
			admin_clientsocket, admin_adr = admin_socket.accept()
			admin_request = admin_clientsocket.recv(1024).decode()
		except BlockingIOError:
			# logger.info("There aren't any request from orchestrator_adm"\
			# 			" in the admin_socket on port 11001")
			pass
		if admin_request:
			admin_requests.append(admin_request)
			logger.info("Received command from orchestrator_adm => {}".format(admin_request))
		else:
			flag = False
	if admin_requests:
		for req in admin_requests:
			if re.search(r'stop', req, flags=re.I|re.S):
				match = re.match(r'stop\s+(.*?$)', req, flags=re.I|re.S)
				logger.info("Container => {} will be stopped by admin request". \
					format(match.group(1)))
				container_manager.stop_container_2(name = match.group(1))
			elif re.search(r'start', req, flags=re.I|re.S):
				match = re.match(r'start\s+(.+?)\s+(.+?$)', req, flags=re.I|re.S)
				logger.info("Container => {} on host => {} will be started by admin request". \
					format(match.group(1), match.group(2)))
				container_manager.run_container(host_ip = match.group(2), \
												application = match.group(1))
			elif re.search(r'release', req, flags=re.I|re.S):
				match = re.match(r'release\s+(.+?$)', req, flags=re.I|re.S)
				logger.info("Node => {} will be released by admin request".format(match.group(1)))
				decision_maker.release_node(match.group(1))
		decision_maker.update_platform_status()


def processing_stats(stats_socket, logger):

	stats_clientsocket,addr = stats_socket.accept()
	stats_clientsocket.sendall("Give me stats".encode('utf-8'))
	logger.info("Asking for stats from stats_collector")
	b = b''
	containers_stats = stats_clientsocket.recv(1024)
	if containers_stats:
		b += containers_stats
		containers_stats = json.loads(b.decode('utf-8'))
		logger.info("Received stats by stats_collector => {}".format(containers_stats))
	stats_clientsocket.close()

	return containers_stats




def looking_for_minimum_quota(etcd_manager, decision_maker, container_manager, logger):

	apps_count = decision_maker.calculating_app_on_hosts()
	thresholds = literal_eval(etcd_manager.read_key("/platform/orchestrator/thresholds"))
	logger.info("Platform state => {}".format(decision_maker.update_platform_status()))
	flag_failed_nodes = True
	for app in apps_count:
		min_app = "{}_min".format(app)
		app_counter = 0
		while apps_count[app] < int(thresholds[min_app]):
			logger.info("Running container from application {} because of " 
						"minimum quota limitation".format(app))
			### 2019.09.05
			failed_nodes = etcd_manager.get_failed_nodes()
			logger.warning("Detected failed nodes => {}".format(failed_nodes))
			if failed_nodes and flag_failed_nodes:
				return_result = container_manager.run_container_failed_node \
											(host_ip = failed_nodes[0], application = app)
				# logger.info("Returned result => {}".format(return_result))
				if return_result == "SUCCESS":
					logger.info("Failed node {} was detected as live !"
								"Moving the node from failed_nodes to platform_nodes!")
					flag_failed_nodes = False
					etcd_manager.write("/platform/orchestrator/platform_nodes/{}". \
										format(failed_nodes[0]), "1")
					etcd_manager.remove_key("/platform/orchestrator/failed_nodes/{}". \
										format(failed_nodes[0]))

			### 2019.09.05			
			host = decision_maker.making_host_decision(app, decision = 'up')
			container_manager.run_container(host_ip = host, application = app)
			apps_count = decision_maker.calculating_app_on_hosts()
			logger.info("Application count after calculating => {}".format(apps_count))
			app_counter = app_counter + 1
			if app_counter > 2:
				logger.info("Application => {} can't be started! Breaking the loop". \
					format(app))
				break
			time.sleep(1)


def ensure_floating_container(etcd_manager, logger, decision_maker):


	apps = literal_eval(etcd_manager.get_platform_status())
	app_types = etcd_manager.get_application_instances()
	floating_containers = literal_eval(etcd_manager.read_key("/platform/orchestrator/floating_containers"))
	apps_containers = {}

	for app in app_types:
		apps_containers_list = []
		for host in apps.keys():
			if app in apps[host]:
				apps_containers_list = apps_containers_list + list(apps[host][app].keys())
		apps_containers[app] = apps_containers_list
	for app in app_types:
		# app_flag = etcd_manager.get_floating_container("float_{}".format(app))
		app_flag = floating_containers["float_{}".format(app)]
		logger.info("Floating container => {} is => {}".format("float_{}".format(app), app_flag))
		if app_flag:
			if app_flag not in apps_containers[app]:
				floating_containers["float_{}".format(app)] = apps_containers[app][0]
				logger.info("Floating container is down => {}, it will be replace with {}". \
							format(app_flag, apps_containers[app][0]))
				etcd_manager.write("/platform/orchestrator/floating_containers", floating_containers)
		else:
			floating_containers["float_{}".format(app)] = apps_containers[app][0]
			logger.info("Floating container will be chosen for first time => {}". \
				format(apps_containers[app][0]))
			etcd_manager.write("/platform/orchestrator/floating_containers", floating_containers)



def ensure_first_container_is_runned(etcd_manager, decision_maker, container_manager, logger):

	apps = literal_eval(etcd_manager.get_platform_status())
	app_types = etcd_manager.get_application_instances()
	apps_containers = {}

	for app in app_types:
		apps_containers_list = []
		for host in apps.keys():
			if app in apps[host]:
				apps_containers_list = apps_containers_list + list(apps[host][app].keys())
		apps_containers[app] = apps_containers_list
	for app in app_types:
		if "{}_1".format(app) not in apps_containers[app]:
			host = decision_maker.making_host_decision(app, decision = 'up')
			logger.info("First application is not running || Application for increment"
						" => {} on host => {}".format("{}_1".format(app), host))
			container_manager.run_container_name(host_ip = host, \
												application = app, \
												container_hostname = "{}_1".format(app))


def take_master_parameters(etcd_manager, logger, sleep_timer, counter, prev_number):

	my_hostname = socket.gethostname()
	who_is_master = literal_eval(etcd_manager.read_key("platform/orchestrator/who_is_master"))
	curr_num = randint(0, 1000)

	if not who_is_master:
		master_key = {"master": my_hostname, "random_number": curr_num}
		etcd_manager.write(new_key = "platform/orchestrator/who_is_master", \
							value = master_key)
		logger.info("I become master because nobody is at that moment!")
		return True, curr_num, 0
	elif who_is_master["master"] == my_hostname:
		master_key = {"master": my_hostname, "random_number": curr_num}
		etcd_manager.write(new_key = "platform/orchestrator/who_is_master", \
					value = master_key)
		return True, curr_num, 0
	else:
		if counter == 2:
			logger.info("I become master because the other didn't respond for {} iterations". \
						format(counter))
			master_key = {"master": my_hostname, "random_number": curr_num}
			etcd_manager.write(new_key = "platform/orchestrator/who_is_master", \
					value = master_key)
			return True, curr_num, 0
		if prev_number == who_is_master["random_number"]:
			counter = counter + 1
			logger.warning("Failed master orchestrator iteration => {}".format(counter))
			return False, who_is_master["random_number"], counter
		else:
			return False, who_is_master["random_number"], 0


def main():

	sleep_timer = 15
	counter, prev_number = 0, None
	increment_queue_per_app = deque([])
	decrement_queue_per_app = deque([])

	host = 'localhost'

	######## port 11001 => for orchestrator_adm request
	admin_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	admin_socket.setblocking(0)
	admin_port = 11001
	admin_socket.bind((host, admin_port))
	admin_socket.listen(5)
	######## port 11001 => for orchestrator_adm request

	######## port 11000 => listen for stats_collector tool
	decision_maker, etcd_manager,confg_supervisor, container_manager = get_initial_obj_instances()
	dynamic_scaling = eval(etcd_manager. \
			get_etcd_orchestrator_config()['platform']['orchestrator']['dynamic_scaling'])

############## 2018.11.07 microplatform cutting logic for stats
	if dynamic_scaling:
		stats_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		stats_port = 11000
		stats_socket.bind((host, stats_port))
		stats_socket.listen(5)
############## 2018.11.07 microplatform cutting logic for stats


	while True:

		logger = get_obj_instances()
		master_flag, prev_number, counter = take_master_parameters( \
						etcd_manager, logger, sleep_timer, counter, prev_number)
		if master_flag:
			app_for_incremnting = None
			app_for_decrementing = None
			########## 2019.04.02
			decision_maker.update_platform_status()
			########## 2019.04.02
			# dynamic_scaling = bool(etcd_manager. \
			# 				get_etcd_orchestrator_config()['platform']['orchestrator']['dynamic_scaling'])


		######## processing admin requests
			# readable, writable, errored = select.select([admin_socket], [], [])
			# logger.info("After")
			# for s in readable:
			# 	if s is server_socket:
			# 		client_socket, address = server_socket.accept()
			# 		read_list.append(client_socket)
			# 		logger.info("Connection from {}".format(address))
			# 	else:
			# 		data = s.recv(1024)
			# 		if data:
			# 			# s.send(data)
			# 			logger.info("DAta from socket on port 11001 => {}".format(data))
			# 		else:
			# 			s.close()
			# 			read_list.remove(s)


			### ensure floating ip by application
			# ensure_floating_container(etcd_manager, logger, decision_maker)
			### ensure floating ip by application
			######## processing admin_requests
			processing_admin_requests(admin_socket, decision_maker, container_manager, logger)
			######## processing admin_requests
			### Ensure that first container is runned for each app
			ensure_first_container_is_runned(etcd_manager, decision_maker, \
												container_manager, logger)
			### Ensure that first container is runned for each app 

		###Running container if minimum quota is not applied
			looking_for_minimum_quota(etcd_manager, decision_maker, container_manager, logger)
		###Running container if minimum quota is not applied

		### check nodesxml key
			confg_supervisor.check_nodesxml()

		#######processing stats from stats socket

	############## 2018.11.07 microplatform cutting logic for stats
			if dynamic_scaling:
				containers_stats = processing_stats(stats_socket, logger)
			######processing stats from stats socket

				for host in containers_stats:
					for container in containers_stats[host]:
						if re.search(r"registry", container, re.I|re.S):
							break 
						if containers_stats[host][container]["CPU"] > 60 :
							app_for_incremnting = re.sub('\_\d+', "", container)
							if app_for_incremnting not in increment_queue_per_app:
								increment_queue_per_app.append(app_for_incremnting)
							logger.info("CPU {} > 60% => Container {} from application "
										"{} should be runned". \
								format(containers_stats[host][container]["CPU"], \
										container, app_for_incremnting))
							# break
						elif containers_stats[host][container]["CPU"] < 20:
							app_for_decrementing = re.sub('\_\d+', "", container)
							if app_for_decrementing not in decrement_queue_per_app:
								decrement_queue_per_app.append(app_for_decrementing)
							logger.info("CPU {} < 20% => Container {} from application "
										"{} should be stopped". \
								format(containers_stats[host][container]["CPU"], \
										container, app_for_decrementing))
					# if app_for_incremnting or app_for_decrementing:
				# 	# 	break
				logger.info("QUEUE for increment application => {}". \
						format(increment_queue_per_app))
				logger.info("QUEUE for decrement application => {}". \
						format(decrement_queue_per_app))
				if increment_queue_per_app:
					app_for_incremnting = increment_queue_per_app.popleft()
					# print("App for increment => {}".format(app_for_incremnting))
					host = decision_maker.making_host_decision(app_for_incremnting, decision = 'up')
					logger.info("Application for increment => {} on host => {}". \
								format(app_for_incremnting, host))
					container_manager.run_container(host_ip = host, \
													application = app_for_incremnting)
				elif decrement_queue_per_app:
					app_for_decrementing = decrement_queue_per_app.popleft()
					# print("App for decrement => {}".format(app_for_decrementing))
					host = decision_maker.making_host_decision(app_for_decrementing, \
																decision = 'down')
					# logger.info("App for decrement => {} on host {}".format(app_for_decrementing, host))
					# print("Host => {}".format(host))
					if host is not None:
						highest_cpu_stat = 0
						container_name = None
						for container in containers_stats[host].keys():
							if re.search(r'{}'.format(app_for_decrementing), container):
								if containers_stats[host][container]['CPU'] > highest_cpu_stat:
									container_name = container
									highest_cpu_stat = containers_stats[host][container]['CPU']
						# print("Container name => {}".format(container_name))
						if container_name is not None:
							container_manager.stop_container(name = container_name, host_ip = host)
							logger.info("Container name => {} will be stopped on host => {}". \
										format(container_name, host))
					else:
						logger.info("Can't stop container, minimal application number is running!")
						node_for_releasing = decision_maker.check_for_releasing_node()
						if node_for_releasing:
							logger.info("Node {} will be released by the orchestrator api". \
										format(node_for_releasing))
							decision_maker.release_node(host = node_for_releasing)	
						else:
							logger.info("There isn't any node that can be released"
										"from the orchestrator api")

	############## 2018.11.07 microplatform cutting logic for stats
		logger.info("Sleeping {} seconds for the next cycle".format(sleep_timer))
		logger.clear_handler()
		time.sleep(sleep_timer)



main()
