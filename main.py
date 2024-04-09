from src import simple_socket
from os import getuid

if getuid() != 0:
    print("sudo required")
    exit(0)

s = simple_socket.simple_socket_server()
while 1:
    pass
