from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, SO_BROADCAST, SOL_SOCKET, SO_REUSEADDR
from gc import collect
from threading import Thread
from json import load
from time import sleep
from subprocess import run
try:
    from src.tools import log
except Exception as e:
    from tools import log


# it seems no point to add heartbeat packet mech to this project, it is okay for client to disconnect for no reason

class simple_socket_server:
    """server for both TCP and UDP"""
    __connection_mode = 0

    __TCP_host: str
    __TCP_port: int
    __TCP_pool = {}
    __TCP_recv = {}
    __TCP_send = []
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
        """main thread"""
        if self.__connection_mode == 0:  # TCP
            try:
                self.__TCP_sock = socket(AF_INET, SOCK_STREAM)
                self.__TCP_sock.bind((self.__TCP_host, self.__TCP_port))
                self.__TCP_sock.listen(49)

                while True:
                    c, a = self.__TCP_sock.accept()
                    self.__TCP_pool[a[0]] = Thread(
                        target=self.__TCP_recv_thread, args=(c, a)
                    )
                    self.__TCP_pool[a[0]].start()
            except Exception as e:
                log.exception()
        else:  # UDP
            pass

    def TCP_send_enqueue(self, address: str, msg: bytes):
        """add a message to send queue"""
        self.__TCP_send.append((address, msg))

    def __TCP_send_all(self):
        """send all the messages in the queue"""
        if len(self.__TCP_send):
            return
        msg: bytes
        for packet in self.__TCP_send:
            try:
                if packet[0] in self.__TCP_pool:
                    msg = packet[1]
                    self.__TCP_pool[packet[0]].send(msg)
            except Exception as e:
                log.exception()
                file_name = hash(msg)
                log.event(
                    "TCP SEND FAIL", "MESSAGE SENDING FAILED, MESSAGE SAVED TO .\\temp\\{}".format(file_name))
                with open(".\\temp\\{}".format(file_name), "w+")as msg_rec:
                    msg_rec.write(msg)

    def __TCP_recv_thread(self, connection: socket, address):
        """recving message and add to the dict"""

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
                # print(msg, "\n", self.__TCP_recv, "\n", self.__TCP_pool)
                msg = b""

        connection.close()
        self.__TCP_pool[address[0]] = None
        collect()

    def __shut_down(self):  # shut down server
        """try shut down server, 60s to clean up, connection reset every 20s to avoid shutdown socket being blocked"""

        while self.__alive:  # reset connection
            try:
                self.__shut_down_sock = socket(AF_INET, SOCK_STREAM)
                self.__shut_down_sock.setsockopt(  # allow reuse
                    SOL_SOCKET, SO_REUSEADDR, 1)
                self.__shut_down_sock.bind(
                    (self.__shut_down_host, self.__shut_down_port))
                self.__shut_down_sock.listen(1)
                self.__shut_down_sock.timeout(20)

                while self.__alive:
                    connection, address = self.__shut_down_sock.accept()
                    # shut down request not from a trusted address
                    if address[0] not in self.__shut_down_trusted:
                        continue
                    elif connection.recv(1024).decode() == self.__shut_down_key:
                        self.__alive = False
                        log.shutdown(address)
                        self.close_all()
                        collect()
                        sleep(60)
                        run(["sudo", "killall", "-9", "python"])
            except TimeoutError as timeout:
                self.__shut_down_sock.close()
                continue

    def get_data(self, address, __connection_mode=0):
        """return recieved data"""
        try:
            return (
                self.__TCP_recv[address]
                if __connection_mode == 0
                else self.__UDP_recv[address]
            )
        except Exception as e:
            return None

    def close_all(self):
        """close all the connections"""
        for connection in self.__TCP_pool.keys():
            self.__TCP_pool[connection].close()


class simple_socket_client:
    def __init__(self) -> None:
        pass
