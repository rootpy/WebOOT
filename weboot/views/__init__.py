from cStringIO import StringIO
from os.path import exists, join as pjoin

from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.location import lineage
from pyramid.url import static_url
from pyramid.view import view_config

import ROOT as R

from ..resources.multitraverser import MultipleTraverser
from ..resources.filesystem import FilesystemTraverser
from ..resources.root.file import RootFileTraverser
from ..resources.root.object import RootObject
    
def build_path(context):
    return "".join('<span class="breadcrumb">{0}</span>'.format(l.__name__) 
                    for l in reversed(list(lineage(context))) if l.__name__)

def view_root_object(context, request):
    if context.forward_url:
        return HTTPFound(location=context.forward_url)
    return dict(path=build_path(context),
                content="\n".join(context.content))

