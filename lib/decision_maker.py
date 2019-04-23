import docker
import json
import re
import sys
from collections import Counter

#custom lib
sys.path.append('/aux0/customer/containers/orchestrator/')
from lib.containering import parse_config
from lib.containering import update_config
#from lib.swarming import SwarmManagment
from lib.containering import ContainerManagement
sys.path.append('/aux0/customer/containers/ocpytools/lib/')
from logger import Logger
from etcd_client import EtcdManagement


class DecisionMaker():

	def __init__(self):
		"""
		Constructor
		Args:
			available_nodes(list)
		"""
		###etcd way
		self.etcd_manager = EtcdManagement()
		###etcd way


	@staticmethod
	def get_docker_api(host_ip):
		"""
		Get docker api client
		Args:
			host_ip(str)
		"""
		return docker.DockerClient(base_url='tcp://{}:2375'.format(host_ip))


	@staticmethod
	def list_containers_by_host(host_ip):

		docker_api = DecisionMaker.get_docker_api(host_ip)
		cont_names = []
		for container in docker_api.containers.list():
			app_name_search = re.search('(.*?)\_\d+', container.name)
			if app_name_search:
				app_name = app_name_search.group(1)
				cont_names.append(app_name)
		return cont_names


	def update_platform_status(self):

		names_by_hosts = {}
		###etcd way
		orchestrator_conf = self.etcd_manager.get_etcd_orchestrator_config()['platform']['orchestrator']
		for host in orchestrator_conf['platform_nodes']:
		###etcd way
			names_by_hosts[host] = {}
			docker_api = DecisionMaker.get_docker_api(host)
			for container in docker_api.containers.list():
				app_name_search = re.search('(.*?)\_\d+', container.name)
				if app_name_search:
					app_name = app_name_search.group(1)
					if app_name not in names_by_hosts[host]:
						names_by_hosts[host][app_name] = {}
					names_by_hosts[host][app_name].update( \
							{container.name: orchestrator_conf['types_instances'][app_name][container.name]})
		self.etcd_manager.write("/platform/orchestrator/platform_status", str(names_by_hosts))
		return names_by_hosts


	def take_containers_by_hosts(self):

		names_by_hosts = {}
		###orchastrator.json way
		# for host in parse_config('orchastrator.json')['platform_nodes']:
		###orchastrator.json way
		###etcd way
		orchestrator_conf = self.etcd_manager.get_etcd_orchestrator_config()['platform']['orchestrator']
		for host in orchestrator_conf['platform_nodes']:
		###etcd way
			names_by_hosts[host] = dict(Counter(self.list_containers_by_host(host)))
		return names_by_hosts


	def counting_app_by_host(self, application):
		"""
		Counting application by hosts
		Args:
			application(str)
		Returns:
			container_count(str)
		"""
		apps_by_hosts = self.take_containers_by_hosts()
		container_count = {}
		for host in apps_by_hosts.keys():
			if application not in apps_by_hosts[host]:
				# return host
				container_count[host] = {application: 0}
			else:
				container_count[host] = {application: apps_by_hosts[host][application]}

		return container_count


	def calculating_app_on_hosts(self):
		"""
		Args:
			None
		Returns:
			app_counts(dict)
		"""
		
		app_counts = {}
		for app in self.etcd_manager.get_application_instances():
			app_count = self.counting_app_by_host(app)
			number = 0
			for host in app_count:
				number += app_count[host][app]
			app_counts[app] = number

		return app_counts


	def check_for_releasing_node(self):
		"""
		Check for finding a node that can 
		be released if it is not necessary
		Args:
			None
		Returns:
			host_for_release(str) or None		
		"""
		orchestrator_conf = self.etcd_manager.get_etcd_orchestrator_config()['platform']['orchestrator']
		apps_count = self.calculating_app_on_hosts()
		curr_nodes_number = len(orchestrator_conf['platform_nodes'])
		validation_flag = True
		for app in apps_count.keys():
			app_count = apps_count[app]
			app_per_node = '{}_per_node'.format(app)
			if curr_nodes_number*orchestrator_conf[app_per_node] - app_count >= \
				orchestrator_conf[app_per_node]:
				pass
			else:
				validation_flag = False
		if validation_flag:
			# return "Should be released some node"
			all_app_count = 1000
			names_by_hosts = self.take_containers_by_hosts()
			for host in names_by_hosts.keys():
				if host == orchestrator_conf['master']:
					continue
				curr_count = 0
				for app in names_by_hosts[host].keys():
					curr_count += names_by_hosts[host][app]
				if curr_count < all_app_count:
					host_for_release = host
					all_app_count = curr_count
			return host_for_release
		else:
			return None



	def making_host_decision(self, application, decision, release_node=False):
		"""
		Make decision on which host to run container
		Args:
			application(str)
			decision(str)
		Returns:
			host(str)
		"""
		orchestrator_conf = self.etcd_manager.get_etcd_orchestrator_config()['platform']['orchestrator']
		# swarm_manager = SwarmManagment()
		app_per_node = "{}_per_node".format(application)
		app_by_hosts = self.counting_app_by_host(application)
		if release_node:
			del(app_by_hosts[release_node])
		host_number = len(app_by_hosts.keys())
		if decision is 'up':
			application_number = 0
			for host in app_by_hosts.keys():
				if app_by_hosts[host][application] == 0:
					return host
				else:
					application_number += app_by_hosts[host][application]
			average_app_number = application_number/host_number
			logger_2 = Logger(filename = "orchestrator", logger_name = "DecisionMaker making_host_decision", dirname="/aux1/ocorchestrator/")
			logger_2.info("Aplication {} ||| Average => {}\tApp_per_node => {}". \
				format(application, average_app_number, orchestrator_conf[app_per_node]))
			logger_2.clear_handler()
			###logic for adding node to the swarm
			if average_app_number >= float(orchestrator_conf[app_per_node]):
				if len(list(orchestrator_conf['available_nodes'].keys())) != 0:
					available_nodes = list(orchestrator_conf['available_nodes'].keys())
					new_node = available_nodes[0]
					self.etcd_manager.remove_key("/platform/orchestrator/available_nodes/{}".format(new_node))
					self.etcd_manager.write("/platform/orchestrator/platform_nodes/{}".format(new_node), '1')
					return new_node
				else:
					logger = Logger(filename = "orchestrator", \
									logger_name = "DecisionMaker making_host_decision", \
									dirname="/aux1/ocorchestrator/")
					logger.critical("There are not any available servers should" \
									"look at host stat to run on the lowest" \
									"loaded host a container")
					logger.clear_handler()
			###logic for adding node to the swarm			
			for host in app_by_hosts.keys():
				if app_by_hosts[host][application] < average_app_number and \
					app_by_hosts[host][application] < float(orchestrator_conf[app_per_node]): #parse_config('orchastrator.json')[app_per_node]:
					return host
			for host in app_by_hosts.keys():
				return host
		elif decision is 'down':
			application_number = 0
			for host in app_by_hosts.keys():
					application_number += app_by_hosts[host][application]

			min_app = "{}_min".format(application)
			logger = Logger(filename = "orchestrator", \
							logger_name = "DecisionMaker making_host_decision", \
							dirname="/aux1/ocorchestrator/")
			logger.warning("Application => {} ||| min_apps on platform=> {}\tcurrent app_num {}". \
				format(application, orchestrator_conf[min_app], application_number))
			logger.clear_handler()
			if application_number == float(orchestrator_conf[min_app]):
				return None

			average_app_number = application_number/host_number			
			for host in app_by_hosts.keys():
				if app_by_hosts[host][application] > average_app_number and \
					app_by_hosts[host][application] < orchestrator_conf[app_per_node]: #parse_config('orchastrator.json')[app_per_node]:
					return host
			for host in app_by_hosts.keys():
				return host
		


	def release_node(self, host):
		"""
		Stop all containers from the passed node,
		move them to the other hosts in self.platform_nodes,
		and move the host to available.servers
		Args:
			host(str)
		Returns:
			None
		"""
		container_manager = ContainerManagement()
		apps_by_host = container_manager.get_container_names_by_host(host)
		for app in apps_by_host:
			app_name_search = re.search('(.*?)\_\d+', app)
			if app_name_search:
				app_name = app_name_search.group(1)		
			container_manager.stop_container(name=app, host_ip=host)
			new_host = self.making_host_decision(application=app_name, decision='up', release_node=host)
			container_manager.run_container_name(host_ip=new_host, \
												application=app_name, \
												container_hostname=app)
		#####
		self.etcd_manager.remove_key("/platform/orchestrator/platform_nodes/{}".format(host))
		self.etcd_manager.write("/platform/orchestrator/available_nodes/{}".format(host), '1')
		#####
		logger = Logger(filename = "orchestrator", logger_name = "DecisionMaker release_node", dirname="/aux1/ocorchestrator/")
		logger.warning("Releasing node {} was successfull !".format(host))
		logger.clear_handler()		
