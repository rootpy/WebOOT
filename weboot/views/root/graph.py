from .canvas import render_canvas

def render_graph(context, request):
    g = context.obj
    
    resolution = min(int(request.params.get("resolution", 100)), 200)
    with render_canvas(resolution) as c:
        if "logx" in request.params: c.SetLogx()
        if "logy" in request.params: c.SetLogy()
        if "logz" in request.params: c.SetLogz()
        
        g.Draw("ACP")
        
        return c._weboot_canvas_to_response()
