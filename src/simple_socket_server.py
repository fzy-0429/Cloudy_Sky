# read before use: this whole library is posix system only, it does not run on windows
from socket import (
    socket,
    AF_INET,
    SOCK_STREAM,
    SOCK_DGRAM,
    SO_BROADCAST,
    SOL_SOCKET,
    SO_REUSEADDR,
)
from gc import collect
from threading import Thread
from json import load
from time import sleep
from subprocess import run


try:
    from src.tools import log, clock, task, instruction_tool
except Exception:
    from tools import log, clock, task, instruction_tool


class simple_socket_server:
    __connection_mode: int
    __timer_interval: int
    Clients_MSG = []

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

    __interface = False

    def __init__(self, mode=0, timer_interval=1, interface=False):
        """init"""
        self.__connection_mode = mode
        self.__timer_interval = timer_interval
        self.__interface = interface

        config: dict
        with open("./config.json") as json:
            config = load(json)
        self.__TCP_host = config["server"]["TCP_host"]
        self.__TCP_port = config["server"]["TCP_port"]
        self.__UDP_host = config["server"]["UDP_host"]
        self.__UDP_port = config["server"]["UDP_port"]
        self.__UDP_broadcast_port = config["server"]["UDP_broadcast_port"]

        self.__shut_down_key = config["server"]["SHUTDOWN"]
        self.__shut_down_trusted = config["server"]["TRUST"]

        self.__main_thread = Thread(target=self.__run)
        self.__shut_down_thread = Thread(target=self.__shut_down)
        self.__timer_thread = Thread(target=self.__timer)

        if self.__interface:
            self.interface = Thread(target=self.__user_interface)
            self.interface.start()

        self.__main_thread.start()
        self.__shut_down_thread.start()
        self.__timer_thread.start()

        self.timer_add_task(log.commit, 5)  # update log for every 5 seconds
        # send all the TCP packet in queue
        self.timer_add_task(self.__sendall, 1)
        # clear recv buffer each hour to save some mem
        self.timer_add_task(self.__clear, 3600)

    def __timer(self):
        """for tasks to run sequentially, and being able to terminate if timeout"""
        counter = 0
        while self.__alive:
            for task_interval in self.__timer_tasks.keys():  # check tasks interval
                if counter % task_interval == 0:
                    # get all tasks
                    for timer_task in self.__timer_tasks[task_interval]:
                        # each task may take up to 3s to finish, if excessed it will be terminated
                        task_timer = clock.clock(
                            task.task(target=timer_task), timeout=3
                        )
                        task_timer.start()
            sleep(self.__timer_interval)
            counter += 1
            # save some mem, if larger than this it will cost two times more mem
            if counter == 2147483647:
                counter = 0
            # collect garbage after each run
            collect()

    def timer_add_task(self, func, interval):
        """add a task to the timer task, only add task that runs forever, no remove after added"""
        if interval in self.__timer_tasks.keys():
            self.__timer_tasks[interval].append(func)
        else:
            self.__timer_tasks[interval] = [func]

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

    def __TCP_run(self, connection: socket, addr):
        """TCP recv thread for a single TCP"""
        # save TCP connnection using address
        try:
            msg = b""
            while self.__alive:
                try:
                    buffer = connection.recv(1024)  # recv 1024 bytes
                    if buffer == b"":  # if recv eof, socket closed
                        connection.close()  # clean up
                        collect()
                        break
                    msg += buffer
                    if len(buffer) < 1024:  # check if this is the last packet
                        if addr[0] not in self.__TCP_recv.keys():
                            self.__TCP_recv[addr[0]] = []
                        self.__TCP_recv[addr[0]].append(msg)
                        # for the block chain server only
                        self.Clients_MSG.append([addr, msg])
                        # print(msg, "\n", self.__TCP_recv, "\n", self.__TCP_pool)
                        msg = b""
                except:
                    log.exception()
                    continue
        except:
            pass
        finally:
            connection.close()
            self.__TCP_pool[addr[0]] = None
            del self.__TCP_pool[addr[0]]
            collect()

    def send(self, data, addr: tuple, mode=0):  # append to send queue
        """data:bytes, address: tuple(host:str,port:int)"""
        if mode == 0:
            self.__TCP_send.append((addr, data))
        else:
            self.__UDP_send.append((addr, data))

    def __sendall(self):  # manually sending all message in queue
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
        try:
            self.__UDP_sock = socket(AF_INET, SOCK_DGRAM)
            self.__UDP_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
            self.__UDP_sock.bind((self.__UDP_host, self.__UDP_port))

            # UDP is connectionless, can't save a connection and do something later
            while self.__alive:
                try:
                    msg, addr = self.__UDP_sock.recvfrom(1024)
                    # print(msg, addr)
                    # dump data to temp buffer
                    if addr[0] not in self.__UDP_recv.keys():
                        self.__UDP_recv[addr[0]] = [msg]
                    else:
                        self.__UDP_recv[addr[0]].append(msg)
                    self.Clients_MSG.append([addr, msg])
                except:
                    log.exception()
                    continue
        except:
            pass
        finally:
            self.__UDP_sock.close()

    def UDP_broadcast(
        self, data, port=None
    ):  # broadcast message to all client in network
        try:
            if port == None:
                port = self.__UDP_broadcast_port
            self.__UDP_sock.sendto(data, ("<broadcast>", port))
        except:
            log.exception()

    def __shut_down(self):  # allowing remote shutdown
        """server remote shutdown thread"""
        self.__shut_down_sock = socket(AF_INET, SOCK_STREAM)
        try:  # a random bug printing out address already in use error, but does not influence functionality, the remote shutdown still works
            self.__shut_down_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.__shut_down_sock.bind((self.__shut_down_host, self.__shut_down_port))
        except:
            pass
        self.__shut_down_sock.listen(1)

        while self.__alive:
            connection, addr = self.__shut_down_sock.accept()
            if addr[0] not in self.__shut_down_trusted:
                log.warning(
                    "A",
                    "UNAUTH SHUTDOWN",
                    "an untrusted devide was trying to shutdown the system but being rejected",
                    addr[0],
                )
            elif connection.recv(1024).decode() == self.__shut_down_key:
                self.__alive = False
                log.shutdown(addr[0])
                sleep(5)
                run(["sudo", "killall", "-9", "python"])
            else:
                log.warning(
                    "B",
                    "AUTH FAIL",
                    "a trusted devide was trying to shutdown the system with worng shutdown key",
                    addr[0],
                )

    def get_data(self, addr, __connection_mode=0):  # get data from the receiving queue
        """get data recv from an address"""
        try:
            return (
                self.__TCP_recv[addr]
                if __connection_mode == 0
                else self.__UDP_recv[addr]
            )
        except:
            return None

    def close_all(self):  # close all TCP connections
        """close all connections"""
        for connection in self.__TCP_pool.keys():
            self.__TCP_pool[connection].close()
            self.__TCP_pool[connection] = None
        collect()

    def __clear(self):  # remove all message
        self.__TCP_recv.clear()
        self.__UDP_recv.clear()
        collect()

    def __user_interface(self):  # manual debug tool
        while self.__interface:
            i = input()
            ins, addr, content = instruction_tool(i)
            if ins == 0:
                print("sending: {} to {}".format(content, addr))
                if self.__connection_mode == 0:
                    self.send(content, (addr, 50), 0)
                else:
                    self.send(content, (addr, 51), 1)
                continue
            if ins == 1:
                print("fetching: {}".format(addr))
                if self.__connection_mode == 0:
                    print(self.get_data(addr))
                else:
                    print(self.get_data(addr, 1))
                continue
            if ins == 2:
                print("closing: {}".format(addr))
                self.__TCP_pool[addr].close()
                self.__TCP_pool[addr] = None
                collect()
            if ins == 3:
                print("exiting interface")
                self.__interface = False
                continue
            if ins == 4:
                if self.__connection_mode == 0:
                    print(self.__TCP_recv)
                else:
                    print(self.__UDP_recv)
                continue
            if ins == -1:
                print("unknown instruction")
                continue

    def get_num_connections(self):  # check number of TCP connections
        """get number of online clients, for block chain server"""
        return len(self.__TCP_pool.keys())
