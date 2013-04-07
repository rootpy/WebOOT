from .. import log
log = log[__name__]

import ROOT as R

from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.url import static_url

from ...utils.timer import timer


@log.trace()
def view_root_object_render(context, request):
    """
    Only called if the object doesn't inherit from Renderable
    """

    if request.params.get("render", "") == "xml":
        o = context.obj
        xmlfile = R.TXMLFile("test.xml", "recreate")
        o.Write()
        xmlfile.Close()
        with open("test.xml") as fd:
            content = fd.read()
        return Response(content, content_type="text/plain")

    return HTTPFound(location=static_url('weboot:static/close_32.png', request))
