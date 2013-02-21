from .. import log; log = log[__name__]

from cStringIO import StringIO
from os.path import exists, join as pjoin

from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.url import static_url
from pyramid.view import view_config

import ROOT as R

from ..resources.multitraverser import MultipleTraverser
from ..resources.vfs import VFSTraverser
from ..resources.root.object import RootObject

from .breadcrumb import build_breadcrumbs

def view_root_object(context, request):
    if context.forward_url:
        return HTTPFound(location=context.forward_url)
    return dict(path=build_breadcrumbs(context),
                content="\n".join(context.content),
                sidebar="<!-- Hello world -->")

