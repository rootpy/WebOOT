import random

from os.path import exists, join as pjoin
from tempfile import NamedTemporaryFile

from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.location import lineage
from pyramid.response import Response
from pyramid.url import static_url
from pyramid.view import view_config

import ROOT as R

from minty.histograms import fixup_hist_units

from .resources import MultipleTraverser, FilesystemTraverser, RootFileTraverser, RootObject, RootObjectRender

def my_view(request):
    
    return {'project':'WebOOT'}

def build_draw_params(params):
    options = ["box"]
    if "hist" in params:
        options.append("hist")
    if "e0x0" in params:
        options.append("e0x0")
    return " ".join(options)

def eps_to_png(what, input_name, resolution=100):
    from subprocess import Popen, PIPE
    with NamedTemporaryFile(suffix=".png") as tmpfile:
        p = Popen(["convert", "-density", str(resolution), input_name, tmpfile.name])
        p.wait()
        with open(tmpfile.name) as fd:
            content = fd.read()
    
    return content

def render_histogram(context, request):
    h = context.o
    if not isinstance(h, R.TH1):
        raise HTTPNotFound("Not a histogram")
    
    print "Will attempt to render", h
    if isinstance(h, R.TH3):
        #h = h.Project3D("x")
        pass
    if isinstance(h, R.TH2):
        h = h.ProjectionX()
        
    c = R.TCanvas("{0}{1:03d}".format(h.GetName(), random.randint(0, 999)))
    
    if "logx" in request.params: c.SetLogx()
    if "logy" in request.params: c.SetLogy()
    
    #h = fixup_hist_units(h)
    
    h.Draw(build_draw_params(request.params))
    
    with NamedTemporaryFile(suffix=".eps") as tmpfile:
        c.SaveAs(tmpfile.name)
        #content = open(tmpfile.name).read()
        resolution = min(int(request.params.get("resolution", 100)), 200)
        content = eps_to_png(h.GetName(), tmpfile.name, resolution)
        
    return Response(content, content_type="image/png")

@view_config(renderer='weboot:templates/result.pt', context=RootObjectRender)
def view_root_object_render(context, request):
    if isinstance(context.o, R.TH1):
        return render_histogram(context, request)
    return HTTPFound(location=static_url('weboot:static/cancel_32.png', request))
    
def build_path(context):
    return "".join('<span class="breadcrumb">{0}</span>'.format(l.__name__) 
                    for l in reversed(list(lineage(context))) if l.__name__)
    
@view_config(renderer='weboot:templates/result.pt', context=RootObject)
def view_root_object(context, request):
    if context.forward_url:
        return HTTPFound(location=context.forward_url)
    content = []
    content.append('<p><img id="plot" src="{0}" /></p>'.format(context["!render"].url))
    return dict(path=build_path(context),
                 content="\n".join(content))
                
#@view_config(renderer='weboot:templates/result.pt', context=MultipleTraverser)
#def view_multitraverse(context, request):
#    content = []
#    for c in context.contexts:
#        content.append("<p>{repr(0)}</p>".format(c))
#    return dict(path="You are at {0}".format(context.path),
#                content="\n".join(content))

#@view_config(renderer='weboot:templates/result.pt', context=RootFileTraverser)
#def view_rootfile(context, request):
#    return dict(path="You are at {0}".format(context.path),
#                content=context.content)
    
#@view_config(renderer='weboot:templates/result.pt', context=FilesystemTraverser)
def view_listing(context, request):
    return dict(path="You are at {0}".format(context.path), 
                context=context,
                items=context.items)
    


