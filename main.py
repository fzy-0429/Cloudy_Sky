from src import simple_socket_server
from src import sky
from os import getuid
from src.tools import log
from src.sky import beacon
from time import sleep
from src.bc import Transaction
from pickle import dumps

if getuid() != 0:
    print("sudo required")
    exit(0)
s = sky.beacon()
s.get_block_chain().add_transaction(Transaction("ALICE", "BOB", 10, 0))

while 1:
    sleep(1)
    s.broadcast()
