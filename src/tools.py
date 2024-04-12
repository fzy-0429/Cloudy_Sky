from sys import exc_info
from datetime import datetime
from os import name
from signal import signal, alarm, SIGALRM
from LIE import clock, task
from re import match


def instruction_tool(ins):
    res = (-1, None, None)
    if len(ins) < 4:
        return res
    ip = "((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}"
    op = ins[0:3]
    if op == "send":
        address = match(ip, ins).group[0]
        content = ins.split(ip)[1][1:]
        res = (0, address, content)
    if op == "recv":
        address = match(ip, ins).group[0]
        res = (1, address, None)
    if op == "stop":
        address = match(ip, ins).group[0]
        res = (2, address, None)
    if op == "exit":
        res = (2, None, None)
    return res


def func_timer(time=5):
    if name != "posix":
        raise BaseException("this timer is for posix system only")

    def decorator(func):
        def __timeout(signum, frame):
            raise TimeoutError("function timeout: {}\n".format(func))

        def wrapper(*args, **kwargs):
            signal(SIGALRM, __timeout)
            alarm(time)
            re = func(*args, **kwargs)
            return re

        return wrapper

    return decorator


def now():
    """get current time as string"""
    return datetime.now().strftime("%m\\%d\\%Y %H:%M:%S")


def exception_info():
    """get exception info"""
    type, obj, trackback = exc_info()
    return type, obj, trackback.tb_frame.f_code.co_filename, trackback.tb_lineno


class log:
    __server_log = open("./server_log.log", "a+")

    @classmethod
    def close(self):
        """linux only, windows will save file immediently"""
        self.__server_log.close()

    @classmethod
    def commit(self):
        """save all changes"""
        self.__server_log.flush()

    @classmethod
    def log(self, data):
        """regular logging"""
        self.__server_log.write("SYSTEMLOG:{}\n\t{}\n".format(now(), data))

    @classmethod
    def warning(self, priority, warning_type, warning_desc, data):
        """dangerous operations"""
        self.__server_log.write(
            "WARNLEVL{}:{}\n\t{}\n\t{}\n\t{}\n".format(
                priority, now(), warning_type, warning_desc, data
            )
        )

    @classmethod
    def exception(self):
        "exception logging"
        type, obj, trackback = exc_info()
        file, line = trackback.tb_frame.f_code.co_filename, trackback.tb_lineno
        self.__server_log.write(
            'EXCEPTION:{}\n\t{}\n\t{}\n\t"{}", line {}\n'.format(
                now(), type, obj, file, line
            )
        )

    @classmethod
    def shutdown(self, address):
        """server shut down"""
        self.__server_log.write("SHUT DOWN:{}\n\t{}\n".format(now(), address[0]))
