import time
from lib.decision_maker import DecisionMaker

from lib.containering import update_config

decision_maker = DecisionMaker()
print("Names => {}".format(decision_maker.apps_by_hosts))
print(decision_maker.making_host_decision('ipgw', 'up'))
