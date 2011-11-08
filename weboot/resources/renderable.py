"""
Renderable objects 
"""

from contextlib import contextmanager
from random import randint
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
from thread import get_ident

from pyramid.response import Response

import ROOT as R

from weboot import log; log = log.getChild("renderable")

from .actions import HasActions, action
from .locationaware import LocationAware

def renderable_view(context, request):
    return context.content
    
    
def convert_eps(input_name, resolution=100, target_type="png"):
    """
    Call convert on an eps file in order to rewrite it to another type.
    This is typically faster and prettier (e.g. anti-aliasing) than ROOT's png 
    files.
    """
    with NamedTemporaryFile(suffix=".png") as tmpfile:
        options = ["-density", str(resolution)]        
        p = Popen(["convert"] + options + [input_name, tmpfile.name])
        p.wait()
        with open(tmpfile.name) as fd:
            content = fd.read()
    
    return content

class Renderable(HasActions):
    """
    Classes inheriting from Renderable gain a !render action
    """
    
    @property
    def icon(self):
        return self.rendered("png")["!resolution"]["25"]
        
    def rendered(self, format):
        return self["!render"][format]
        
    @property
    def icon_url(self):
        return self.icon.url
    
    @action
    def render(self, parent, key, format):
        """
        !render/format
        """
        if not hasattr(self, "renderer"):
            raise RuntimeError("{0} inherits from Renderable but doesn't "
                                  "define `renderer`".format(type(self)))
        return self.renderer.from_parent(parent, key, self, format)

class Renderer(LocationAware):
    """
    The base renderer
    """
    RESOLUTION_DEFAULT, RESOLUTION_MAX = 100, 200
    
    def __init__(self, request, resource_to_render, format, params=None):
        super(Renderer, self).__init__(request)
        self.resource_to_render = resource_to_render
        self.format = format
        self.params = params or {}
    
    @action
    def resolution(self, parent, key, resolution):
        params = {"resolution": resolution}
        params.update(self.params)
        args = parent, key, self.resource_to_render, self.format, params
        return self.from_parent(*args)
    
    @property
    def filename(self):
        """
        The filename for this rendering
        """
        return self.resource_to_render.__name__ + "." + self.format
    
    @property
    @contextmanager
    def canvas(self):
        # We need a thread-specific name, otherwise if two canvases exist with the
        # same name we can get a crash
        canvas_name = str(get_ident()) + str(randint(0, int(1e14)))
        log.debug("Operating with canvas {0} ({1} alive)"
                  .format(canvas_name, len(R.gROOT.GetListOfCanvases())))
        assert not R.gROOT.GetListOfCanvases().FindObject(canvas_name), (
            "Canvas collision")
        
        c = R.TCanvas(canvas_name)
        yield c
        # Make the canvas go away. Don't wait for GC.
        c.IsA().Destructor(c)
    
    def render(self, canvas, keep_alive):
        raise NotImplementedError("Implement this class in the subclass")
    
    def configure_canvas(self, params, c):
        if "logx" in params: c.SetLogx()
        if "logy" in params: c.SetLogy()
        if "logz" in params: c.SetLogz()        
    
    @property
    def content(self):
        params = self.params
        params.update(self.request.params)
        
        resolution = int(params.get("resolution", self.RESOLUTION_DEFAULT))
        resolution = min(resolution, self.RESOLUTION_MAX)
        
        with self.canvas as canvas:
            self.configure_canvas(params, canvas)
            alive = []       
            self.render(canvas, alive.append)
            
            if self.format == "xml":
                # TODO(pwaller): special case
                raise NotImplementedError()
            
            with NamedTemporaryFile(suffix=".eps") as tmpfile:
                canvas.SaveAs(tmpfile.name)
                
                if self.format == "eps":
                    # No conversion necessary
                    content = open(tmpfile.name).read()
                else:
                    content = convert_eps(tmpfile.name, resolution, self.format)
            
            extra_args = {}
            if "attach" in params:
                extra_args.update(content_disposition=(
                    "Content-Disposition: attachment; filename={0};"
                    .format(self.filename)))
                    
            return Response(content,
                content_type="image/{0}".format(self.format), **extra_args)

