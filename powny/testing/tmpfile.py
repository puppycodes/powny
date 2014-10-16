import os
import contextlib
import tempfile


# =====
@contextlib.contextmanager
def write_file(text):
    try:
        (fd, path) = tempfile.mkstemp()
        os.close(fd)
        with open(path, "w") as yaml_file:
            yaml_file.write(text)
        yield path
    finally:
        os.remove(path)
