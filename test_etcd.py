import etcd

# # client = etcd.Client() # this will create a client against etcd server running on localhost on port 4001
client = etcd.Client(port=2379)
# # client = etcd.Client(host='127.0.0.1', port=4003)
# # client = etcd.Client(host='127.0.0.1', port=4003, allow_redirect=False) # wont let you run sensitive commands on non-leader machines, default is true
# # client = etcd.Client(
# #              host='127.0.0.1',
# #              port=4003,
# #              allow_reconnect=True,
# #              protocol='https',)

# # client.write('/asparuhhhh', 123124)
# # print(client.read('nodes').value)




###############


######### micro platvorm 
client.write('/platform/orchestrator/types_instances/smsc_br/smsc_br_1', "10.102.7.80")
client.write('/platform/orchestrator/types_instances/smsc_br/smsc_br_2', "10.102.7.81")
client.write('/platform/orchestrator/types_instances/smsc_br/smsc_br_3', "10.102.7.82")
client.write('/platform/orchestrator/types_instances/smsc_br/smsc_br_4', "10.102.7.83")
client.write('/platform/orchestrator/types_instances/smsc_br/smsc_br_5', "10.102.7.84")
client.write('/platform/orchestrator/types_instances/ussdc_br/ussdc_br_1', "10.102.7.85")
client.write('/platform/orchestrator/types_instances/ussdc_br/ussdc_br_2', "10.102.7.86")
client.write('/platform/orchestrator/types_instances/ussdc_br/ussdc_br_3', "10.102.7.87")
client.write('/platform/orchestrator/types_instances/ussdc_br/ussdc_br_4', "10.102.7.88")
client.write('/platform/orchestrator/types_instances/ussdc_br/ussdc_br_5', "10.102.7.89")


client.write('/platform/orchestrator/types_instances/smsc_ipgw/smsc_ipgw_1', "10.102.7.90")
client.write('/platform/orchestrator/types_instances/smsc_ipgw/smsc_ipgw_2', "10.102.7.91")
client.write('/platform/orchestrator/types_instances/smsc_ipgw/smsc_ipgw_3', "10.102.7.92")
client.write('/platform/orchestrator/types_instances/smsc_ipgw/smsc_ipgw_4', "10.102.7.93")
client.write('/platform/orchestrator/types_instances/smsc_ipgw/smsc_ipgw_5', "10.102.7.94")
client.write('/platform/orchestrator/types_instances/ussdc_ipgw/ussdc_ipgw_1', "10.102.7.95")
client.write('/platform/orchestrator/types_instances/ussdc_ipgw/ussdc_ipgw_2', "10.102.7.96")
client.write('/platform/orchestrator/types_instances/ussdc_ipgw/ussdc_ipgw_3', "10.102.7.97")
client.write('/platform/orchestrator/types_instances/ussdc_ipgw/ussdc_ipgw_4', "10.102.7.98")
client.write('/platform/orchestrator/types_instances/ussdc_ipgw/ussdc_ipgw_5', "10.102.7.99")


client.write('/platform/orchestrator/dynamic_scaling', 'False')
client.write('/platform/orchestrator/smsc_br_per_node', 3)
client.write('/platform/orchestrator/ussdc_br_per_node', 3)

client.write('/platform/orchestrator/smsc_ipgw_per_node', 3)
client.write('/platform/orchestrator/ussdc_ipgw_per_node', 3)
client.write('/platform/orchestrator/smsc_br_min', 4)
client.write('/platform/orchestrator/ussdc_br_min', 3)
client.write('/platform/orchestrator/smsc_ipgw_min', 4)
client.write('/platform/orchestrator/ussdc_ipgw_min', 3)




client.write('/platform/orchestrator/available_servers/10.102.7.124', "")

client.write('/platform/orchestrator/swarm_servers/10.102.7.122', "")
client.write('/platform/orchestrator/swarm_servers/10.102.7.123', "")

client.write('/platform/orchestrator/logging_level', 10)
client.write('/platform/orchestrator/token', "SWMTKN-1-5ynn8bvs5tolq1okngmcysob08fsltgozvnrjpzq95sv5q2w7v-dksyhgw8jhs2h8gx9mco50kj6")
client.write('/platform/orchestrator/master', "10.102.7.122")
client.write('/platform/orchestrator/network_name', "external_macvlan")



######### micro platform
# client.write('/platform/orchestrator/types_instances/br/br_1', "10.102.7.80")
# client.write('/platform/orchestrator/types_instances/br/br_2', "10.102.7.81")
# client.write('/platform/orchestrator/types_instances/br/br_3', "10.102.7.82")
# client.write('/platform/orchestrator/types_instances/br/br_4', "10.102.7.83")
# client.write('/platform/orchestrator/types_instances/br/br_5', "10.102.7.84")
# client.write('/platform/orchestrator/types_instances/br/br_6', "10.102.7.85")
# client.write('/platform/orchestrator/types_instances/br/br_7', "10.102.7.86")
# client.write('/platform/orchestrator/types_instances/br/br_8', "10.102.7.87")
# client.write('/platform/orchestrator/types_instances/br/br_9', "10.102.7.88")
# client.write('/platform/orchestrator/types_instances/br/br_10', "10.102.7.89")


# client.write('/platform/orchestrator/types_instances/ipgw/ipgw_1', "10.102.7.90")
# client.write('/platform/orchestrator/types_instances/ipgw/ipgw_2', "10.102.7.91")
# client.write('/platform/orchestrator/types_instances/ipgw/ipgw_3', "10.102.7.92")
# client.write('/platform/orchestrator/types_instances/ipgw/ipgw_4', "10.102.7.93")
# client.write('/platform/orchestrator/types_instances/ipgw/ipgw_5', "10.102.7.94")
# client.write('/platform/orchestrator/types_instances/ipgw/ipgw_6', "10.102.7.95")
# client.write('/platform/orchestrator/types_instances/ipgw/ipgw_7', "10.102.7.96")
# client.write('/platform/orchestrator/types_instances/ipgw/ipgw_8', "10.102.7.97")
# client.write('/platform/orchestrator/types_instances/ipgw/ipgw_9', "10.102.7.98")
# client.write('/platform/orchestrator/types_instances/ipgw/ipgw_10', "10.102.7.99")



# client.write('/platform/orchestrator/available_servers/10.102.7.122', "")
# client.write('/platform/orchestrator/available_servers/10.102.7.124', "")

# client.write('/platform/orchestrator/swarm_servers/10.102.7.122', "")
# client.write('/platform/orchestrator/swarm_servers/10.102.7.123', "")

# client.write('/platform/orchestrator/logging_level', 10)
# client.write('/platform/orchestrator/token', "SWMTKN-1-5ynn8bvs5tolq1okngmcysob08fsltgozvnrjpzq95sv5q2w7v-dksyhgw8jhs2h8gx9mco50kj6")
# client.write('/platform/orchestrator/master', "10.102.7.122")
# client.write('/platform/orchestrator/network_name', "external_macvlan")
# client.write('/platform/orchestrator/br_per_node', 3)
# client.write('/platform/orchestrator/ipgw_per_node', 3)
# client.write('/platform/orchestrator/br_min', 6)
# client.write('/platform/orchestrator/ipgw_min', 6)


# client.delete('/platform/orchestrator/available_servers/10.102.7.122')
# client.delete('/platform/orchestrator/swarm_servers/10.102.7.124')
# client.delete('/platform/orchestrator/swarm_servers/10.102.7.125')

# client.delete("/platform/orchestrator/")

################################


client.write('/platform/orchestrator/platform_status', "")

# r = client.read('/orchestrator/types_instances/', recursive=True, sorted=True)
# print(r)
# for child in r.children:
#     print("%s: %s" % (child.key,child.value))



from lib.etcd_client import EtcdManagement

etcd = EtcdManagement()
# print(etcd.get_types_instances())
# print(etcd.get_available_servers())
# print(etcd.get_swarm_servers())
# print(etcd.get_logging_level())
# print(etcd.get_network_name())
# print(etcd.get_token())
# print(etcd.get_master())
print(etcd.get_etcd_config())
# print(etcd.get_initial_state())