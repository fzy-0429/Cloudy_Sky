from os import getuid
from src.sky import sky


if getuid() != 0:
    print("sudo required")
    exit(0)
s = sky()

