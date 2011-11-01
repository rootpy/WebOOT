"""
"""

from contextlib import contextmanager
from random import randint
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
from thread import get_ident

import ROOT as R

from pyramid.response import Response

from ... import log; log = log.getChild("views.root.canvas")
from ...utils.timer import timer

@log.trace()
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

@contextmanager
def render_canvas(resolution=100, target_type="png", c=None):
    # We need a thread-specific name, otherwise if two canvases exist with the
    # same name we can get a crash
    canvas_name = str(get_ident()) + str(randint(0, int(1e14)))
    log.debug("Operating with canvas {0} ({1} alive)"
              .format(canvas_name, len(R.gROOT.GetListOfCanvases())))
    assert not R.gROOT.GetListOfCanvases().FindObject(canvas_name), (
        "Canvas collision")
    
    if c is None:
        c = R.TCanvas(canvas_name)
    def f():
        with NamedTemporaryFile(suffix=".eps") as tmpfile:
            c.SaveAs(tmpfile.name)
            if target_type == "eps":
                content = open(tmpfile.name).read()
            else:
                content = convert_eps(tmpfile.name, resolution, target_type)
        return Response(content, content_type="image/{0}".format(target_type))
            
    c._weboot_canvas_to_response = f
    yield c
    # Make the canvas go away. Don't wait for GC.
    c.IsA().Destructor(c)

def render_actual_canvas(context, request):
    canvas = context.obj
    
    resolution = min(int(request.params.get("resolution", 100)), 200)
    with render_canvas(resolution, c=canvas) as c:
        if "logx" in request.params: c.SetLogx()
        if "logy" in request.params: c.SetLogy()
        if "logz" in request.params: c.SetLogz()
        
        c.Draw()
        
        return c._weboot_canvas_to_response()
        
        
