import os
import contextlib
import tempfile
import shutil


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


@contextlib.contextmanager
def write_tree(content):
    try:
        root = tempfile.mkdtemp(prefix="/tmp/")
        for (rel_path, text) in content:
            file_path = os.path.join(root, rel_path)
            dir_path = os.path.dirname(file_path)
            os.makedirs(dir_path, exist_ok=True)
            with open(file_path, "w") as text_file:
                text_file.write(text)
        yield root
    finally:
        shutil.rmtree(root)
