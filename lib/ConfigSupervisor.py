import sys
import re
import json
import hashlib
import ast
# import xmltodict

sys.path.append('/opt/containers/ocpytools/lib/')
from logger import Logger
from etcd3_client import EtcdManagement
import xmltodict

class ConfigSupervisor():

	def __init__(self):
		self.current_md5state = ""
		self.current_platform_state = ""
		self.current_state_hosts = []
		self.etcd_manager = EtcdManagement()

	def check_nodesxml(self):
		platform_nodes = self.etcd_manager.get_etcd_orchestrator_config()
		platform_state = ast.literal_eval(platform_nodes["platform"]["orchestrator"]["platform_status"])
		mapping = json.loads(platform_nodes["platform"]["orchestrator"]["nodesxml_mapping"])
		md5state = hashlib.md5(str(platform_state).encode('utf-8')).hexdigest()
		state_hosts = []

		if(md5state == self.current_md5state):
			# write to log here
			pass
		else:
			logger = Logger(filename = "orchestrator", \
							logger_name="ConfigSupervisor check_nodesxml", \
							dirname="/aux1/ocorchestrator/")
			hostnames = self.get_nodexml_hostnames(platform_nodes["platform"]["orchestrator"]["nodes_xml"])
			state_hosts = self.get_hosts(platform_state,state_hosts)
			host_diff = self.is_container_in_nodesxml(hostnames,state_hosts)
			logger.warning("Hostnames: {}, State hosts: {} Host_diff: {}".format(hostnames,state_hosts,host_diff))
			if(host_diff):
				self.add_hostnames_to_nodesxml(platform_nodes["platform"]["orchestrator"]["nodes_xml"],host_diff)
			added,removed = self.compare_hostnames_in_platform_states(state_hosts,self.current_state_hosts)
			self.add_nodeid_to_nodesxml_group(platform_nodes["platform"]["orchestrator"]["nodes_xml"],added,removed,mapping)
			self.current_md5state = md5state
			self.current_platform_state = platform_state
			self.current_state_hosts = state_hosts
			logger.clear_handler()
		return 0

	def get_hosts(self, dat, ips = []):
		for k,v in dat.items():
			if(type(v) is dict):
				self.get_hosts(v, ips)
			else:
				ips.append(k)
		return ips

	def get_ips_of_servers(self, orc_state):
		server_ips = []
		for i in orc_state.keys():
			if(re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',i)):
				server_ips.append(i)
			else:
				pass
		return server_ips

	def get_nodexml_hostnames(self, nxml):
		nodes_xml = xmltodict.parse(nxml,process_namespaces=True)
		ba = []
		# self.logger.warning("type {} value: {}".format(type(nodes_xml),nodes_xml))
		try:
			for k in nodes_xml["nodesinfo"]["nodes"]["node"]:
				# self.logger.warning("Type of nodesxml is: {}, value is: {}".format(type(k),k))
				# print(k)
				ba.append(k["@hostname"])
		except:
			pass
		# self.logger.clear_handler()
		return ba

	def is_container_in_nodesxml(self, nodes,states):
		return list(set(states).difference(nodes))

	def compare_hostnames_in_platform_states(self, newstate,oldstate):
		added = list(set(newstate).difference(oldstate))
		removed = list(set(oldstate).difference(newstate))
		return added,removed

	def get_max_nodesxml_id(self, nodesxml):
		nodes_xml = xmltodict.parse(nodesxml,process_namespaces=True)
		cn = 0
		try:
			for k in nodes_xml["nodesinfo"]["nodes"]["node"]:
				ci = int(k["@id"])
				if(cn < ci):
					cn = ci
		except:
			return 1
		return cn

	def add_hostnames_to_nodesxml(self, nodesxml,hostnames):
		max_node_id = self.get_max_nodesxml_id(nodesxml)
		nodes_xml = nodesxml
		for host in hostnames:
			max_node_id += 1
			node = r'<node id="'+str(max_node_id)+'" hostname="'+host+'" /></nodes>'
			nodes_xml = re.sub(r'<\/nodes>',node,nodes_xml)
		self.etcd_manager.write("/platform/orchestrator/nodes_xml",nodes_xml)
		return nodes_xml

	def get_nodeid_by_hostname(self, nodesxml,hostname):
		ba = 0
		for k in nodesxml["nodesinfo"]["nodes"]["node"]:
			if(k["@hostname"] == hostname):
				ba = k["@id"]
		return ba

	def add_nodeid_to_nodesxml_group(self, nodesxml,for_insert,for_removal,mapping):
		platform_nodes = self.etcd_manager.get_etcd_orchestrator_config()
		nodes_xml = xmltodict.parse(platform_nodes["platform"]["orchestrator"]["nodes_xml"],process_namespaces=True)
		new_nodes_xml = platform_nodes["platform"]["orchestrator"]["nodes_xml"]
		for a in for_insert:
			_,pltfm,app_type,id,_ = re.split(r'(^.*?)_(.*?)_.*(\d+)$',a)
			id = str(self.get_nodeid_by_hostname(nodes_xml,a))
			# print("App is: {} Id: {}".format(app_type,id))
			for b in mapping[app_type].split(","):
				pattern = r'(?s)(<nodetype\s+id="'+ b +'".*?)<\/nodeslist>'
				node_id_pattern = r'(?s)<node\s+id="'+ id +'"\s+\/>'
				group_content = re.search(pattern,new_nodes_xml)
				if(re.search(node_id_pattern, group_content.group(0))):
					continue
				replacement = r'\1<node id="'+ id +'" /></nodeslist>'
				new_nodes_xml = re.sub(pattern,replacement,new_nodes_xml)
		for c in for_removal:
			_,_,app_type1,_,_ = re.split(r'(^.*?)_(.*?)_.*(\d+)$',c)
			id1 = str(self.get_nodeid_by_hostname(nodes_xml,c))
			# print("Removal app is: {} Id: {}".format(app_type1,id1))
			for d in mapping[app_type1].split(","):
				node_id_pattern1 = r'(?s)<node\s+id="'+ id1 +'"\s+\/>'
				new_nodes_xml = re.sub(node_id_pattern1,'',new_nodes_xml)
		self.etcd_manager.write("/platform/orchestrator/nodes_xml",new_nodes_xml)
		return new_nodes_xml
