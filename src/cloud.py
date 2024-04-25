try:
    from src.simple_socket_client import simple_socket_client
    from src.bc import Blockchain, Transaction
    from src.UserAccountSystem import *
except:
    from simple_socket_client import simple_socket_client
    from bc import Blockchain, Transaction
    from UserAccountSystem import *
from threading import Thread
from socket import AF_INET, SOCK_STREAM, socket
from pickle import loads
from time import sleep


class cloud:
    __TCP_server: simple_socket_client
    __UDP_server: simple_socket_client
    block_chain = Blockchain()
    __interface: Thread
    __client_handler: Thread
    __user: str
    __account_system = UserAccountSystem()

    def __init__(self) -> None:
        self.__user = None
        # change to your server address, this is local network test
        self.__TCP_server = simple_socket_client(
            mode=0, interface=False, host="192.168.1.86", port=50, self_port=None
        )
        print("loading block chain")
        self.__TCP_server.send(b"<hash>init")
        self.__UDP_server = simple_socket_client(
            mode=1, interface=False, host="192.168.1.86", port=51, self_port=52
        )
        self.__interface = Thread(target=self.__user_interface)
        self.__client_handler = Thread(target=self.__handler)
        self.__interface.start()
        self.__client_handler.start()

    # only work in local network
    def broadcast(self, data):
        """request a broadcast"""
        self.__TCP_server.send(b"<brod>" + data)

    def __user_interface(self):
        while True:
            try:
                i = input()
                commands = i.split(" ")
                op = commands[0]

                if op == "login":  # init block chain
                    login_status = self.__account_system.login(commands[1], commands[2])
                    if login_status:
                        print("login success")
                        self.__user = commands[1]

                elif op == "recv":  # show received message
                    print(self.__TCP_server.recv_buffer)
                    print(self.__UDP_server.recv_buffer)

                elif op == "trade":  # send money to someone
                    if self.__user == None:
                        print("login required")
                        continue
                    receiver = commands[1]
                    amount = commands[2]
                    if self.block_chain.get_balance(self.__user) < int(amount):
                        print("no enough balance")
                        print(
                            "remining: {}".format(
                                self.block_chain.get_balance(self.__user)
                            )
                        )
                        continue
                    self.__TCP_server.send(
                        "<trad>{} {} {}".format(self.__user, receiver, amount).encode()
                    )

                elif op == "check":  # check local block chain correctness
                    self.__TCP_server.send(
                        "<hash>{}".format(
                            self.block_chain.get_latest_block_hash()
                        ).encode()
                    )

                elif op == "kill":  # shutdown server, authorized client only
                    s = socket(AF_INET, SOCK_STREAM)
                    s.connect(("192.168.1.86", 49))
                    s.send(commands[1].encode())
                    s.close()

                elif op == "wallet":  # check balance of a user
                    print(self.block_chain.get_balance(commands[1]))

                elif op == "create":
                    user = commands[1]
                    pw = commands[2]
                    print(
                        "create user status: {}".format(
                            self.__account_system.create_user(user, pw)
                        )
                    )

                # just close the tab
                # elif op == "exit":
                #     print("client system exiting")
                #     exit(0)

                elif op == "mine":
                    # suppose to be a long time mining, but for demo I just make the system transact 100 to account

                    # self.block_chain.mine_block()

                    self.block_chain.add_transaction(
                        Transaction("SYSTEM", self.__user, 100, 0)
                    )
                    self.__TCP_server.send(
                        "<trad>SYSTEM {} 100".format(self.__user).encode()
                    )

                else:  # unknown command
                    pass
            except Exception as e:
                print(e)

    def __handler(self):
        """receive the latest block chain"""
        while True:
            if len(self.__TCP_server.recv_buffer) != 0:
                self.block_chain = loads(self.__TCP_server.recv_buffer.pop())
            if len(self.__UDP_server.recv_buffer) != 0:
                self.block_chain = loads(self.__UDP_server.recv_buffer.pop())
            sleep(1)
