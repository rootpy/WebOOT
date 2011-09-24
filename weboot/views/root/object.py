from .. import log; log = log.getChild(__name__)

import ROOT as R

from ...utils.timer import timer

from .histogram import render_histogram
from .canvas import render_actual_canvas
from .graph import render_graph

@log.trace()
def view_root_object_render(context, request):
    if issubclass(context.cls, R.TH1):
        return render_histogram(context, request)
            
    if issubclass(context.cls, R.TGraph):
        return render_graph(context, request)
        
    if issubclass(context.cls, R.TCanvas):
        return render_actual_canvas(context, request)
        
    return HTTPFound(location=static_url('weboot:static/close_32.png', request))
