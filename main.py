from src import simple_socket
from os import getuid
from src.tools import log

if getuid() != 0:
    print("sudo required")
    exit(0)
try:
    1 / 0
except:
    log.log("HELLO")

s = simple_socket.simple_socket_server(1)
