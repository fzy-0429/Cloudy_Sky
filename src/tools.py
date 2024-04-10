from sys import exc_info
from datetime import datetime
from inspect import stack


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
    def failure(self, type_info, data):
        """unimportant failures"""
        self.__server_log.write(
            "FUNCFAILS:{}\n\t{}\n\t{}\n".format(now(), type_info, data))

    @classmethod
    def event(self, event_name, event_desc):
        """event logging"""
        self.__server_log.write(
            "FUNCEVENT:{}\n\t{}\n\t{}\n\t{}\n".format(now(), event_name, event_desc, stack()[1][3]))

    @classmethod
    def log(self, data):
        """regular logging"""
        self.__server_log.write("SYSTEMLOG:{}\n\t{}\n".format(now(), data))

    @classmethod
    def warning(self, data):
        """dangerous operations"""
        pass

    @classmethod
    def exception(self):
        "exception logging"
        type, obj, trackback = exc_info()
        file, line = trackback.tb_frame.f_code.co_filename, trackback.tb_lineno
        self.__server_log.write(
            "EXCEPTION:{}\n\t{}\n\t{}\n\t\"{}\", line {}\n".format(now(), type, obj, file, line))

    @classmethod
    def shutdown(self, address):
        """server shut down"""
        self.__server_log.write(
            "SHUT DOWN:{}\n\t{}\n".format(now(), address[0])
        )
