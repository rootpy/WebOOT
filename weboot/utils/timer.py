from contextlib import contextmanager
from time import time

@contextmanager
def timer(what):
    raise RuntimeError("DEPRECATED!")
    start = time()
    try:
        yield
    finally:
        print "Took {0:.3f} to {1}".format(time()-start, what)
