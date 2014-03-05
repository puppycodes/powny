import sys
import logging

try:
    import cffi
except ImportError:
    cffi = None


##### Public classes #####
class LogRecord(logging.LogRecord):
    def __init__(self, *args, **kwargs):
        logging.LogRecord.__init__(self, *args, **kwargs)
        self.tid = _gettid()


##### Private methods #####
def _make_gettid():
    if sys.platform.startswith("linux") and cffi is not None:
        ffi = cffi.FFI()
        ffi.cdef("int syscall(int number);")
        lib = ffi.verify("""
                #include <unistd.h>
                #include <sys/syscall.h>
            """)
        # 186 - Linux-specific syscall gettid()
        gettid = ( lambda: lib.syscall(186) ) # pylint: disable=E1101
    else:
        gettid = ( lambda: None ) # Fallback
    return gettid
_gettid = _make_gettid()
