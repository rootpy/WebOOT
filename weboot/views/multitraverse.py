from weboot.resources.multitraverser import MultipleTraverser
from .root.canvas import render_canvas

from .breadcrumb import build_breadcrumbs
def view_multitraverse(context, request):
    content = []
    for name, finalcontext in context.contexts:
        if isinstance(finalcontext, MultipleTraverser):
            subcontent = []
            for subname, subcontext in finalcontext.contexts:
                subcontent.append('<img class="plot" src="{0.url}?render&resolution=30&{1}" />'.format(subcontext, request.query_string))
            
            content.append('<p>{0}</p><div>{1}</div>'.format(name, "".join(subcontent)))
            continue
        content.append('<p>{0}</p><div><img class="plot" src="{1.url}?render&resolution=50&{2}" /></div>'.format(name, finalcontext, request.query_string))
    return dict(path=build_breadcrumbs(context), #'You are at {0!r} {1!r} <a href="{2}/?render">Render Me</a>'.format(context.path, context, context.url),
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
