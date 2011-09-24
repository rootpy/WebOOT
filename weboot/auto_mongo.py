from weboot import log; log = log.getChild("auto_mongo")

import atexit
import logging
import sys
from os import makedirs
from os.path import exists, join as pjoin
from signal import SIGKILL

from pexpect import spawn, ExceptionPexpect, EOF

import pymongo
from pymongo.errors import ConnectionFailure


class MongoStartFailure(RuntimeError):
    "Raised if we can't start mongo"


class PythonizeMongoOutput(object):
    """
    A logger used to intercept mongodb log messages and send them to python
    """
    
    def __init__(self, logger, level=logging.DEBUG):
        self.logger, self.level = logger, level
        
        self.sub_loggers = {}
        self.buffer = []
        self.append = self.buffer.append
        
    def get_sublogger(self, name):
        """
        Get a log broadcast function who is a child (`name`) of `self.logger`
        """
        if name in self.sub_loggers:
            return self.sub_loggers[name]
        child_logger = self.logger.getChild(name)
        level, child_log = self.level, child_logger.log
        def log_func(message):
            child_log(level, message)
        self.sub_loggers[name] = log_func
        return log_func
    
    @staticmethod
    def parse_message(original_message):
        date, lb, message = original_message.partition("[")
        child, rb, message = message.partition("]")
        if lb and rb:
            return child, message
        return "mongo", message
    
    def flush(self):
        contents = "".join(self.buffer).split("\n")
        for line in contents:
            if not line.strip():
                continue
            child, message = self.parse_message(line)
            self.get_sublogger(child)(message.strip())
        self.buffer[:] = []        
    
    def write(self, contents):
        self.append(contents)
    

def start_mongo(bin, settings):
    """
    Attempts to start a mongod process located at bin (or searches the path).
    Returns True if mongod appears to be working correctly, False if it had a 
    problem. Registers an atexit handler which kills mongod.
    """
    
    log.getChild("start_mongo").info("Starting {0}".format(bin))
    
    args = []
    for item, value in settings.iteritems():
        if item.startswith("mongo.args."):
            args.extend(["--" + item[len("mongo.args."):], value])
    
    dbpath = settings.get("mongo.args.dbpath", None)
    if dbpath and not exists(dbpath):
        makedirs(dbpath)
    
    # TODO: cStringIO this output, send it to a different logger
    mongo_logger = PythonizeMongoOutput(log.manager.getLogger("mongod"))
    
    try:
        log.info("Mongo args: {0}".format(args))
        mongo_process = spawn(bin, args, logfile=mongo_logger, timeout=None)
    except ExceptionPexpect as e:
        if not e.value.startswith("The command was not found"):
            # Something weird happened that we don't know how to deal with
            raise
        # It doesn't exist
        return False
    
    @atexit.register
    def kill_mongo():
        log.info("Killing MongoDB")
        mongo_process.kill(SIGKILL)
        
    log.info("Waiting for mongo startup (can be slow the first time)")
    
    possibilities = [EOF, "exception", "waiting for connections"]
    GOOD_STATE = len(possibilities) - 1
    index = mongo_process.expect(possibilities)
    
    if index != GOOD_STATE:
        log.info("Mongod didn't reach '{0}' state".format(possibilities[GOOD_STATE]))
        log.info(" -- instead is '{0}'".format(possibilities[index]))
        mongo_process.kill(SIGKILL)
        return False
    
    return True

def try_starting_mongo(settings):
    """
    If the `mongo.run` configuration option is set, try to start mongod
    """
    
    if not settings.get("mongo.run", None):
        raise MongoStartFailure(
            "Couldn't connect to mongodb, not attempting to start mongod "
            "because mongo.run not set")
    
    # Hmm, maybe we should try and start it

    # Do we have a mongo configured?
    mongo_path = settings.get("mongo.path", None)
    if mongo_path:
        if not exists(mongo_path):
            raise RuntimeError("Invalid mongo.path specified in configuration")
        if not start_mongo(pjoin(mongo_path, "mongod"), settings):
            return False
        
    our_mongo = pjoin(sys.prefix, "bin", "mongod")
    log.info("Our mongo would be located at: {0}".format(our_mongo))
    if exists(our_mongo):
        # There is one installed in our prefix, try that first
        if start_mongo(our_mongo, settings):
            return True
            
    # Prefix didn't work, let's try our PATH.
    return start_mongo("mongod", settings)

def configure_mongo(config, settings):
    """
    Setup mongo
    """
    def try_connection(url):
        """
        Attempt to establish a connection, and on success add a NewRequest #
        handler which populates the db attribute of the request object.
        
        Return value of None means success, otherwise the exception is returned
        """
        try:
            connection = pymongo.Connection(mongo_url)
        except ConnectionFailure as e:
            return e
        else:
            return connection[settings.get("mongo.dbname", "WebOOT")]
    
    # Do we know where to connect?
    mongo_url = settings.get('mongo.url', None)
    if not mongo_url:
        raise MongoStartFailure("mongo.url is not configured")
    
    # Try connecting first
    db = try_connection(mongo_url)
    if not isinstance(db, Exception):
        return db
    
    # I couldn't connect. Attempt to start mongod, raises MongoStartError
    try_starting_mongo(settings)
    
    # If we're still here we can try again
    db = try_connection(mongo_url)
    if isinstance(db, Exception):
        # Nope
        raise MongoStartFailure("Can't connect to mongodb: {0}".format(db))
    return db
