from src import simple_socket
from os import getuid
from src.tools import log
from src.Block_Chain import block, chain
from src.sky import beacon
from time import sleep

if getuid() != 0:
    print("sudo required")
    exit(0)
s = simple_socket.simple_socket_server(1, interface=True)

while 1:
    s.UDP_broadcast(b"broadcast", 50)
    sleep(5)
