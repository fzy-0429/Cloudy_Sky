from sys import exc_info
from datetime import datetime
from os import name
from signal import signal, alarm, SIGALRM
from LIE import clock, task
import pickle


def instruction_tool(ins):
    res = (-1, None, None)
    try:
        if len(ins) < 4:
            return res
        ins = ins.split(" ")
        if ins[0] == "send":
            if len(ins) > 2:
                res = (0, ins[1], ins[2].encode())
            else:
                res = (0, None, ins[1].encode())
        elif ins[0] == "recv":
            if len(ins) >= 1:
                res = (1, ins[1], None)
            else:
                res = (1, None, None)
        elif ins[0] == "stop":
            if len(ins) >= 1:
                res = (2, ins[1], None)
            else:
                res = (2, None, None)
        elif ins[0] == "exit":
            res = (3, None, None)
        elif ins[0] == "show":
            res = (4, None, None)
    except:
        log.exception()
    finally:
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
    __trade_log = open("./trade_log.log", "a+")

    @classmethod
    def close(self):
        """linux only, windows will save file immediently"""
        self.__server_log.close()
        self.__trade_log.flush()

    @classmethod
    def commit(self):
        """save all changes"""
        self.__server_log.flush()
        self.__trade_log.flush()

    @classmethod
    def trade_request(self, client, sender, receiver, amount):
        """client request write to chain"""
        self.__trade_log.write(
            "CLREQUEST:{}\n\tREQUEST_ID:{}\n\tSENDER:{}\n\tRECEIVER:{}\n\tAMOUNT:{}\n".format(
                now().client, sender, receiver, amount
            )
        )

    @classmethod
    def trade_verify(self, trade_id, admit, deny, result):
        """record how many clients admit a trade"""
        self.__trade_log.write(
            "TRADEVERI:{}\n\tREQUEST_ID:{}\n\tADMIT:{}\n\tDENY:{}\n\tRESULT:{}\n".format(
                now(), trade_id, admit, deny, result
            )
        )

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
