from datetime import datetime


class log:
    def __init__(self) -> None:
        self.__server_log = open("./server_log.log", "a")

    def log(self, data):
        self.__server_log.write("\n".join([data]))

    def error(self, error):
        self.__server_log.write("{}\n".format(error))

    def shutdown(self, address):
        self.__server_log.write(
            "server terminated by {} at {}\n".format(
                address[0], datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            )
        )
