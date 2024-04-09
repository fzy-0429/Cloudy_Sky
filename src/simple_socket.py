from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, SO_BROADCAST, SOL_SOCKET
from gc import collect
from threading import Thread
from json import load
from time import sleep
from subprocess import run
try:
    from src.tools import log
except Exception as e:
    from tools import log


class simple_socket_server:
    __connection_mode = 0

    __TCP_host: str
    __TCP_port: int
    __TCP_pool = {}
    __TCP_recv = {}
    __TCP_sock: socket

    __UDP_host: str
    __UDP_port: int
    __UDP_pool = {}
    __UDP_recv = {}
    __UDP_sock: socket

    __shut_down_host = "0.0.0.0"
    __shut_down_port = 49
    __shut_down_key: str
    __shut_down_sock: socket

    __main_thread: Thread
    __shut_down_thread: Thread
    __alive = True

    def __init__(self) -> None:

        config: dict
        with open("./config.json") as json:
            config = load(json)
        self.__TCP_host = config["server"]["TCP_host"]
        self.__TCP_port = config["server"]["TCP_port"]
        self.__UDP_host = config["server"]["UDP_host"]
        self.__UDP_port = config["server"]["UDP_port"]

        self.__shut_down_key = config["server"]["SHUTDOWN"]
        self.__shut_down_trusted = config["server"]["TRUST"]

        self.__main_thread = Thread(target=self.__run)
        self.__shut_down_thread = Thread(target=self.__shut_down)
        self.__main_thread.daemon = True
        self.__main_thread.start()
        self.__shut_down_thread.start()

    def __run(self):
        if self.__connection_mode == 0:  # TCP
            try:
                self.__TCP_sock = socket(AF_INET, SOCK_STREAM)
                self.__TCP_sock.bind((self.__TCP_host, self.__TCP_port))
                self.__TCP_sock.listen(5)

                while True:
                    c, a = self.__TCP_sock.accept()
                    self.__TCP_pool[a[0]] = Thread(
                        target=self.__TCP_connection, args=(c, a)
                    )
                    self.__TCP_pool[a[0]].start()
            except:
                pass
        else:  # UDP
            pass

    def __TCP_connection(self, connection: socket, address):
        # save TCP connnection using address
        self.__TCP_pool[address[0]] = connection
        msg = b""
        while self.__alive:
            buffer = connection.recv(1024)  # recv 1024 bytes

            if buffer == b"":  # if recv eof, socket closed
                connection.close()  # clean up
                self.__TCP_pool[address[0]] = None
                collect()
                break

            msg += buffer

            if len(buffer) < 1024:  # check if this is the last packet
                if address[0] not in self.__TCP_recv.keys():
                    self.__TCP_recv[address[0]] = []
                self.__TCP_recv[address[0]].append(msg)
                print(msg, "\n", self.__TCP_recv, "\n", self.__TCP_pool)
                msg = b""

        connection.close()
        self.__TCP_pool[address[0]] = None
        collect()

    def __shut_down(self):  # shut down server
        self.__shut_down_sock = socket(AF_INET, SOCK_STREAM)
        self.__shut_down_sock.bind(
            (self.__shut_down_host, self.__shut_down_port))
        self.__shut_down_sock.listen(1)
        while self.__alive:
            connection, address = self.__shut_down_sock.accept()
            if address[0] not in self.__shut_down_trusted:
                continue
            elif connection.recv(1024).decode() == self.__shut_down_key:
                self.__alive = False
                print("SHUT DOWN")
                sleep(5)
                run(["sudo", "killall", "-9", "python"])

    def get_data(self, address, __connection_mode=0):  # get data of address
        return (
            self.__TCP_connection[address]
            if __connection_mode == 0
            else self.__UDP_recv[address]
        )

    def close_all(self):
        for connection in self.__TCP_pool.keys():
            self.__TCP_pool[connection].close()


class simple_socket_client:
    def __init__(self) -> None:
        pass
