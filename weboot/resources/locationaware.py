"""
Resources which know where they live should inherit from LocationAware.

This gives them a .url property, and "from_parent" class method.
"""

from .actions import HasActions

class LocationAware(HasActions):
    __name__ = ""
    __parent__ = None
    
    actions = {}
    
    def __init__(self, request):
        self.request = request
    
    @property
    def forward_url(self):
        pass

    def sub_url(self, *args, **kwargs):
        return self.request.resource_url(self, *args, **kwargs)

    def __repr__(self):
        return "<{self.__class__.__name__} url={self.url}>".format(self=self)

    @property
    def url(self):
        return self.sub_url()

    @classmethod
    def from_parent(cls, parent, name, *args, **kwargs):
        c = cls(parent.request, *args)
        c.__name__ = name
        c.__parent__ = parent
        c.__dict__.update(kwargs)
        return c
