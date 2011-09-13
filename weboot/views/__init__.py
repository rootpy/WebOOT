from cStringIO import StringIO
from contextlib import contextmanager
from os.path import exists, join as pjoin
from pprint import pformat
from socket import gethostname, gethostbyaddr
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
from thread import get_ident

from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.location import lineage
from pyramid.response import Response
from pyramid.url import static_url
from pyramid.view import view_config

import ROOT as R

from ..utils import fixup_hist_units
from ..utils.timer import timer

from ..resources.multitraverser import MultipleTraverser
from ..resources.filesystem import FilesystemTraverser
from ..resources.root.file import RootFileTraverser
from ..resources.root.object import RootObject

def home(request):
    
    remote_host = "your machine"
    remote_addr = request.environ.get("REMOTE_ADDR", None)
    if remote_addr:
        remote_host, _, _ = gethostbyaddr(remote_addr)
    
    return {
        'project':'WebOOT', 
        'user': request.environ.get("HTTP_ADFS_FIRSTNAME", "uh, I didn't catch your name"), 
        'login': request.environ.get("HTTP_ADFS_LOGIN", "localuser"), 
        'host': gethostname(),
        'remote_host': remote_host,
        'env': ''}


def view_environ(request):
    
    return {'env': pformat(request.environ)}

def build_draw_params(h, params):
    options = ["colz" if isinstance(h, R.TH2) else "box"]
    if "hist" in params:
        options.append("hist")
    if "e0x0" in params:
        options.append("e0x0")
    return " ".join(options)

def convert_eps(input_name, resolution=100, target_type="png"):
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
    canvas_name = str(get_ident())
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
                with timer("Do EPS conversion"):
                    content = convert_eps(tmpfile.name, resolution, target_type)
        return Response(content, content_type="image/{0}".format(target_type))
            
    c._weboot_canvas_to_response = f
    yield c
    # Make the canvas go away. Don't wait for GC.
    c.IsA().Destructor(c)
    
def render_histogram(context, request):
    h = context.obj
    if not isinstance(h, R.TH1):
        raise HTTPNotFound("Not a histogram")
    
    print "Will attempt to render", h
        
    if "unit_fixup" in request.params:
        h = fixup_hist_units(h)
    
    if "nostat" in request.params:
        h.SetStats(False)
    
    if "notitle" in request.params:
        h.SetTitle("")
    
    resolution = min(int(request.params.get("resolution", 100)), 200)
    with render_canvas(resolution) as c:
        if "logx" in request.params: c.SetLogx()
        if "logy" in request.params: c.SetLogy()
        if "logz" in request.params: c.SetLogz()
        
        h.Draw(build_draw_params(h, request.params))
        
        return c._weboot_canvas_to_response()

def render_graph(context, request):
    g = context.obj
    
    resolution = min(int(request.params.get("resolution", 100)), 200)
    with render_canvas(resolution) as c:
        if "logx" in request.params: c.SetLogx()
        if "logy" in request.params: c.SetLogy()
        if "logz" in request.params: c.SetLogz()
        
        g.Draw("ACP")
        
        return c._weboot_canvas_to_response()

def render_actual_canvas(context, request):
    canvas = context.obj
    
    resolution = min(int(request.params.get("resolution", 100)), 200)
    with render_canvas(resolution, c=canvas) as c:
        if "logx" in request.params: c.SetLogx()
        if "logy" in request.params: c.SetLogy()
        if "logz" in request.params: c.SetLogz()
        
        c.Draw()
        
        return c._weboot_canvas_to_response()

def view_root_object_render(context, request):
    print "I am inside view_roto-object_render:", context, context.o
    if issubclass(context.cls, R.TH1):
        with timer("render histogram"):
            return render_histogram(context, request)
    if issubclass(context.cls, R.TGraph):
        return render_graph(context, request)
    if issubclass(context.cls, R.TCanvas):
        return render_actual_canvas(context, request)
    return HTTPFound(location=static_url('weboot:static/close_32.png', request))
    
def build_path(context):
    return "".join('<span class="breadcrumb">{0}</span>'.format(l.__name__) 
                    for l in reversed(list(lineage(context))) if l.__name__)

def view_root_object(context, request):
    if context.forward_url:
        return HTTPFound(location=context.forward_url)
    return dict(path=build_path(context),
                content="\n".join(context.content))

def view_multitraverse(context, request):
    content = []
    for name, finalcontext in context.contexts:
        content.append("<p>{0} -- {1.url}</p>".format(name, finalcontext))
    return dict(path='You are at {0!r} {1!r} <a href="{2}/?render">Render Me</a>'.format(context.path, context, context.url),
                content="\n".join(content))

def view_multitraverse_render(context, request):
    content = "\n".join(str(fc.obj) for name, fc in context.contexts)
    with render_canvas() as c:
        if "logx" in request.params: c.SetLogx()
        if "logy" in request.params: c.SetLogy()
        if "logz" in request.params: c.SetLogz()
        
        objs = [fc.obj for name, fc in context.contexts]
        max_value = max(o.GetMaximum() for o in objs) * 1.1
        obj = objs.pop()
        obj.GetXaxis().SetRangeUser(0, 100e3)
        obj.Draw("hist")
        obj.SetMaximum(max_value)
        for obj in objs:
            obj.Draw("hist same")
            
        return c._weboot_canvas_to_response()
            
    return Response("Hello, world" + content, content_type="text/plain")

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
                
def view_user(context, request):
    from pyramid.security import authenticated_userid, effective_principals
    return Response("You are looking at user: {0} - {1} <pre>{2}</pre>".format(context.user, authenticated_userid(request), "\n".join(sorted(effective_principals(request)))))
    
def view_new_user(context, request):
    return Response("Welcome, new user: {0}".format(context.user))
