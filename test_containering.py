import time
from lib.containering import ContainerManagement

container_manager = ContainerManagement()

while True:
        print("Names => {}".format(container_manager.get_container_names()))
        container_manager.run_container('10.102.7.122', 'ipgw')
        #container_manager.stop_container(host_ip = '10.102.7.122', name = 'ipgw_6')
        time.sleep(10)
        container_manager.run_container('10.102.7.123', 'ipgw')
        time.sleep(5)

