import docker
import json
import re
import sys
from ast import literal_eval
###custom libs
sys.path.append('/aux0/customer/containers/ocpytools/lib/')
from lib.logger import Logger
from lib.etcd_client import EtcdManagement

def parse_config(json_file):
	"""
	Parse json_file and load it to a dictionary
	Returns:
		js_data(dict)
	"""
	try:
		with open(json_file) as json_data:
			js_data = json.load(json_data)
	except IOError:
		logger = Logger(filename = "orchestrator", logger_name = "parse_config", dirname="/aux1/ocorchestrator/")
		logger.error("File => {} couldn't be opened for read!".format(json_file))
		logger.clear_handler()
		raise("File => {} couldn't be opened for read!".format(json_file))

	return js_data



def update_config(json_file, key, value, state):
	"""
	Update json_file
	"""

	jsonFile = open(json_file, "r") # Open the JSON file for reading
	data = json.load(jsonFile) # Read the JSON into the buffer
	jsonFile.close() # Close the JSON file


	if state is 'add':
		if key is 'available_servers' or key is 'swarm_servers':
			data[key].append(value)
		else:
			data[key] = value
	elif state is 'remove':
		if key is 'available_servers' or key is 'swarm_servers':
			data[key].remove(value)
		else:
			data[key] = value		
	## Save our changes to JSON file

	jsonFile = open(json_file, "w+")
	jsonFile.write(json.dumps(data,  indent=4))
	jsonFile.close()



class ContainerManagement():
	"""
	Class for running and 
	stopping contrainers 
	"""

	def __init__(self):
		"""
		Constructor
		Args:
			available_servers(list)
		"""
		###orchastrator.json way
		# self.swarm_servers = parse_config('orchastrator.json')['swarm_servers']
		# self.roles_config = parse_config('orchastrator.json')['types_instances']
		###orchastrator.json way

		###etcd way
		self.etcd_manager = EtcdManagement()
		self.swarm_servers = self.etcd_manager.get_swarm_servers()
		self.roles_config = self.etcd_manager.get_types_instances()
		###etcd way		
		

	def add_server(self, host_ips):
		"""
		Add server to swarm_servers
		If the server consist in the self.swarm_servers
		it won't be add
		Args:
			host_ips(list or str)
		Returns:
			Append to self.swarm_servers the host_ips
		"""
		logger = Logger(filename = "orchestrator", logger_name = "ContainerManagement add_server", dirname="/aux1/ocorchestrator/")
		if isinstance(host_ips, str):
			if host_ips not in self.swarm_servers:
				self.swarm_servers.append(host_ips)
				###etcd way
				self.etcd_manager.write("/platform/orchestrator/swarm_servers/{}".format(host_ips), "")
				###etcd way		
			else:
				# print("The host ip is already in the list")
				logger.info("The host ip {} is already in the list".format(host_ips))
				logger.clear_handler()
		elif isinstance(host_ips, list):
			self.swarm_servers = list(set(self.swarm_servers + host_ips))
			###etcd way
			self.etcd_manager.write("/platform/orchestrator/swarm_servers/{}".format(host_ips), "")
			###etcd way
		else:
			logger.error("Server should be list or string")
			logger.clear_handler()
			raise TypeError("Server should be list or string")


	def remove_available_server(self, host_ip):
		"""
		Remove server ip from self.swarm_servers
		Args:
			host_ip(str)
		"""
		self.swarm_servers.remove(host_ip)
		###etcd way
		self.etcd_manager.remove_key("/platform/orchestrator/swarm_servers/{}".format(host_ip))
		###etcd way


	def run_container(self, host_ip, application):
		"""
		Run container
		Args:
			host_ip(str)
		"""
		images = literal_eval(self.etcd_manager.read_key("/platform/orchestrator/images"))
		logger = Logger(filename = "orchestrator", logger_name = "ContainerManagement run_container", dirname="/aux1/ocorchestrator/")
		docker_api = self.get_docker_api(host_ip)
		oc_containers = self.get_container_names()
		logger.info("Aplication {} will be runned on server => {}".format(application, host_ip))
		if not "{}_1".format(application) in oc_containers:
			logger.info("First application container should be runned=> {} with this ip => {} from image {}" \
						.format("{}_1".format(application), \
								self.roles_config[application]["{}_1".format(application)], \
								images[application]))
			runned_container = docker_api.containers. \
						create(image = "{}". \
						format(images[application]), \
						hostname = "{}_1".format(application), name = "{}_1".format(application), \
						privileged = True, detach=True)
			docker_api.networks.get(self.etcd_manager.get_network_name()). \
				connect(runned_container, \
				ipv4_address=self.roles_config[application]["{}_1".format(application)])
			runned_container.start()
		else:
			for role_config in self.roles_config[application].keys():
				if not role_config in oc_containers:
					logger.info("This name is not runned as container => {} with this ip => {} from image {}" \
						.format(role_config, self.roles_config[application][role_config], images[application]))
					### Two ways:: 1st => run the contaienr and then connect it
					### to the network 
					### 2nd => create the container, then connect it to the 
					### network and then start it

					# runned_container = docker_api.containers. \
					# 			run(image = "g2.pslab.opencode.com:5000/{}1:v2". \
					# 			format(application), \
					# 			hostname = role_config, name = role_config, \
					# 			privileged = True, detach=True)
					runned_container = docker_api.containers. \
								create(image = "{}". \
								format(images[application]), \
								hostname = role_config, name = role_config, \
								privileged = True, detach=True)
					docker_api.networks.get(self.etcd_manager.get_network_name()). \
						connect(runned_container, \
						ipv4_address=self.roles_config[application][role_config])
					runned_container.start()
					break
		logger.clear_handler()

	def stop_container(self, name, host_ip):
		"""
		Stopping container
		"""
		logger = Logger(filename = "orchestrator", logger_name = "ContainerManagement stop_container", dirname="/aux1/ocorchestrator/")
		client = self.get_docker_api(host_ip)
		container_names = self.get_container_names()
		container_names[name].stop(timeout = 30)
		logger.info("Exiting from orchestration func because we stop a container")
		logger.info("=== Pruned  stopped containers ===")
		logger.clear_handler()
		client.containers.prune(filters=None)



	@staticmethod
	def get_docker_api(host_ip):
		"""
		Get docker api client
		Args:
			host_ip(str)
		"""
		return docker.DockerClient(base_url='tcp://{}:2375'.format(host_ip))

	def get_container_names(self):
		"""
		Get container names
		Args:
		"""
		container_names = {}
		for server in self.swarm_servers:
			docker_api = self.get_docker_api(server)
			for container in docker_api.containers.list():
				container_names[container.name] = container

		return container_names


	def get_container_names_by_host(self, host):
		"""
		Get container names by host
		Args:
			host(str)
		Returns:
			container_names(list)
		"""
		container_names = []
		docker_api = self.get_docker_api(host)
		for container in docker_api.containers.list():
			container_names.append(container.name)

		return container_names		
