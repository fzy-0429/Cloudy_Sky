from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, SO_BROADCAST, SOL_SOCKET
from threading import Thread

# seperate from server to make it can run on windows


class simple_socket_client:
    __host = "127.0.0.1"
    __port = 50
    __self_port = 55
    __sock: socket
    recv_buffer = []
    __interface = False

    def __init__(self, mode=0, host=None, port=None, interface=False, self_port=None):
        self.mode = mode  # TCP or UDP mode
        self.__interface = interface  # need cmd?
        if host != None and port != None:  # need to connect to a remote server?
            self.__host = host
            self.__port = port
        if self_port != None:  # need to change port?
            self.__self_port = self_port
        if mode == 0:  # TCP
            self.__sock = socket(AF_INET, SOCK_STREAM)
            self.__sock.connect((self.__host, self.__port))
            t = Thread(target=self.TCP_run)
            t.start()
        else:  # UDP
            self.__sock = socket(AF_INET, SOCK_DGRAM)
            self.__sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
            self.__sock.bind(("", self.__self_port))
            t = Thread(target=self.UDP_run)
            t.start()
        if self.__interface:
            t = Thread(target=self.interface)
            t.start()

    def TCP_run(self):
        while True:
            buffer, address = self.__sock.recv(1024)
            if buffer == b"":
                exit(0)
            self.recv_buffer.append(buffer)
            # print(buffer)

    def UDP_run(self):
        while True:
            buffer, address = self.__sock.recvfrom(1024)
            if buffer == b"":
                exit(0)
            self.recv_buffer.append(buffer)
            # print(buffer)

    def interface(self):
        while True:
            i = input()
            i = i.split(" ")
            if i[0] == "send":  # send message to server
                if self.mode == 0:
                    self.__sock.send(i[1].encode())
                else:
                    self.__sock.sendto(i[1].encode(), (self.__host, self.__port))
            elif i[0] == "brod":  # request server to broadcast a message
                if self.mode == 0:
                    self.__sock.send(b"<brod>" + i[1].encode())
                else:
                    self.__sock.sendto(
                        b"<brod>" + i[1].encode(), (self.__host, self.__port)
                    )
            else:
                print(self.recv_buffer)

    def send(self, data):  # send message
        if self.mode == 0:
            self.__sock.send(data)
        else:
            self.__sock.sendto(data, (self.__host, self.__port))
