from .. import log; log = log[__name__]

import ROOT as R

from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response

from ...utils.timer import timer

from .histogram import render_histogram
from .canvas import render_actual_canvas
from .graph import render_graph

@log.trace()
def view_root_object_render(context, request):
    if request.params.get("render", "") == "xml":
        o = context.obj
        xmlfile = R.TXMLFile("test.xml", "recreate")
        o.Write()
        xmlfile.Close()
        with open("test.xml") as fd:
            content = fd.read()
        return Response(content, content_type="text/plain")

    if issubclass(context.cls, R.TH1):
        return render_histogram(context, request)
            
    if issubclass(context.cls, R.TGraph):
        return render_graph(context, request)
        
    if issubclass(context.cls, R.TCanvas):
        return render_actual_canvas(context, request)
        
    return HTTPFound(location=static_url('weboot:static/close_32.png', request))
