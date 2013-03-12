"""
Minimal TGraph
"""

import ROOT as R

from rootpy.memory.keepalive import keepalive

from weboot.resources.root.object import RootObject
from weboot.resources.renderable import Renderable, RootRenderer

class GraphRenderer(RootRenderer):
    def render(self, canvas):
        # TODO(pwaller): Introduce some options here..
        g = self.resource_to_render.obj
        opts = "ACP"
        if isinstance(g, R.TGraph2D):
            opts = "SURF"
        g.Draw(opts)
        keepalive(canvas, g)
            
class Graph(Renderable, RootObject):
    renderer = GraphRenderer
    
    def __init__(self, request, root_object):
        super(Graph, self).__init__(request, root_object)
    
    @property
    def content(self):
        rendered = self["!render"]["png"]["!resolution"]["100"]
        return ['<p><img class="plot" src="{0}" /></p>'.format(rendered.sub_url(query={"todo-removeme": 1}))]
        
        #return ['<p><img class="plot" src="{0}" /></p>'.format(self.sub_url(query={"render":None, "resolution":70}))]
