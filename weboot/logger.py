
import os
import logging

from contextlib import contextmanager
from functools import wraps
from time import time

VERBOSE_LEVEL = 15
logging.addLevelName(VERBOSE_LEVEL, "VERBOSE")

# Rename critical to FATAL.
logging.addLevelName(logging.CRITICAL, "FATAL")

# The background is set with 40 plus the number of the color, and the foreground with 30
RED, YELLOW, BLUE, WHITE = 1, 3, 4, 7

# These are the sequences need to get colored ouput
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

def insert_seqs(message):
    return message.replace("$RESET", RESET_SEQ).replace("$BOLD", BOLD_SEQ)

def remove_seqs(message):
    return message.replace("$RESET", "").replace("$BOLD", "")

COLORS = {
    'DEBUG'   : BLUE,
    'VERBOSE' : WHITE,
    'INFO'    : YELLOW,
    'WARNING' : YELLOW,
    'ERROR'   : RED,
    'FATAL'   : RED,
}


class CustomFormatter(logging.Formatter):
    def format(self, record):
        return logging.Formatter.format(self, record)
        
class CustomColoredFormatter(CustomFormatter):
    def __init__(self, msg, datefmt=None, use_color=True):
        msg = insert_seqs(msg)
        logging.Formatter.__init__(self, msg, datefmt)
        self.use_color = use_color

    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in COLORS:
            color_seq = COLOR_SEQ % (30 + COLORS[levelname])
            record.levelname = color_seq + levelname + RESET_SEQ
        return logging.Formatter.format(self, record)


LoggerClass = logging.getLoggerClass()
class ExtendedLogger(LoggerClass):
    def __init__(self, name):
        LoggerClass.__init__(self, name)
    
    def trace(self, level=logging.DEBUG):
        return log_trace(self, level)

    def getChild(self, suffix):
        """
        Taken from CPython 2.7, modified to remove duplicate prefix and suffixes
        """
        if self.root is not self:
            if suffix.startswith(self.name + "."):
                # Remove duplicate prefix
                suffix = suffix[len(self.name + "."):]
                
                suf_parts = suffix.split(".")
                if len(suf_parts) > 1 and suf_parts[-1] == suf_parts[-2]:
                    # If we have a submodule's name equal to the parent's name,
                    # omit it.
                    suffix = ".".join(suf_parts[:-1])
                    
            suffix = '.'.join((self.name, suffix))
            
        return self.manager.getLogger(suffix)

    def verbose(self, *args):
        self.log(VERBOSE_LEVEL, *args)

    def fatal(self, *args):
        self.critical(*args)
        
    def __repr__(self):
        return "<ExtendedLogger {0}>".format(self.name)

ExtendedLogger.__dict__.update(logging._levelNames)

class CustomLogManager(logging.Manager):
    """
    Workaround for CPython 2.6
    """
    def getLogger(self, name):
        logger = logging.Manager.getLogger(self, name)
        logger.__class__ = ExtendedLogger
        return logger

# Reference: 
# http://hg.python.org/cpython/file/5395f96588d4/Lib/logging/__init__.py#l979

log_manager = CustomLogManager(logging.getLogger())

def make_custom_logger(name):
    return log_manager.getLogger(name)

def make_handler(

    FORMAT = "[$BOLD%(name)-20s$RESET][%(levelname)-18s]  %(message)s"
    if os.isatty(handler.stream.fileno()):
        handler.setFormatter(ColoredFormatter(insert_seqs(FORMAT)))
    else:
        handler.setFormatter(MCVizFormatter(remove_seqs(FORMAT)))

def get_log_handler(singleton={}):
    """
    Return the STDOUT handler singleton used for all weboot logging.
    """
    if "value" in singleton:
        return singleton["value"]
        
    
    # Make the top level logger and make it as verbose as possible.
    # The log messages which make it to the screen are controlled by the handler
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)

    singleton["value"] = handler
    return handler

@contextmanager
def log_level(level):
    """
    A log level context manager. Changes the log level for the duration.
    """
    handler = get_log_handler()
    old_level = handler.level
    try:
        handler.setLevel(level)
        yield
    finally:
        handler.setLevel(old_level)

def log_trace(logger, level=logging.DEBUG, show_enter=True, show_exit=True):
    def wrap(function):
        log = logger.getChild(function.__name__).log
        @wraps(function)
        def thunk(*args, **kwargs):
            start = time()
            if show_enter:
                log(level, "__enter__ {0} {1}".format(args, kwargs))
            result = function(*args, **kwargs)
            if show_exit:
                log(level, "__exit__ [{0:.2f} sec]".format(time() - start))
            return result
        return thunk
    return wrap

def get_logger_level(quiet, verbose):
    if quiet:
        log_level = logging.WARNING
    elif not verbose:
        log_level = logging.INFO
    elif verbose == 1:
        log_level = VERBOSE_LEVEL
    elif verbose > 1:
        log_level = logging.DEBUG
        
    return log_level
