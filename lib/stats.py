import docker
import paramiko
import re
import json
# import scp
import socket

#custom libs

class StatsCollector():
	"""
	class StatsCollector
	"""

	def __init__(self):
		"""
		Constructor
		Args:
			username(str)
			password(str)
		"""
		self.__docker_client_api = docker.from_env()


	def list_nodes_ips(self):
		"""
		Lists all node ips in the swarm
		Args:
			None
		Returns:
			ip_nodes(list)
		"""
		ip_nodes = []
		for node in self.__docker_client_api.nodes.list():
			ip_nodes.append(node.attrs['Status']['Addr'])
		return ip_nodes


	def list_nodes_hostnames(self):
		"""
		Lists all node hostnames in the swarm
		Args:
			None
		Returns:
			hostname_nodes(list)
		"""
		hostname_nodes = []
		for node in self.__docker_client_api.nodes.list():
			hostname_nodes.append(node.attrs['Description']['Hostname'])
		return hostname_nodes


	@staticmethod
	def get_docker_api(host_ip):
		"""
		Get docker api client
		Args:
			host_ip(str)
		"""
		return docker.DockerClient(base_url='tcp://{}:2375'.format(host_ip))



	def collect_stats(self):
		"""
		Collects all containers stattistics of all nodes in the swarm
		Args:
			None
		Returns:
			all_hosts_containers(dict)
		"""
		oc_containers = {}
		for host in self.list_nodes_ips():
			oc_containers[host] = {}
			docker_client_api = self.get_docker_api(host)
			for container in docker_client_api.containers.list():
				stats = container.stats(decode = False, stream=False)
				container_id_search = re.search('<Container:\s*([^>]+)>', str(container))
				container_id = container_id_search.group(1)
				taken_stats = {}
				taken_stats[container.name]= {
												"container_id": container_id, 
												"stats": stats
											 }
				oc_containers[host].update(taken_stats)


		return oc_containers


	def take_processes(self):
		"""
		Show running processes in the containers
		Args:
			None
		Returns:
			container_processes(dict)
		"""

		container_processes = {}
		for host in self.list_nodes_ips():
			container_processes[host] = {}
			docker_client_api = self.get_docker_api(host)
			for container in docker_client_api.containers.list():
				processes = container.top()
				taken_processes = {}
				taken_processes[container.name] = processes
				container_processes[host].update(taken_processes)

		return container_processes



	def parsed_stats(self):

		parsed_stats = {}
		stats = self.collect_stats()
		for host in stats.keys():
			parsed_stats[host] = {}
			for container in stats[host].keys():
				cpu_percentage = round(self.calculate_cpu_percent(stats[host][container]['stats']), 2)
				memory_percentage = round(self.calculate_mem_percent(stats[host][container]['stats']), 2)
				taken_stats = {}
				taken_stats[container] = {
												"CPU": cpu_percentage,
												"MEM": memory_percentage
												}
				parsed_stats[host].update(taken_stats)


		return parsed_stats


	def calculate_mem_percent(self, d):
		"""
		Calculate cpu usage
		Args:
			d(dict)
		Returns:
			memory_percentage(float)
		"""		
		memory_max = d['memory_stats']['limit']
		memory_curr = d['memory_stats']['usage']
		memory_percentage = memory_curr*100 / memory_max

		return memory_percentage


	def calculate_cpu_percent(self, d):
		"""
		Calculate cpu usage
		Args:
			d(dict)
		Returns:
			cpu_percentage(float)
		"""
		cpu_count = len(d["cpu_stats"]["cpu_usage"]["percpu_usage"])
		cpu_percentage = 0.0
		cpu_delta = float(d["cpu_stats"]["cpu_usage"]["total_usage"]) - \
					float(d["precpu_stats"]["cpu_usage"]["total_usage"])
		system_delta = float(d["cpu_stats"]["system_cpu_usage"]) - \
					   float(d["precpu_stats"]["system_cpu_usage"])
		if system_delta > 0.0:
			cpu_percentage = cpu_delta / system_delta * 100.0 * cpu_count

		return cpu_percentage


	def show_stats(self):
		"""
		Dumps in pretty format dictionary 
		returned by parsed_stats function
		Args:
			None
		Returns:
			None
		"""
		return json.dumps(self.parsed_stats(), indent = 4)


	def show_processes(self):
		"""
		Dumps in pretty format dictionary 
		returned by take_processes function
		Args:
			None
		Returns:
			None
		"""
		return json.dumps(self.take_processes(), indent = 4)