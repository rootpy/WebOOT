from os.path import exists, join as pjoin
from tempfile import NamedTemporaryFile

from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response
from pyramid.view import view_config

import ROOT as R

from minty.histograms import fixup_hist_units

from .resources import MultipleTraverser, FilesystemTraverser, RootFileTraverser, RootObject

def my_view(request):
    
    print "Test!", R.kTRUE
    
    return {'project':'WebOOT'}

def build_draw_params(params):
    options = []
    if "hist" in params:
        options.append("hist")
    return " ".join(options)
    
@view_config(renderer='weboot:templates/result.pt', context=RootObject)
def view_result(context, request):
    h = context.o
    if not isinstance(h, R.TH1):
        raise HTTPNotFound("Not a histogram")
    
    print "Will attempt to render", h
    if isinstance(h, R.TH3):
        h = h.Project3D("x")
    if isinstance(h, R.TH2):
        raise HTTPNotFound
    c = R.TCanvas()
    if "log" in request.params:
        c.SetLogy()
    #if h.Get
    h = fixup_hist_units(h)
    
    h.Draw(build_draw_params(request.params))
    
    with NamedTemporaryFile(suffix=".png") as tmpfile:
        c.SaveAs(tmpfile.name)
        content = open(tmpfile.name).read()
        
    return Response(content, content_type="image/png")
    
@view_config(renderer='weboot:templates/result.pt', context=MultipleTraverser)
def view_multitraverse(context, request):
    content = []
    for c in context.contexts:
        content.append("<p>{repr(0)}</p>".format(c))
    return dict(path="You are at {0}".format(context.path),
                content="\n".join(content))

@view_config(renderer='weboot:templates/result.pt', context=RootFileTraverser)
def view_rootfile(context, request):
    return dict(path="You are at {0}".format(context.path),
                content=context.content)
    
@view_config(renderer='weboot:templates/result.pt', context=FilesystemTraverser)
def view_filesystem(context, request):
    return dict(path="You are at {0}".format(context.path),
                content=context.content)
    


