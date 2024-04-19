from src import simple_socket_server
from src import sky
from os import getuid
from src.tools import log
from src.sky import sky
from time import sleep
from src.bc import Transaction
from pickle import dumps

if getuid() != 0:
    print("sudo required")
    exit(0)
s = sky()
# while True:
#     sleep(1)
#     s.broadcast()