from functools import wraps as builtin_wraps

def wraps(function):
    f = builtin_wraps(function)
    f.__wrapped__ = function
    return f
    
def unwrap(f):
    while hasattr(f, "__wrapped__"):
        f = f.__wrapped__
    return f
