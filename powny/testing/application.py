import contextlib
import textwrap

from ..core import apps
from .tmpfile import write_file


# =====
@contextlib.contextmanager
def configured(text=None):
    if text is not None:
        with write_file(textwrap.dedent(text)) as file_path:
            config = apps.init("test", "Test case", ["-c", file_path])
    else:
        config = apps.init("test", "Test case", [])
    try:
        yield config
    finally:
        apps._config = None  # pylint: disable=protected-access
