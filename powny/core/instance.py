import os
import socket
import platform


node_name = None
fqdn = None


def get_info():
    return {
        "node": (node_name or platform.uname()[1]),
        "fqdn": (fqdn or socket.getfqdn()),
        "pid":  os.getpid(),
    }
