import docker
import json
import re
import os
import sys
import paramiko
from ast import literal_eval
###custom libs
sys.path.append('/opt/containers/ocpytools/lib/')
from logger import Logger
from etcd3_client import EtcdManagement

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
				logger.info("The host ip {} is already in the list!".format(host_ips))
				logger.clear_handler()
		elif isinstance(host_ips, list):
			platform_nodes = list(set(platform_nodes + host_ips))
			###etcd way
			self.etcd_manager.write("/platform/orchestrator/platform_nodes/{}". \
									format(host_ips), "")
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

		logger = Logger(filename = "orchestrator", \
						logger_name = "ContainerManagement run_container_name", \
						dirname="/aux1/ocorchestrator/")
		###24.01.2019 Pruning containers from all hosts with exited status before runinig someone else
		for host_ip_2 in self.etcd_manager.get_platform_nodes():
			###11.06.2019 Exporting exited container in export_dir ref by T099325
			lowlevel_client = self.get_docker_api_lowlevel(host_ip_2)
			exited_containers = lowlevel_client.containers(all=True, \
													filters = {"status": "exited"})
			if exited_containers:
				export_dir = self.etcd_manager.read_key("/platform/orchestrator/export_dir")
				if not export_dir:
					export_dir = "/aux1/"
				for ex_cont in exited_containers:
					data = self.archive(ex_cont['Id'], lowlevel_client)
					with open("{}{}.tar".format(export_dir, ex_cont['Names'][0][1:]), "wb") as file:
						for chunk in data:
							file.write(chunk)
			###11.06.2019 Exporting exited container in export_dir ref by T099325
			client = self.get_docker_api(host_ip_2)
			client.containers.prune(filters=None)
		logger.info("Crashed containers were pruned from host_ips {}". \
					format(self.etcd_manager.get_platform_nodes()))
		###24.01.2019 Pruning containers from all hosts with exited status before runinig someone else

		images = self.etcd_manager.read_key("/platform/orchestrator/images")
		roles_config = self.etcd_manager.get_types_instances()
		lowlevel_docker_api = self.get_docker_api_lowlevel(host_ip)

		###26.11.2019 T105645 create and start container in specific network
		container_networks_dict = literal_eval(roles_config[application][container_hostname])
		networking_config = lowlevel_docker_api.create_networking_config({
			"external_macvlan": lowlevel_docker_api.create_endpoint_config(
				ipv4_address=container_networks_dict["external_macvlan"])
		})
		###26.11.2019 T105645 create and start container in specific network

		#01.07.2019 T100021
		volumes_conf = literal_eval(self.etcd_manager.read_key("/platform/orchestrator/volumes"))
		host_config = None
		volumes = None
		if eval(volumes_conf[application]):
			microplatform_name = re.search('(^.*?)\_', container_hostname)
			if microplatform_name:
					microplatform_name = microplatform_name.group(1)
			volumes=['/aux0']
			volume_bindings = {
						'{}-aux0'.format(container_hostname): {
							'bind': '/aux0',
							'mode': 'rw'
						}
			}
			host_config = lowlevel_docker_api.create_host_config(binds=volume_bindings)
			host_volumes = lowlevel_docker_api.volumes()
			list_volumes = []
			for struct in host_volumes['Volumes']:
				list_volumes.append(struct['Name'])
			if "{}-aux0".format(container_hostname) not in list_volumes:
				logger.info("Volume {}-aux0 is not created on host {} and will be created!" \
							.format(container_hostname, host_ip))
				curr_volume = lowlevel_docker_api.create_volume(name='{}-aux0'. \
																format(container_hostname), \
																driver='local')
				try:
					paramiko_client = paramiko.SSHClient()
					paramiko_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
					paramiko_client.connect(host_ip, timeout=5)
					_, _, _ = paramiko_client.exec_command( \
						'mkdir -p /aux0/docker/{}/{}/aux0/'. \
							format(microplatform_name, container_hostname))
					_, _, _ = paramiko_client.exec_command( \
						'rm -fr /var/lib/docker/volumes/{}-aux0/_data/'.format(container_hostname))
					_, _, _ = paramiko_client.exec_command( \
						'ln -s /aux0/docker/{}/{}/aux0/ /var/lib/docker/volumes/{}-aux0/_data'. \
							format(microplatform_name, container_hostname, container_hostname))
				except:
					logger.error("Can't create symlink => ln -s /aux0/docker/{}/{}/aux0/"
						" /var/lib/docker/volumes/{}-aux0/_data". \
						format(microplatform_name, container_hostname, container_hostname))
					logger.clear_handler()
					return
			#01.07.2019 T100021
		try: 
			runned_container = lowlevel_docker_api.create_container( \
				image = "{}/{}:latest".format(images, application), \
				hostname = container_hostname, \
				name = container_hostname, \
				detach=True, \
				# environment=["ETCD_HOSTNAME={}".format(host_ip)], \
				environment=["ETCD_HOSTNAME={}".format(host_ip), "ETCD_NODES={}".format(os.environ["ETCD_NODES"])], \
				networking_config=networking_config,
				#01.07.2019 T100021 
				host_config=host_config,
				volumes=volumes)
				#01.07.2019 T100021
			### 26.11.2019 T105645
			for network_name in container_networks_dict.keys():
				if network_name is "external_macvlan":
					continue
				lowlevel_docker_api.connect_container_to_network(container = container_hostname, \
									net_id = network_name, \
									ipv4_address = container_networks_dict[network_name])
			### 26.11.2019 T105645
			logger.info("Container {} with this network configuration => {} from image {} will be started!". \
				format(container_hostname, \
						roles_config[application][container_hostname], \
						"{}/{}:latest".format(images, application)))	
			lowlevel_docker_api.start(container = runned_container.get('Id'))
		except:
				logger.error("There is something wrong with the creation and starting "
				 			"of container {} on {} host!".format(container_hostname, host_ip))
		logger.clear_handler()


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
		images = self.etcd_manager.read_key("/platform/orchestrator/images")
		docker_api = self.get_docker_api(host_ip)
		lowlevel_docker_api = self.get_docker_api_lowlevel(host_ip)
		oc_containers = self.get_container_names()
		###24.01.2019 Pruning containers from all hosts with exited status before runinig someone else
		for host_ip_2 in self.etcd_manager.get_platform_nodes():
			###11.06.2019 Exporting exited container in export_dir ref by T099325
			try:
				lowlevel_client = self.get_docker_api_lowlevel(host_ip_2)
				exited_containers = lowlevel_client.containers(all=True, \
													filters = {"status": "exited"})
			except:
				logger.error("Can't retrieve data from {} host !".format(host_ip_2))
				logger.clear_handler()
				return
			if exited_containers:
				export_dir = self.etcd_manager.read_key("/platform/orchestrator/export_dir")
				if not export_dir:
					export_dir = "/aux1/"
				for ex_cont in exited_containers:
					data = self.archive(ex_cont['Id'], lowlevel_client)
					with open("{}{}.tar".format(export_dir, ex_cont['Names'][0][1:]), "wb") as file:
						for chunk in data:
							file.write(chunk)
			###11.06.2019 Exporting exited container in export_dir ref by T099325
			client = self.get_docker_api(host_ip_2)
			client.containers.prune(filters=None)
		logger.info("Crashed containers were pruned from host_ips {}". \
					format(self.etcd_manager.get_platform_nodes()))
		###24.01.2019 Pruning containers from all hosts with exited status before runinig someone else
		logger.info("Aplication {} will be runned on server => {}". \
					format(application, host_ip))
		###### 27.02.2019 Checking if image is available locally
		try:
			docker_api.images.get("{}/{}:latest".format(images, application))
		except(docker.errors.ImageNotFound,docker.errors.APIError):
			logger.info("Image {} was not found on {}".format("{}/{}:latest".format(images, application), \
															host_ip))
			match = re.match(r'(.*)\:(.*?$)', images[application], flags=re.I|re.S)
			if docker_api.images.pull(match.group(1), tag=match.group(2)):
				logger.info("Image {} was pulled successfully locally on {}". \
							format("{}/{}:latest".format(images, application), host_ip))
		###### 27.02.2019 Checking if image is available locally
		flag_free_containers = True
		for role_config in roles_config[application].keys():
			if not role_config in oc_containers:
				flag_free_containers = False
				logger.info("Container {} with this network configuration => {} from image {} will be started!". \
							format(role_config, \
									roles_config[application][role_config], \
									"{}/{}:latest".format(images, application)))
				###26.11.2019 T105645 create and start container in specific network
				container_networks_dict = literal_eval(roles_config[application][role_config])
				networking_config = lowlevel_docker_api.create_networking_config({
					"external_macvlan": lowlevel_docker_api.create_endpoint_config(
						ipv4_address=container_networks_dict["external_macvlan"])
				})
				###26.11.2019 T105645 create and start container in specific network
				#01.07.2019 T100021
				volumes_conf = literal_eval(self.etcd_manager. \
								read_key("/platform/orchestrator/volumes"))
				host_config = None
				volumes = None
				if eval(volumes_conf[application]):
					microplatform_name = re.search('(^.*?)\_', role_config)
					if microplatform_name:
							microplatform_name = microplatform_name.group(1)
					volumes=['/aux0']
					volume_bindings = {
								'{}-aux0'.format(role_config): {
									'bind': '/aux0',
									'mode': 'rw'
								}
					}
					host_config = lowlevel_docker_api.create_host_config(binds=volume_bindings)
					host_volumes = lowlevel_docker_api.volumes()
					list_volumes = []
					for struct in host_volumes['Volumes']:
						list_volumes.append(struct['Name'])
					if "{}-aux0".format(role_config) not in list_volumes:
						logger.info("Volume {}-aux0 is not created on host {} and will be created!" \
									.format(role_config, host_ip))
						curr_volume = lowlevel_docker_api.create_volume(name='{}-aux0'. \
																		format(role_config), \
																		driver='local')
						try:
							paramiko_client = paramiko.SSHClient()
							paramiko_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
							paramiko_client.connect(host_ip, timeout=5)
							_, _, _ = paramiko_client.exec_command( \
							'mkdir -p /aux0/docker/{}/{}/aux0/'. \
								format(microplatform_name, role_config))
							_, _, _ = paramiko_client.exec_command( \
							'rm -fr /var/lib/docker/volumes/{}-aux0/_data/'.format(role_config))
							_, _, _ = paramiko_client.exec_command( \
							'ln -s /aux0/docker/{}/{}/aux0/ /var/lib/docker/volumes/{}-aux0/_data'. \
									format(microplatform_name, role_config, role_config))
						except:
							logger.error("Can't create symlink => ln -s /aux0/docker/{}/{}/aux0/"
							" /var/lib/docker/volumes/{}-aux0/_data". \
							format(microplatform_name, role_config, role_config))
							logger.clear_handler()
							return
				#01.07.2019 T100021
				try:
					runned_container = lowlevel_docker_api.create_container( \
									image = "{}/{}:latest".format(images, application), \
									hostname = role_config, \
									name = role_config, \
									detach=True, \
									# environment=["ETCD_HOSTNAME={}".format(host_ip)], \
									environment=["ETCD_HOSTNAME={}".format(host_ip), "ETCD_NODES={}".format(os.environ["ETCD_NODES"])], \
									networking_config=networking_config,
									#01.07.2019 T100021
									volumes=volumes,
									host_config=host_config)
									#01.07.2019 T100021 
					### 26.11.2019 T105645 create and start container in specific network
					for network_name in container_networks_dict.keys():
						if network_name is "external_macvlan":
							continue
						lowlevel_docker_api.connect_container_to_network(container = role_config, \
											net_id = network_name, \
											ipv4_address = container_networks_dict[network_name])
					### 26.11.2019 T105645 create and start container in specific network
					lowlevel_docker_api.start(container = runned_container.get('Id'))
				except:
					logger.error("There is something wrong with the creation and starting"
					 			" of container {} on {} host!".format(role_config, host_ip))
				#### 27.02.2019 create and start container in specific network
				break
		if flag_free_containers:
			logger.error("No available hostname and ip for {}".format(application))
		logger.clear_handler()

	def run_container_failed_node(self, host_ip, application):

		"""
		Run container
		Args:
			host_ip(str)
		"""
		logger = Logger(filename = "orchestrator", \
						logger_name = "ContainerManagement run_container_failed_node", \
						dirname="/aux1/ocorchestrator/")
		roles_config = self.etcd_manager.get_types_instances()
		images = self.etcd_manager.read_key("/platform/orchestrator/images")
		docker_api = self.get_docker_api(host_ip)
		lowlevel_docker_api = self.get_docker_api_lowlevel(host_ip)
		oc_containers = self.get_container_names()
		###24.01.2019 Pruning containers from all hosts with exited status before runinig someone else
		for host_ip_2 in self.etcd_manager.get_platform_nodes():
			###11.06.2019 Exporting exited container in export_dir ref by T099325
			try:
				lowlevel_client = self.get_docker_api_lowlevel(host_ip_2)
				exited_containers = lowlevel_client.containers(all=True, \
													filters = {"status": "exited"})
			except:
				logger.error("Can't retrieve data from {} host !".format(host_ip_2))
				logger.clear_handler()
				return "ERROR"
			if exited_containers:
				export_dir = self.etcd_manager.read_key("/platform/orchestrator/export_dir")
				if not export_dir:
					export_dir = "/aux1/"
				for ex_cont in exited_containers:
					data = self.archive(ex_cont['Id'], lowlevel_client)
					with open("{}{}.tar".format(export_dir, ex_cont['Names'][0][1:]), "wb") as file:
						for chunk in data:
							file.write(chunk)
			###11.06.2019 Exporting exited container in export_dir ref by T099325
			client = self.get_docker_api(host_ip_2)
			client.containers.prune(filters=None)
		logger.info("Crashed containers were pruned from host_ips {}". \
					format(self.etcd_manager.get_platform_nodes()))
		###24.01.2019 Pruning containers from all hosts with exited status before runinig someone else
		logger.info("Aplication {} will be runned on server => {}". \
					format(application, host_ip))
		###### 27.02.2019 Checking if image is available locally
		try:
			docker_api.images.get("{}/{}:latest".format(images, application))
		except:
		# except(docker.errors.ImageNotFound,docker.errors.APIError):
			logger.info("Image {} was not found on {}".format("{}/{}:latest".format(images, application), \
															host_ip))
			match = re.match(r'(.*)\:(.*?$)', "{}/{}:latest".format(images, application), flags=re.I|re.S)
			try:
				if docker_api.images.pull(match.group(1), tag=match.group(2)):
					logger.info("Image {} was pulled successfully locally on {}". \
								format("{}/{}:latest".format(images, application), host_ip))
			except:
				logger.clear_handler()
				return "ERROR"

		###### 27.02.2019 Checking if image is available locally
		flag_free_containers = True
		for role_config in roles_config[application].keys():
			if not role_config in oc_containers:
				flag_free_containers = False
				logger.info("Container {} with this network configuration => {} from image {} will be started!". \
							format(role_config, \
									roles_config[application][role_config], \
									"{}/{}:latest".format(images, application)))
				###26.11.2019 T105645 create and start container in specific network
				container_networks_dict = literal_eval(roles_config[application][role_config])
				networking_config = lowlevel_docker_api.create_networking_config({
					"external_macvlan": lowlevel_docker_api.create_endpoint_config(
						ipv4_address=container_networks_dict["external_macvlan"])
				})
				###26.11.2019 T105645 create and start container in specific network
				#01.07.2019 T100021
				volumes_conf = literal_eval(self.etcd_manager. \
								read_key("/platform/orchestrator/volumes"))
				host_config = None
				volumes = None
				if eval(volumes_conf[application]):
					microplatform_name = re.search('(^.*?)\_', role_config)
					if microplatform_name:
							microplatform_name = microplatform_name.group(1)
					volumes=['/aux0']
					volume_bindings = {
								'{}-aux0'.format(role_config): {
									'bind': '/aux0',
									'mode': 'rw'
								}
					}
					host_config = lowlevel_docker_api.create_host_config(binds=volume_bindings)
					host_volumes = lowlevel_docker_api.volumes()
					list_volumes = []
					for struct in host_volumes['Volumes']:
						list_volumes.append(struct['Name'])
					if "{}-aux0".format(role_config) not in list_volumes:
						logger.info("Volume {}-aux0 is not created on host {} and will be created!" \
									.format(role_config, host_ip))
						curr_volume = lowlevel_docker_api.create_volume(name='{}-aux0'. \
																		format(role_config), \
																		driver='local')
						try:
							paramiko_client = paramiko.SSHClient()
							paramiko_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
							paramiko_client.connect(host_ip, timeout=5)
							_, _, _ = paramiko_client.exec_command( \
							'mkdir -p /aux0/docker/{}/{}/aux0/'. \
								format(microplatform_name, role_config))
							_, _, _ = paramiko_client.exec_command( \
							'rm -fr /var/lib/docker/volumes/{}-aux0/_data/'.format(role_config))
							_, _, _ = paramiko_client.exec_command( \
							'ln -s /aux0/docker/{}/{}/aux0/ /var/lib/docker/volumes/{}-aux0/_data'. \
									format(microplatform_name, role_config, role_config))
						except:
							logger.error("Can't create symlink => ln -s /aux0/docker/{}/{}/aux0/"
							" /var/lib/docker/volumes/{}-aux0/_data". \
							format(microplatform_name, role_config, role_config))
							logger.clear_handler()
							return
				#01.07.2019 T100021
				try:
					runned_container = lowlevel_docker_api.create_container( \
									image = "{}/{}:latest".format(images, application), \
									hostname = role_config, \
									name = role_config, \
									detach=True, \
									# environment=["ETCD_HOSTNAME={}".format(host_ip)], \
									environment=["ETCD_HOSTNAME={}".format(host_ip), "ETCD_NODES={}".format(os.environ["ETCD_NODES"])], \
									networking_config=networking_config,
									#01.07.2019 T100021
									volumes=volumes,
									host_config=host_config)
									#01.07.2019 T100021
					### 26.11.2019 T105645 create and start container in specific network
					for network_name in container_networks_dict.keys():
						if network_name is "external_macvlan":
							continue
						lowlevel_docker_api.connect_container_to_network(container = role_config, \
											net_id = network_name, \
											ipv4_address = container_networks_dict[network_name])
					### 26.11.2019 T105645 create and start container in specific network
					lowlevel_docker_api.start(container = runned_container.get('Id'))
				except:
					logger.error("There is something wrong with the creation and starting"
					 			" of container {} on {} host!".format(role_config, host_ip))
					logger.clear_handler()
					return "ERROR"
				#### 27.02.2019 create and start container in specific network
				break
		if flag_free_containers:
			logger.error("No available hostname and ip for {}".format(application))
		logger.clear_handler()
		return "SUCCESS"

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
		logger.info("Pruning stopped containers ...")
		client.containers.prune(filters=None)
		logger.info("Exiting from orchestration func because we stop a container")
		logger.clear_handler()


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
		logger.info("Pruning  stopped containers ...")
		logger.clear_handler()
		logger.info("Exiting from orchestration func because we stop a container")
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
		logger = Logger(filename = "orchestrator", \
						logger_name = "ContainerManagement get_container_names", \
						dirname="/aux1/ocorchestrator/")
		container_names = {}
		for server in self.etcd_manager.get_platform_nodes():
			try:
				docker_api = self.get_docker_api(server)
				for container in docker_api.containers.list():
					container_names[container.name] = container
			except:
				logger.error("Can't retrieve data from {} host!".format(server))
				logger.clear_handler()
		return container_names


	def get_container_names_by_host(self, host):
		"""
		Get container names by host
		Args:
			host(str)
		Returns:
			container_names(list)
		"""
		logger = Logger(filename = "orchestrator", \
				logger_name = "ContainerManagement get_container_names_by_host", \
				dirname="/aux1/ocorchestrator/")
		container_names = []
		docker_api = self.get_docker_api(host)
		try:
			for container in docker_api.containers.list():
				container_names.append(container.name)
		except:
			logger.error("Can't retrieve data from {} host!".format(host))
			logger.clear_handler()
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


	@staticmethod
	def archive(container_id, client_api):
			"""Archive the container"""
			try:
				resp = client_api.export(container=container_id)
				for data in resp.stream():
					yield data
			except errors.APIError as ex:
				raise ex
