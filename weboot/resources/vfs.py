from .. import log; log = log[__name__]

from os import listdir
from os.path import basename, exists, isfile, isdir, join as pjoin

import fnmatch
import re

from pyramid.traversal import traverse
from pyramid.url import static_url
from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import FileResponse, Response

import ROOT as R

from .renderable import Renderer
from .actions import action
from .locationaware import LocationAware
from .multitraverser import MultipleTraverser
from ._markdown import MarkdownResource
from .static import StaticImageResource
from ..utils.root_vfs import RootVFS
from .root.builder import build_root_object



class VFSTraverser(LocationAware):
    section = "directory"

    def __init__(self, request, path=None, vfs=None):
        self.request = request
        self.path = path or request.registry.settings["results_path"]
        self.vfs = vfs or RootVFS(self.path)

    @action
    def download(self, parent, key):
        #  return FileResponse(self.path)
        with open(self.path) as fd:
            contents = fd.read()
        return Response(contents, content_type="application/x-pdf",
                        content_disposition="Content-Disposition: attachment; filename=beamer.pdf;")

    @property
    def name(self):
        return basename(self.path)
    
    @property
    def icon_url(self):
        p = self.vfs.get(self.path)

        if p.isdir():
            if p.isvfile():
                return static_url('weboot:static/folder_chart_32.png', self.request)
            else:
                return static_url('weboot:static/folder_32.png', self.request)
        elif p.isobject():
            raise RuntimeError("Should not be a VFSTraverser!")
        return static_url('weboot:static/close_32.png', self.request)
    
    @property
    def items(self):
        items = [self[i] for i in self]
        items = [i for i in items if i]
        items.sort(key=lambda o: o.name)
        return items
    
    def keys(self):
        try:
            return sorted(self.vfs[self.path].listdir())
        except OSError as err:
            raise HTTPNotFound("Failed to open {0}: {1}".format(self.path, err))
        except KeyError as err:
            raise HTTPNotFound("Failed to open {0}: {1}".format(self.path, err))
    
    def __iter__(self):
        return iter(self.keys())
    
    def __getitem__(self, key):
        if MultipleTraverser.should_multitraverse(key):
            return MultipleTraverser.from_listable(self, key)
        path = pjoin(self.path, key)
        item = self.vfs.get(path)
        if not item:
            #log.debug("VFS returned None")
            return None
        elif item.isdir():
            return VFSTraverser.from_parent(self, key, path, self.vfs)
        elif item.isobject():
            return build_root_object(self, key, item)
        elif path.endswith(".md") or path.endswith(".markdown"):
            return MarkdownResource.from_parent(self, key, path)
        elif path.endswith(".png"):
            return StaticImageResource.from_parent(self, key, path)
        log.debug("Ignoring unknown resource type {0}".format(item))


