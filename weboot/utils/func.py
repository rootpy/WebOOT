from functools import wraps as builtin_wraps


def wraps(function):
    f = builtin_wraps(function)
    print "I am in WRAPS"
    f._weboot_wrapped = function
    print f._weboot_wrapped
    return f


def unwrap(f):
    while hasattr(f, "_weboot_wrapped"):
        f = f._weboot_wrapped
    return f
