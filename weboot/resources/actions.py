from inspect import getsourcelines

from weboot.utils.func import wraps
# LocationAware is imported below to avoid circular imports

def action(function):
    """
    Specifies that the decorated function should be called when "!functionname"
    is passed to self.try_action
    """
    n_args = function.__code__.co_argcount
    n_args -= 3 # (self, parent, key)
    
    if n_args <= 0:
        thunk = function
    else:
        @wraps(function)
        def thunk(orig_resource, key):
            args = orig_resource, key, function, n_args, orig_resource
            return ArgumentCollector.from_parent(*args)
    
    function.is_action = True
    function.thunk = thunk
    return function
    
class HasActionsMeta(type):
    """
    Builds a dictionary of actions for the class type
    """
    def __init__(self, name, bases, dct):
        self.actions = {}
        for cls in reversed(self.__mro__):
            for key, value in cls.__dict__.iteritems():
                if getattr(value, "is_action", None):
                    # TODO(pwaller): Assert that value's 
                    self.actions["!" + key] = value.thunk

class HasActions(object):
    """
    Inherit from this class to use the @action decorator
    """
    __metaclass__ = HasActionsMeta
    
    @action
    def definition(self, parent, key, name):
        if key in self.actions:
            return CodeDefinition.from_parent(parent, key, self.actions[name])
    
    @action
    def list_actions(self, key):
        return ActionList.from_parent(self, key, self.actions)
    
    def try_action(self, key):
        if key in self.actions:
            return self.actions[key](self, key)
    
    def __getitem__(self, key):
        """
        This code needs to be called from subclasses, either through copy-pasting
        or super().
        """
        ret = self.try_action(key)
        if ret: return ret

# LocationAware inherits from HasActions.
from weboot.resources.locationaware import LocationAware
            
class ArgumentCollector(LocationAware):
    """
    An intermediate class which collects arguments and passes them all in one 
    go to the desired function
    """
    def __init__(self, request, function, parameters, resource, args=()):
        self.request = request
        self.function, self.parameters, self.resource = function, parameters, resource
        self.args = args
        
    def __getitem__(self, key):
        args = self.args + (key,)   
        if len(args) >= self.parameters:
            # We've collected enough arguments to execute the wrapped action
            return self.function(self.resource, self, key, *args)
        # Collect this argument
        return ArgumentCollector.from_parent(self, key, self.function, self.parameters, self.resource, args)

class CodeDefinition(LocationAware):
    """
    Represents the source code of a function object
    TODO(pwaller): Support for classes, link to online viewer
    """
    def __init__(self, request, function):
        super(CodeDefinition, self).__init__(request)
        self.code = "".join(inspect.getsourcelines(unwrap(function))[0])

class ActionList(LocationAware):
    """
    List available actions on an object
    """
    def __init__(self, request, actions):
        super(ActionList, self).__init__(request)
        self.actions = actions
    
