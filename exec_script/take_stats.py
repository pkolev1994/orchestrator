import docker
import re
import socket



def get_statistics(cli):


	host_ip = socket.gethostbyname(socket.gethostname())
	oc_containers = {}
	oc_containers[host_ip] = {}
	for container in cli.containers.list():
		stats = container.stats(decode = False, stream=False)
		container_id_search = re.search('<Container:\s*([^>]+)>', str(container))
		container_id = container_id_search.group(1)
		taken_stats = {}
		taken_stats[container.name] = {
										"stats": stats, 
									   "container_id": container_id
									   }
		oc_containers[host_ip].update(taken_stats)
	return oc_containers

def main():

	client = docker.from_env()
	oc_containers = get_statistics(client)
	print(oc_containers)

main()


