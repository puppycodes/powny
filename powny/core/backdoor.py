# TODO: Move to separate package


import socket

from contextlog import get_logger

import manhole


# =====
def start(port, reinstall_on_fork=False):
    manhole.logger = get_logger()
    manhole.Manhole.get_socket = staticmethod(_make_get_socket(port))
    manhole.ManholeConnectionThread.check_credentials = staticmethod(_check_credentials)
    manhole.install(patch_fork=reinstall_on_fork)


# =====
def _make_get_socket(port):
    def get_socket():
        for res in socket.getaddrinfo(None, port, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
            (af, sock_type, proto, _, sa) = res
            sa = sa[:2]
            try:
                sock = manhole._ORIGINAL_SOCKET(af, sock_type, proto)  # pylint: disable=protected-access
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except socket.error:
                sock = None
                continue

            try:
                sock.bind(sa)
                sock.listen(0)
                manhole.logger.critical("Manhole opened on *:%d", port)
                return sock
            except socket.error:
                manhole.logger.exception("Cannot bind/listen to %s", sa)

        msg = "Cannot create manhole on *:{}".format(port)
        manhole.logger.error(msg)
        raise RuntimeError(msg)
    return get_socket


def _check_credentials(client):
    # XXX: Access for all clients
    return manhole.get_peercred(client)
