from contextlib import contextmanager
from shutil import rmtree
from tempfile import mkdtemp


@contextmanager
def TemporaryDirectory(*args, **kwargs):
    d = mkdtemp(*args, **kwargs)
    try:
        yield d
    finally:
        rmtree(d)
