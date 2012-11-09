"""
An action is something which can be applied to a resource. For example, let's say
you have a `weboot.resources.Histogram` object which represents a 2D histogram.
In order to project that histogram, an "project" action can be defined. This
is done as a function, `project(self, parent, key, axis)`, which is wrapped with
the @action decorator.

Note that in order for the @action decorator to function correctly, it is
necessary for the resource class to inherit from `HasActions`, and in addition
that the `__getitem__` of the resource must first call `HasActions.try_action`
with the `key`, and return the resulting object if it is not None.

The `self` in this context is the Histogram resource. `parent` and `key` are
necessary to construct the correct heirarchy of objects required for traversal.
Actions support an arbitrary number of arguments, which are then subsequent url
fragments, i.e. given the action defined as:

    class Histogram(HasActions, ...):    
        @action
        def my_action(self, parent, key, a, b, c):
            return NewResource(...)

The url:

    /path/to/histogram/!my_action/1/2/3/
    
will result in a `my_action` call with:

    self == the histogram resource
    parent == the resource representing `/!my_action/`
    key == the text `/!my_action/`
    a, b, c = "1", "2", "3"
    
Actions are inherited by subclasses as normal. i.e, actions defined on a
`RootObject` are also available on a `Histogram` due to inheritence.

The `HasActions` class provides a couple of actions which are inherited by all
classes using actions, including `!list_actions` which allows the user to see
the actions supported by a given resource.

Implementation details
======================

The `HasActions` class uses the `HasActionsMeta` metaclass, which enumerates
all of the methods decorated with @action and puts them into a dictionary so
that they can be rapidly discovered by the `try_action` function.

The resource representing the `/!my_action/` URL fragment is an
`ArgumentCollector`. Its children are also ArgumentCollectors until the number
of children is equal to the number of arguments that the `@action`-decorated
function accepts, at which point the child is the return value of that
`@action`-decorated function.
"""

from inspect import getsourcelines

from pyramid.response import Response

from weboot.utils.func import wraps, unwrap

# imported below to avoid circular imports:
# .locationaware.LocationAware 
# .renderable.Renderable

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
        def thunk(orig_resource, key):
            args = orig_resource, key, function, n_args, orig_resource
            return ArgumentCollector.from_parent(*args)
           
    function.is_action = True
    function._action_thunk = thunk
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
                    self.actions["!" + key] = value

class HasActions(object):
    """
    Inherit from this class to use the @action decorator
    """
    __metaclass__ = HasActionsMeta
    
    @action
    def throw(self, key):
        raise RuntimeError("!throw action requested")
    
    @action
    def definition(self, parent, key, name):
        if name in self.actions:
            return CodeDefinition.from_parent(parent, key, self.actions[name])
    
    @action
    def list_actions(self, key):
        return ActionList.from_parent(self, key, self.actions)
    
    @action
    def p(self, parent, key, param, value):
        """
        Collect a parameter
        """
        self.request.params[param] = value
        return self.from_parent(parent, key)
    
    def try_action(self, key):
        if key in self.actions:
            return self.actions[key]._action_thunk(self, key)
    
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
    
    @property
    def target(self):
        return self.function.__name__
    
    def __repr__(self):
        return ('<ArgumentCollector target={self.target} '
                 'collected_args={self.args} url="{self.url}">'
                 .format(self=self))
    
    def __getitem__(self, key):
        args = self.args + (key,)   
        if len(args) >= self.parameters:
            # We've collected enough arguments to execute the wrapped action
            return self.function(self.resource, self, key, *args)
        # Collect this argument
        return ArgumentCollector.from_parent(self, key, self.function, self.parameters, self.resource, args)

# Needs to go here to avoid circular imports
from .renderable import Renderer

class CodeDefinition(Renderer):
    """
    Represents the source code of a function object
    TODO(pwaller): Support for classes, link to online viewer
    """
    def __init__(self, request, function):
        super(CodeDefinition, self).__init__(request, self, None)
        self.function = function

    @property
    def content(self):
        f = self.function
        code = "".join(getsourcelines(f)[0])
        return Response(code, content_type="text/plain")

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }

def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c,c) for c in text)

class ActionList(Renderer):
    """
    List available actions on an object
    """
    def __init__(self, request, actions):
        super(ActionList, self).__init__(request, self, None)
        self.actions = actions
    
    @property
    def content(self):
        c = []
        for key, action in sorted(self.actions.iteritems()):
            c.append("<h1>{0}</h1>".format(key))
            c.append("<pre>")
            c.append(html_escape(self.__parent__["!definition"][key].content.body))
            c.append("</pre>")
        
        return Response("\n\n".join(c), content_type="text/html")
