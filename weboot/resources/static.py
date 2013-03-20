
from os.path import basename

from pyramid.response import Response

from .locationaware import LocationAware
from .renderable import Renderer, Renderable

class StaticImageResource(Renderer, LocationAware):
    
    section = "Images"
    
    def __init__(self, request, path=None):
        self.request = request
        self.path = path
        self.type = None
        if path:
            _, _, self.type = path.rpartition(".")
        self.actions.pop("!resolution", None)
    
    @property
    def source(self):        
        with open(self.path) as fd:
            return fd.read()
            
    @property
    def icon_url(self):
        return self.url
    
    @property
    def content(self):
        return Response(self.source, content_type="image/{0}".format(self.type))
    
    @property
    def name(self):
        return basename(self.path)

