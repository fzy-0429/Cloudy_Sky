from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, SO_BROADCAST, SOL_SOCKET
from gc import collect
from threading import Thread
from json import load
from time import sleep
from subprocess import run


try:
    from src.tools import log, clock, task

except Exception:
    from tools import log, clock, task


class simple_socket_server:
    __connection_mode: int
    __timer_interval: int

    __TCP_host: str
    __TCP_port: int
    __TCP_pool = {}
    __TCP_recv = {}
    __TCP_send = []
    __TCP_sock: socket

    __UDP_host: str
    __UDP_port: int
    __UDP_recv = {}
    __UDP_send = []
    __UDP_sock: socket

    __shut_down_host = "0.0.0.0"
    __shut_down_port = 49
    __shut_down_key: str
    __shut_down_sock: socket

    __main_thread: Thread
    __shut_down_thread: Thread
    __timer_thread: Thread
    __timer_tasks = {}
    __alive = True

    def __init__(self, mode=0, timer_interval=1):
        """init"""
        self.__connection_mode = mode
        self.__timer_interval = timer_interval

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
        self.__timer_thread = Thread(target=self.__timer)

        self.__main_thread.start()
        self.__shut_down_thread.start()
        self.__timer_thread.start()

        self.__timer_add_task(log.commit, 5)  # update log for every 5 seconds
        self.__timer_add_task(self.__sendall, 1)  # send all the TCP packet in queue

    def __run(self):
        """main thread"""
        if self.__connection_mode == 0:  # TCP
            try:
                self.__TCP_sock = socket(AF_INET, SOCK_STREAM)
                self.__TCP_sock.bind((self.__TCP_host, self.__TCP_port))
                self.__TCP_sock.listen(5)

                while True:
                    c, a = self.__TCP_sock.accept()
                    self.__TCP_pool[a[0]] = c
                    s = Thread(target=self.__TCP_run, args=(c, a))
                    s.start()
            except Exception:
                log.exception()
        else:  # UDP
            try:
                self.__UDP_run()
            except Exception:
                log.exception()

    def __timer(self):
        """for tasks to run sequentially, and being able to terminate if timeout"""
        counter = 0
        while self.__alive:
            for task_interval in self.__timer_tasks.keys():  # check tasks interval
                if counter % task_interval == 0:
                    for timer_task in self.__timer_tasks[
                        task_interval
                    ]:  # get all tasks
                        task_timer = clock.clock(
                            task.task(target=timer_task),
                            timeout=3,  # each task may take up to 3s to finish, if excessed it will be terminated
                        )
                        task_timer.start()
            sleep(self.__timer_interval)
            counter += 1
            # save some mem, if larger than this it will cost two times more mem
            if counter == 2147483647:
                counter = 0
            # collect garbage after each run
            collect()

    def __timer_add_task(self, func, interval):
        """add a task to the timer task"""
        if interval in self.__timer_tasks.keys():
            self.__timer_tasks[interval].append(func)
        else:
            self.__timer_tasks[interval] = [func]

    def __TCP_run(self, connection: socket, address):
        """TCP recv thread for a single TCP"""
        # save TCP connnection using address
        try:
            msg = b""
            while self.__alive:
                buffer = connection.recv(1024)  # recv 1024 bytes
                if buffer == b"":  # if recv eof, socket closed
                    connection.close()  # clean up
                    collect()
                    break
                msg += buffer
                if len(buffer) < 1024:  # check if this is the last packet
                    if address[0] not in self.__TCP_recv.keys():
                        self.__TCP_recv[address[0]] = []
                    self.__TCP_recv[address[0]].append(msg)
                    # print(msg, "\n", self.__TCP_recv, "\n", self.__TCP_pool)
                    msg = b""
        except:
            pass
        finally:
            connection.close()
            self.__TCP_pool[address[0]] = None
            collect()

    def send(self, data, address: tuple, mode=0):
        """data:bytes, address: tuple(host:str,port:int)"""
        if mode == 0:
            self.__TCP_send.append((address, data))
        else:
            self.__UDP_send.append((address, data))

    def __sendall(self):
        """send all packets in queue"""
        if not any(map(len, (self.__TCP_send, self.__UDP_send))):
            return
        else:
            size = len(self.__TCP_send)
            for x in range(size):
                try:
                    # pull up the connection using address, send the message
                    packet = self.__TCP_send.pop()
                    self.__TCP_pool[packet[0][0]].send(packet[1])
                except:
                    log.exception()
                    continue
            size = len(self.__UDP_send)
            for x in range(size):
                try:
                    # pull up the connection using address, send the message
                    packet = self.__UDP_send.pop()
                    self.__UDP_sock.sendto(packet[1], packet[0])
                except:
                    log.exception()
                    continue

    def __UDP_run(self):
        """UDP recv thread"""
        self.__UDP_sock = socket(AF_INET, SOCK_DGRAM)
        self.__UDP_sock.bind((self.__UDP_host, self.__UDP_port))
        self.__UDP_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        # UDP is connectionless, can't save a connection and do something later
        while self.__alive:
            msg, addr = self.__UDP_sock.recvfrom(1024)
            # print(msg, addr)
            # dump data to temp buffer
            if addr[0] not in self.__UDP_recv.keys():
                self.__UDP_recv[addr[0]] = [msg]
            else:
                self.__UDP_recv[addr[0]].append(msg)

    def __shut_down(self):
        """server remote shutdown thread"""
        self.__shut_down_sock = socket(AF_INET, SOCK_STREAM)
        self.__shut_down_sock.bind((self.__shut_down_host, self.__shut_down_port))
        self.__shut_down_sock.listen(1)

        while self.__alive:
            connection, address = self.__shut_down_sock.accept()
            if address[0] not in self.__shut_down_trusted:
                log.warning(
                    "A",
                    "UNAUTH SHUTDOWN",
                    "an untrusted devide was trying to shutdown the system but being rejected",
                    address[0],
                )
            elif connection.recv(1024).decode() == self.__shut_down_key:
                self.__alive = False
                log.shutdown(address[0])
                sleep(5)
                run(["sudo", "killall", "-9", "python"])
            else:
                log.warning(
                    "B",
                    "AUTH FAIL",
                    "a trusted devide was trying to shutdown the system with worng shutdown key",
                    address[0],
                )

    def get_data(self, address, __connection_mode=0):
        """get data recv from an address"""
        return (
            self.__TCP_recv[address]
            if __connection_mode == 0
            else self.__UDP_recv[address]
        )

    def close_all(self):
        """close all connections"""
        for connection in self.__TCP_pool.keys():
            self.__TCP_pool[connection].close()
            self.__TCP_pool[connection] = None
        collect()


class simple_socket_client:
    __TCP_port: int
    __TCP_pool = {}
    __TCP_recv = {}
    __TCP_sock: socket

    __UDP_host: str
    __UDP_port: int
    __UDP_recv = {}
    __UDP_sock: socket

    def __init__(self) -> None:
        config: dict
        with open("./config.json") as json:
            config = load(json)
        self.__TCP_host = config["server"]["TCP_host"]
        self.__TCP_port = config["server"]["TCP_port"]
        self.__UDP_host = config["server"]["UDP_host"]
        self.__UDP_port = config["server"]["UDP_port"]

    def __run(self):
        pass
