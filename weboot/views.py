from os.path import exists, join as pjoin
from tempfile import NamedTemporaryFile

from pyramid.view import view_config
from pyramid.response import Response

import ROOT as R

from minty.histograms import fixup_hist_units

from .resources import FilesystemTraverser, RootFileTraverser, RootObject

def my_view(request):
    
    print "Test!", R.kTRUE
    
    return {'project':'WebOOT'}
    
    
@view_config(renderer='weboot:templates/result.pt', context=RootObject)
def view_result(context, request):    
    c = R.TCanvas()
    c.SetLogy()
    h = context.o
    h = fixup_hist_units(h)
    h.Draw()
    
    with NamedTemporaryFile(suffix=".png") as tmpfile:
        c.SaveAs(tmpfile.name)
        content = open(tmpfile.name).read()
        
    return Response(content, content_type="image/png")
    
@view_config(renderer='weboot:templates/result.pt', context=RootFileTraverser)
def view_rootfile(context, request):
    return dict(path="You are at {0}".format(context.rootfile.GetPath()),
                content=context.content)
    
@view_config(renderer='weboot:templates/result.pt', context=FilesystemTraverser)
def view_filesystem(context, request):
    return dict(path="You are at {0}".format(context.path),
                content=context.content)
    


