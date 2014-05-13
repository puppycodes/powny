import socket
import manhole


##### Public methods #####
def start(port, listen):
    manhole.Manhole.get_socket = staticmethod(_make_get_socket(port, listen))
    manhole.ManholeConnection.check_credentials = staticmethod(_check_credentials)
    manhole.install()


##### Private methods #####
def _make_get_socket(port, listen):
    def get_socket():
        for res in socket.getaddrinfo(None, port, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
            (af, sock_type, proto, _, sa) = res
            try:
                sock = manhole._ORIGINAL_SOCKET(af, sock_type, proto) # pylint: disable=W0212
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except socket.error:
                #manhole.logger.exception("Socket error on af=%s, sock_type=%s, proto=%s", af, sock_type, proto)
                sock = None
                continue
            sa = sa[:2]
            try:
                sock.bind(sa)
                sock.listen(listen)
                break
            except socket.error:
                manhole.logger.exception("Cannot bind/listen to %s", sa)

        if sock is not None:
            manhole.logger.info("Manhole opened on *:%d", port)
            return (sock, -1)
        else:
            msg = "Cannot create manhole on *:%d" % (port)
            manhole.logger.error(msg)
            raise RuntimeError(msg)
    return get_socket

def _check_credentials(client):
    # XXX: Access for all clients
    return manhole.get_peercred(client)
