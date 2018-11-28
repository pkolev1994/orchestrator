import docker

client = docker.from_env()

print("Volumes => {}".format(client.volumes.list()))

for volume in client.volumes.list():
	print("Volume name => {}".format(volume.name))
	print("Volume id => {}".format(volume.id))
	print("Volume short id => {}".format(volume.short_id))
	print("Volume attrs => {}".format(volume.attrs))