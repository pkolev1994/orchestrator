import docker
import re
import json
import time


def get_statistics(cli):

	oc_containers = {}
	for container in cli.containers.list():
		stats = container.stats(decode = False, stream=False)
		oc_containers[container.name] = {"stats": stats, "container_id": container}

	return oc_containers

def parse_role_config():
	"""
	Parse test_role_config.json and load it to a dictionary
	Returns:
		js_data(dict)
	"""
	try:
		with open('types_instances.json') as json_data:
			js_data = json.load(json_data)
	except IOError:
		raise("File => role_config.json couldn't be opened for read!")

	return js_data

def orchestration(cli):
	client = cli
	print("List of running containers => {}".format(client.containers.list()))
	range_of_names = parse_role_config()
	oc_containers = get_statistics(client)

	for oc_container in oc_containers.keys():
		mem_usage = oc_containers[oc_container]['stats']['memory_stats']['usage']
		# print("Name => {} MEM => {}".format(oc_container, mem_usage))
		# print("Range containers => {}".format(range_of_names))
		if mem_usage > 11900000:
			regx = re.search(r'([^\_]+)\_', oc_container, flags=re.I|re.S)
			application = regx.group(1)
			print("Appplication => {}".format(application))
			for range_name in range_of_names[application].keys():
				if not range_name in oc_containers:
					print("This name is not runned as container => {} with this ip => {}".format \
						(range_name, range_of_names[application][range_name]))
					runned_container = client.containers. \
								run(image = "g2.pslab.opencode.com:5000/{}1". \
								format(application), \
								hostname = range_name, name = range_name, \
								privileged = True, detach=True)
					client.networks.get("external").connect(runned_container, \
						ipv4_address=range_of_names[application][range_name])
					del(range_of_names[application][range_name])
					print("Exiting from orchestration func because we run a container")
					return
				else:
					continue
		elif mem_usage < 11300000:
			print("Stopping container gracefully giving it 30 seconds timeout => {}". \
														format(oc_container))
			oc_containers[oc_container]['container_id'].stop(timeout=30)
			print("Exiting from orchestration func because we stop a container")
			return

def main():
	while True:
		client = docker.from_env()
		orchestration(client)
		print("=== Pruned  stopped containers ===")
		client.containers.prune(filters=None)
		print("Waiting for 45 seconds")
		time.sleep(45)



main()



with open("oc_containers.json", "a") as container_file:
    container_file.write(json.dumps(oc_containers, indent = 4))
