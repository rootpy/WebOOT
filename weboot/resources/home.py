"""
This file contains the Home object 
"""

from pyramid.httpexceptions import HTTPFound
from pyramid.security import authenticated_userid

from .locationaware import LocationAware
from .user import UserResource

# ** Additional imports appear below to avoid circular dependencies ** #
class EnvResource(LocationAware):
    def __init__(self, request):
        self.request = request


class HomeResource(LocationAware, dict):
    def __init__(self, request):
        super(HomeResource, self).__init__(request)
        
        self.add("browse", FilesystemTraverser)
        self.add("baskets", BasketBrowser)
        self.add("env", EnvResource)
        
    def add(self, name, cls, *args, **kwargs):
        self[name] = cls.from_parent(self, name, *args, **kwargs)
        
    def __getitem__(self, fragment):    
        if fragment in self:
            return self.get(fragment)
        
        if fragment.startswith("~"):
            return UserResource.make(self, fragment)
            
        if fragment == "me":
            request_user = authenticated_userid(self.request)
            return HTTPFound(location=self.sub_url("~{0}".format(request_user)))
        
        raise KeyError("{0} not found on the HomeResource".format(fragment))

        
from .baskets import BasketBrowser
from .filesystem import FilesystemTraverser

