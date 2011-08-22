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

from .resources.multitraverser import MultipleTraverser
from .resources.filesystem import FilesystemTraverser
from .resources.root.file import RootFileTraverser
from .resources.root.object import RootObject, RootObjectRender

def my_view(request):
    
    return {'project':'WebOOT'}

def build_draw_params(h, params):
    options = ["colz" if isinstance(h, R.TH2) else "box"]
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
        
    c = R.TCanvas("{0}{1:03d}".format(h.GetName(), random.randint(0, 999)))
    
    if "logx" in request.params: c.SetLogx()
    if "logy" in request.params: c.SetLogy()
    if "logz" in request.params: c.SetLogz()
    
    if "unit_fixup" in request.params:
        h = fixup_hist_units(h)
    
    if "nostat" in request.params:
        h.SetStats(False)
    
    if "notitle" in request.params:
        h.SetTitle("")
    
    h.Draw(build_draw_params(h, request.params))
    
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
    return dict(path=build_path(context),
                content="\n".join(context.content))
                
@view_config(renderer='weboot:templates/result.pt', context=MultipleTraverser)
def view_multitraverse(context, request):
    content = []
    for c in context.contexts:
        content.append("<p>{repr(0)}</p>".format(c))
    return dict(path="You are at {0}".format(context.path),
                content="\n".join(content))

#@view_config(renderer='weboot:templates/result.pt', context=RootFileTraverser)
#def view_rootfile(context, request):
#    return dict(path="You are at {0}".format(context.path),
#                content=context.content)
    
#@view_config(renderer='weboot:templates/result.pt', context=FilesystemTraverser)
def view_listing(context, request):
    sections = {}
    for item in context.items:
        sections.setdefault(item.section, []).append(item)
    for items in sections.values():
        items.sort(key=lambda o: o.name)
    section_list = []
    #fsorted(sections.iteritems())
    for sec in ["root_file", "directory", "hist"]:
        if sec in sections:
            section_list.append((sec, sections.pop(sec)))
    section_list.extend(sections.iteritems())
    
    return dict(path=build_path(context), 
                context=context,
                sections=section_list)
