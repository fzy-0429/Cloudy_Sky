from sys import exc_info
from datetime import datetime
from os import name


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
        self.__server_log.close()
        self.__server_log = open("./server_log.log", "a+")

    @classmethod
    def log(self, data):
        """regular logging"""
        self.__server_log.write("SYSTEMLOG:{}\n\t{}\n".format(now(), data))

    @classmethod
    def warning(self, priority, warning_type, warning_desc, data):
        """dangerous operations"""
        self.__server_log.write("WARNLEVL{}:{}\n\t{}\n\t{}\n\t{}\n".format(
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
