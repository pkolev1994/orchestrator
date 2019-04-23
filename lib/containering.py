import docker
import json
import re
import sys
from ast import literal_eval
###custom libs
sys.path.append('/aux0/customer/containers/ocpytools/lib/')
from logger import Logger
from etcd_client import EtcdManagement

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
		logger = Logger(filename = "orchestrator", \
						logger_name = "parse_config", \
						dirname="/aux1/ocorchestrator/")
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
		if key is 'available_nodes' or key is 'platform_nodes':
			data[key].append(value)
		else:
			data[key] = value
	elif state is 'remove':
		if key is 'available_nodes' or key is 'platform_nodes':
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
			None
		"""
		###etcd way
		self.etcd_manager = EtcdManagement()
		###etcd way		
		

	def add_server(self, host_ips):
		"""
		Add server to platform_nodes
		If the server consist in the self.etcd_manager.get_platform_nodes()
		it won't be add
		Args:
			host_ips(list or str)
		Returns:
			Append to self.etcd_manager.get_platform_nodes() the host_ips
		"""
		logger = Logger(filename = "orchestrator", \
						logger_name = "ContainerManagement add_server", \
						dirname="/aux1/ocorchestrator/")

		platform_nodes = self.etcd_manager.get_platform_nodes()
		if isinstance(host_ips, str):
			if host_ips not in platform_nodes:
				platform_nodes.append(host_ips)
				###etcd way
				self.etcd_manager.write("/platform/orchestrator/platform_nodes/{}". \
										format(host_ips), "")
				###etcd way		
			else:
				# print("The host ip is already in the list")
				logger.info("The host ip {} is already in the list".format(host_ips))
				logger.clear_handler()
		elif isinstance(host_ips, list):
			platform_nodes = list(set(platform_nodes + host_ips))
			###etcd way
			self.etcd_manager.write("/platform/orchestrator/platform_nodes/{}".format(host_ips), "")
			###etcd way
		else:
			logger.error("Server should be list or string")
			logger.clear_handler()
			raise TypeError("Server should be list or string")


	def remove_platform_node(self, host_ip):
		"""
		Remove server ip from self.etcd_manager.get_platform_nodes()
		Args:
			host_ip(str)
		"""
		self.etcd_manager.get_platform_nodes().remove(host_ip)
		###etcd way
		self.etcd_manager.remove_key("/platform/orchestrator/platform_nodes/{}".format(host_ip))
		###etcd way


	def run_container_name(self, host_ip, application, container_hostname):

		images = literal_eval(self.etcd_manager.read_key("/platform/orchestrator/images"))
		roles_config = self.etcd_manager.get_types_instances()
		lowlevel_docker_api = self.get_docker_api_lowlevel(host_ip)
		networking_config = lowlevel_docker_api.create_networking_config({
			self.etcd_manager.get_network_name(): lowlevel_docker_api.create_endpoint_config(
				ipv4_address=roles_config[application][container_hostname])
		})
		runned_container = lowlevel_docker_api.create_container( \
					image = images[application], \
					hostname = container_hostname, \
					name = container_hostname, \
					detach=True, \
					environment=["ETCD_HOSTNAME={}".format(host_ip)], \
					networking_config=networking_config)
		lowlevel_docker_api.start(container = runned_container.get('Id'))


	def run_container(self, host_ip, application):
		"""
		Run container
		Args:
			host_ip(str)
		"""
		logger = Logger(filename = "orchestrator", \
						logger_name = "ContainerManagement run_container", \
						dirname="/aux1/ocorchestrator/")
		roles_config = self.etcd_manager.get_types_instances()
		images = literal_eval(self.etcd_manager.read_key("/platform/orchestrator/images"))
		docker_api = self.get_docker_api(host_ip)
		lowlevel_docker_api = self.get_docker_api_lowlevel(host_ip)
		oc_containers = self.get_container_names()
		###24.01.2019 Pruning containers from all hosts with exited status before runinig someone else
		for host_ip_2 in self.etcd_manager.get_platform_nodes():
			client = self.get_docker_api(host_ip_2)
			client.containers.prune(filters=None)
		logger.info("Crashed containers were pruned from host_ips {}".format(self.etcd_manager.get_platform_nodes()))
		###24.01.2019 Pruning containers from all hosts with exited status before runinig someone else
		logger.info("Aplication {} will be runned on server => {}".format(application, host_ip))
		###### 27.02.2019 Checking if image is available locally
		try:
			docker_api.images.get(images[application])
		except(docker.errors.ImageNotFound,docker.errors.APIError):
			logger.info("Image {} was not found on {}".format(images[application], \
															host_ip))
			match = re.match(r'(.*)\:(.*?$)', images[application], flags=re.I|re.S)
			if docker_api.images.pull(match.group(1), tag=match.group(2)):
				logger.info("Image {} was pulled successfully locally on {}". \
							format(images[application], host_ip))
		###### 27.02.2019 Checking if image is available locally
		for role_config in roles_config[application].keys():
			if not role_config in oc_containers:
				logger.info("""This name is not runned as container => 
							{} with this ip => {} from image {}""" \
							.format(role_config, \
									roles_config[application][role_config], \
									images[application]))
				#### 27.02.2019 create and start container in specific network
				networking_config = lowlevel_docker_api.create_networking_config({
					self.etcd_manager.get_network_name(): \
					lowlevel_docker_api.create_endpoint_config(
						ipv4_address=roles_config[application][role_config])
				})
				runned_container = lowlevel_docker_api.create_container( \
								image = images[application], \
								hostname = role_config, \
								name = role_config, \
								detach=True, \
								environment=["ETCD_HOSTNAME={}".format(host_ip)], \
								networking_config=networking_config)
				lowlevel_docker_api.start(container = runned_container.get('Id'))
				#### 27.02.2019 create and start container in specific network
				break
		logger.clear_handler()

	def stop_container_2(self, name):
		"""
		Stopping container
		"""
		logger = Logger(filename = "orchestrator", \
						logger_name = "ContainerManagement stop_container_2", \
						dirname="/aux1/ocorchestrator/")
		host_ip = self.get_host_by_container(name)
		client = self.get_docker_api(host_ip)
		container_names = self.get_container_names()
		container_names[name].stop(timeout = 30)
		logger.info("Exiting from orchestration func because we stop a container")
		logger.info("=== Pruned  stopped containers ===")
		logger.clear_handler()
		client.containers.prune(filters=None)


	def stop_container(self, name, host_ip):
		"""
		Stopping container
		"""
		logger = Logger(filename = "orchestrator", \
						logger_name = "ContainerManagement stop_container", \
						dirname="/aux1/ocorchestrator/")
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


	@staticmethod
	def get_docker_api_lowlevel(host_ip):
		"""
		Get docker api client
		Args:
				host_ip(str)
		"""
		return docker.APIClient(base_url='tcp://{}:2375'.format(host_ip))


	def get_container_names(self):
		"""
		Get container names
		Args:
		"""
		container_names = {}
		for server in self.etcd_manager.get_platform_nodes():
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


	def get_host_by_container(self, container_name):
		###orchastrator.json way
		# for host in parse_config('orchastrator.json')['platform_nodes']:
		###orchastrator.json way
		###etcd way
		orchestrator_conf = self.etcd_manager. \
							get_etcd_orchestrator_config()['platform']['orchestrator']
		for host in orchestrator_conf['platform_nodes']:
		###etcd way
			docker_api = self.get_docker_api(host)
			for container in docker_api.containers.list():
				if container.name == container_name:
					return host