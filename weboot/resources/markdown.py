from os.path import basename

import markdown

from pyramid.response import Response

from .locationaware import LocationAware
from .renderable import Renderer, Renderable

class MarkdownRenderer(Renderer):
    @property
    def content(self):
        with open(self.resource_to_render.path) as fd:
            markdown_source = fd.read()
    
        if self.format == "source":
            return Response(markdown_source, content_type="text/plain")
    
        if self.format == "markdown":
            markedup = markdown.markdown(markdown_source)
            return Response(markedup, content_type="text/html")
    
        raise RuntimeError("bad format")
    
        
class MarkdownResource(Renderable, LocationAware):
    renderer = MarkdownRenderer
    section = "documents"
    
    def __init__(self, request, path=None):
        self.request = request
        self.path = path
    
    @property
    def name(self):
        return basename(self.path[:-len(".markdown")])
    
