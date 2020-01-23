import docker


#custom libs import
sys.path.append('/opt/containers/orchestrator/')
from lib.swarming import SwarmManagment
from lib.stats import StatsCollector
from lib.containering import parse_config


class PlatformOrchastration():
	"""
	Platform_Orchastration object
	"""
	
	def __init__(self):
		"""
		Constructor of Platform_Orchastration
		"""

		# self.available_servers = kwargs.get('available_servers', [])
		# self.swarm_servers = kwargs.get('swarm_servers', [])
		# self.master_nodes = kwargs.get('master_nodes', [])
		# self.__master = kwargs.get('master', None)
		# self.__token = kwargs.get('token')
		# self.__user = kwargs.get('username')
		# self.__password = kwargs.get('password')
		# self.__docker_client_api = docker.from_env()

		# self.stats_colector = StatsCollector()

		# self.swarm_manager = SwarmManagment(available_servers=self.available_servers,
		# 									swarm_servers=self.swarm_servers,
		# 									master_nodes=self.master_nodes,
		# 									master=self.__master,
		# 									token=self.__token,
		# 									user=self.__user,
		# 									password=self.__password
		# 									)


		self.available_servers = parse_config("orchastrator.json")["available_servers"]
		self.swarm_servers = parse_config("orchastrator.json")["swarm_servers"]
		self.user = parse_config("orchastrator.json")["user"]
		self.password = parse_config("orchastrator.json")["password"]
		self.master_nodes = parse_config("orchastrator.json")["master_nodes"]
		self.__master = parse_config("orchastrator.json")["master"]
		self.__token = parse_config("orchastrator.json")["token"]
		self.__docker_client_api = docker.from_env()
		self.stats_colector = StatsCollector()

		self.swarm_manager = SwarmManagment()

		
	def take_containers_stats(self):
		"""
		Take the container statistics
		from the swarm nodes
		Args:
			None
		Returns:
			self.stats_colector.collect_stats()(dict)
		"""
		return self.stats_colector.collect_stats()


	def take_host_container_stats(self, host):
		"""
		Take the container statistics
		from the swarm nodes
		Args:
			None
		Returns:
			self.stats_colector.collect_stats_by_host() => dict
		"""
		return self.stats_collector.collect_stats_by_host(host)


	def list_nodes_hostnames(self):
		"""
		Lists all node hostnames in the swarm
		Args:
			None
		Returns:
			self.stats_colector.list_nodes_hostnames() => list
		"""
		return self.stats_colector.list_nodes_hostnames()


	def list_nodes_ips(self):
		"""
		Lists all node ips in the swarm
		Args:
			None
		Returns:
			self.stats_colector.list_nodes_ips() => list
		"""
		return self.stats_colector.list_nodes_ips()


	def add_server(self, host_ips):
		"""
		Add server to available_servers
		If the server consist in the self.available_servers
	 	it won't be add
		Args:
			host_ips(list or str)
		Returns:
			Append to swarm_manager.available_servers the host_ips
		"""		
		self.swarm_manager.add_server(host_ips)


	def add_swarm_server(self, host_ip):
		"""
		Add server to swarm_servers
		If the server consist in the list it won't be add
		Args:
			host_ips(str)
		Returns:
			Append to swarm_manager.swarm_servers the host_ip
		"""
		self.swarm_manager.add_swarm_server(host_ip)


	def list_available_servers(self):
		"""
		List the available servers remain
		Returns:
			self.swarm_manager.available_servers(list)
		"""		
		return self.swarm_manager.list_available_servers()


	def list_swarm_servers(self):
		"""
		List the servers in the swarm
		Returns:
			self.swarm_manager.swarm_servers(list)
		"""
		return self.swarm_manager.swarm_servers


	def remove_available_server(self, host_ip):
		"""
		Remove server ip from self.swarm_manager.available_servers
		Args:
			host_ip(str)
		"""
		self.swarm_manager.remove_available_server(host_ip)



	def remove_swarm_server(self, host_ip):
		"""
		Remove server ip from self.swarm_manager.swarm_servers
		Args:
			host_ip(str)
		"""
		self.swarm_manager.remove_swarm_server(host_ip)


	def join_server_swarm(self, host_ip):
		"""
		Join server to the swarm_manager
		Args:
			host_ip(str)
		"""
		self.swarm_manager.join_server_swarm(host_ip)


	def leave_server_swarm(self, host_ip):
		"""
		Leave server from the swarm_manager
		Args:
			host_ip(str)
		"""
		self.swarm_manager.leave_server_swarm(host_ip)


	def add_master_node(self, host_ip):
		"""
		Add server ip to swarm_manager.master_nodes
		Args:
			host_ip(str)
		"""
		self.swarm_manager.add_master_node(host_ip)


	def remove_master_node(self, host_ip):
		"""
		Remove server ip to swarm_manager.master_nodes
		Args:
			host_ip(str)
		"""
		self.swarm_manager.remove_master_node(host_ip)


	def promote_to_manager(self, host_ip):
		"""
		Promote the server to manager in the swarm_manager
		Args:
			host_ip(str)
		"""
		self.swarm_manager.promote_to_manager(host_ip)


	def demote_manager(self, host_ip):
		"""
		Demote the server from manager in the swarm_manager
		Args:
			host_ip(str)
		"""
		self.swarm_manager.demote_manager(host_ip)


	def change_master(self, host_ip):
		"""
		Change the swarm_manager.__master
		Args:
			host_ip(str)
		"""
		self.swarm_manager.change_master(host_ip)


	def change_token(self, token):
		"""
		Change the swarm_manager.__token
		Args:
			token(str)
		"""
		self.swarm_manager.change_token(token)

	