try:
    from src.simple_socket_server import simple_socket_server
    from src.bc import Blockchain, Transaction
except:
    from simple_socket_server import simple_socket_server
    from bc import Blockchain, Transaction

from time import sleep
from pickle import dumps
from threading import Thread
from datetime import datetime


class sky:
    __TCP_server: simple_socket_server
    __UDP_server: simple_socket_server
    __block_chain: Blockchain
    __broadcast_port = 52
    __number_of_clients = 0
    __trades = []

    def __init__(self) -> None:
        self.__block_chain = Blockchain()
        self.__TCP_server = simple_socket_server(0, 1, True)
        self.__UDP_server = simple_socket_server(1, 1, True)
        self.__handle_thread = Thread(target=self.__recv_handle)
        self.__clients_num_thread = Thread(target=self.__client_count)
        self.__handle_thread.start()
        self.__clients_num_thread.start()
        self.__log = open("trade_log.log", "a+")

    def broadcast(self):
        """broadcast the last block hash to check block chain integrity"""
        self.__UDP_server.UDP_broadcast(
            dumps(self.__block_chain),
            port=self.__broadcast_port,
        )

    def update(self):
        """access the built-in block chain"""
        return self.__block_chain

    def __recv_handle(self):
        """check if any client need anything"""
        while True:
            if self.__TCP_server.Clients_MSG != []:
                while len(self.__TCP_server.Clients_MSG) != 0:
                    self.__handle(self.__TCP_server.Clients_MSG.pop())
            sleep(1)

    def __client_count(self):
        """check number of online clients"""
        while True:
            sleep(5)
            self.__number_of_clients = self.__TCP_server.get_num_connections()

    def __handle(self, packet):
        """handle client requests"""
        command = packet[1][:6]
        if command == b"<brod>":  # a client want to broadcast something
            self.__UDP_server.UDP_broadcast(
                b"<client_broadcast> IP:%s MSG:%s"
                % (packet[0][0].encode(), packet[1][6:]),
                port=self.__broadcast_port,
            )

        if command == b"<hash>":
            if self.__block_chain.get_latest_block_hash().encode() == command[6:]:
                pass
            else:
                self.broadcast()

        if command == b"<trad>":
            sender, receiver, amount = packet[1][6:].split(b" ")
            sender = sender.decode()
            receiver = receiver.decode()
            amount = float(amount)
            self.__block_chain.add_transaction(Transaction(sender, receiver, amount, 0))
            self.__log.write(
                "TRANSACTION:{}\n\tSENDER:{}\n\tRECEIVER:{}\n\tAMOUNT:{}\n".format(
                    datetime.now().strftime("%m\\%d\\%Y %H:%M:%S"),
                    sender,
                    receiver,
                    amount,
                )
            )
            self.__log.flush()
            self.broadcast()
