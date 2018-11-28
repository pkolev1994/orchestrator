import docker
import paramiko
import re
import json
import scp
import socket

#custom libs
from lib.nodeconnection import Node
from lib.containering import parse_config


class StatsCollector():
	"""
	class StatsCollector
	"""

	def __init__(self):
		"""
		Constructor
		"""
		# self.__user = kwargs.get('username')
		# self.__password = kwargs.get('password')
		self.__user = parse_config("orchastrator.json")["user"]
		self.__password = parse_config("orchastrator.json")["password"]
		self.__docker_client_api = docker.from_env()
		self.ssh_client = paramiko.client.SSHClient()
		self.host_ip = socket.gethostbyname(socket.gethostname())


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



	def get_host_containers_statistics(self):
		"""
		Get the container statsitics of the current host
		Args:
			None
		Rteurns:
			oc_containers(dict)
		"""
		oc_containers = {}
		oc_containers[self.host_ip] = {}
		for container in self.__docker_client_api.containers.list():
			stats = container.stats(decode = False, stream=False)
			container_id_search = re.search('<Container:\s*([^>]+)>', str(container))
			container_id = container_id_search.group(1)
			taken_stats = {}
			taken_stats[container.name]= {
											"container_id": container_id, 
											"stats": stats
										 }
			oc_containers[self.host_ip].update(taken_stats)
		return oc_containers

	def exec_script(self, host):
		"""
		Coppy and execute take_stats.py script to host in the swarm
		Args:
			host(str)
		Returns:
			eval(stdout) => dict
		"""
		self.ssh_client.load_system_host_keys()
		self.ssh_client.connect(host, username='root', password='0penc0de')
		self.ssh_client.connect(host)
		scp_client = scp.SCPClient(self.ssh_client.get_transport())
		scp_client.put('exec_script/take_stats.py', '/root/python/')
		_, stdout, _ = self.ssh_client.exec_command('python /root/python/take_stats.py')
		stdout = '\n'.join(map(lambda x: x.rstrip(), stdout.readlines()))

		return eval(stdout)



	def collect_stats(self):
		"""
		Collects all containers stattistics of all nodes in the swarm
		Args:
			None
		Returns:
			all_hosts_containers(dict)
		"""

		# all_hosts_containers ={}
		# list_without_manager_host = self.list_nodes_ips()
		# list_without_manager_host.remove(self.host_ip)

		# for host in list_without_manager_host:
		# 	all_hosts_containers.update(self.exec_script(host))

		# all_hosts_containers.update(self.get_host_containers_statistics())

		# return all_hosts_containers

		all_hosts_containers ={}
		list_without_manager_host = self.list_nodes_ips()
		list_without_manager_host.remove(self.host_ip)

		nodes = []
		for host in list_without_manager_host:
			nodes.append(Node(address=host, \
								user=self.__user, \
								password=self.__password))

		for node in nodes:
			node.join()
			all_hosts_containers.update(node.output)

		all_hosts_containers.update(self.get_host_containers_statistics())

		return all_hosts_containers




	def collect_stats_by_host(self, host):
		"""
		Collects  containers stattistics of the host which is passed
		Args:
			host(str)
		Returns:
			self.exec_script(host) => dict
			or
			self.get_host_containers_statistics() => dict
		"""
		if host != self.host_ip:
			return self.exec_script(host)
		else:
			return self.get_host_containers_statistics()


	# def list_manager_host_containers_stats(self):

	#   host_containers = {}
	#   for host in self.list_nodes_ips():
	#       print("Host => {}".format(host))
	#       self.ssh_client.load_system_host_keys()
	#       self.ssh_client.connect(host, username='root', password='0penc0de')
	#       self.ssh_client.connect(host)
	#       stdin, stdout, stderr = self.ssh_client.exec_command('docker ps')
	#       stdout = '\n'.join(map(lambda x: x.rstrip(), stdout.readlines()))
	#       host_container_ids = re.findall(r'([\w|\d]{12})\s*[^\s*]+\s*', stdout)
	#       print("STDOUT ===> {}".format(host_container_ids))
	#       for i in host_container_ids:
	#           # if re.search(r'850',i):
	#           print("Yess")
	#               # print(i.stats(decode = False, stream = False))
	#           # print("Contaienr id => {}".format(self.__docker_client_api.containers.get(i).stats(decode = False, stream = False)))
	#           stdin, stdout, stderr = self.ssh_client.exec_command('curl --unix-socket /var/run/docker.sock http:/v1.37/containers/{}/json'.format(i))
	#           stdout = '\n'.join(map(lambda x: x.rstrip(), stdout.readlines()))
	#           stdout = stdout.replace("'", "\"")
	#           loaded_json = json.loads(stdout)
	#           # print("STDOUT stats ===> {}".format(json.dumps(loaded_json, indent = 4)))
