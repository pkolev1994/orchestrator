import threading
import paramiko
import time
import socket
import scp


class Node(threading.Thread):
    """
    Node inhertitate threding module
    each Node is a thread that 
    1.Make ssh connection
    2.coppy the take_stats.py script to each
    3.Execute the script and take the result in dict
    """
    def __init__(self, **kwargs):
        """
        Node thread constructor
        Args:
            address(str)
            user(str)
            password(str)
        """
        super().__init__()
        self.address = kwargs.get('address', None)
        self.user = kwargs.get('user', None)
        self.password = kwargs.get('password', None)
        self.ssh_client = paramiko.SSHClient()
        self.output = None
        # start thread
        self.start()

    def _ParamikoConnection(self):
        """
        Connect using paramiko
        writitng self.output attribute with 
        output of the command
        Args:
            None
        """
        try:

            self.ssh_client.load_system_host_keys()
            self.ssh_client.connect(self.address, username=self.user, password=self.password)
            self.ssh_client.connect(self.address)
            scp_client = scp.SCPClient(self.ssh_client.get_transport())
            scp_client.put('exec_script/take_stats.py', '/root/python/')
            _, stdout, _ = self.ssh_client.exec_command('python /root/python/take_stats.py')
            stdout = '\n'.join(map(lambda x: x.rstrip(), stdout.readlines()))
            self.output = eval(stdout)
        except socket.error as e:
            if self.NoCmd:
                print("{}, Connection error: {}".format(self.address, e))
                return
            print('Connection error: {}'.format(e))
            print('Address         : {}'.format(self.address))
            print('Username        : {}'.format(self.user))
            return


    def run(self):
        """
        Run nodeconnection thread
        calling _ParamikoConnection
        """
        self._ParamikoConnection()