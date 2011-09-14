import ROOT as R

from ...utils import fixup_hist_units

from .canvas import render_canvas

def build_draw_params(h, params):
    options = ["colz" if isinstance(h, R.TH2) else "box"]
    if "hist" in params:
        options.append("hist")
    if "e0x0" in params:
        options.append("e0x0")
    return " ".join(options)

    
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
