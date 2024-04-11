from src import simple_socket
from os import getuid
from src.tools import log

if getuid() != 0:
    print("sudo required")
    exit(0)

s = simple_socket.simple_socket_server()
from time import sleep
sleep(5)
print(s.get_data("192.168.1.117"))