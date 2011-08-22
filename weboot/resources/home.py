"""
This file contains the Home object 
"""

from .locationaware import LocationAware

# ** Additional imports appear below to avoid circular dependencies ** #


class HomeResource(dict, LocationAware):
    def add(self, name, cls, *args, **kwargs):
        self[name] = cls.from_parent(self, name, *args, **kwargs)        

    def __init__(self, request):
        self.request = request
        
        self.add("browse", FilesystemTraverser)
        self.add("baskets", BasketBrowser)

        
from .baskets import BasketBrowser
from .filesystem import FilesystemTraverser

