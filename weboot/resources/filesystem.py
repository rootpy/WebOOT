from os import listdir
from os.path import basename, exists, isfile, isdir, join as pjoin

import fnmatch
import re

from pyramid.traversal import traverse
from pyramid.url import static_url

import ROOT as R

from .locationaware import LocationAware
from .multitraverser import MultipleTraverser
from .root.file import RootFileTraverser
from ._markdown import MarkdownResource


class FilesystemTraverser(LocationAware):
    section = "directory"

    def __init__(self, request, path=None):
        self.request = request
        self.path = path or request.registry.settings["results_path"]
    
    @property
    def name(self):
        return basename(self.path)
    
    @property
    def icon_url(self):
        if isdir(self.path):
            return static_url('weboot:static/folder_32.png', self.request)
            
        if exists(self.path) and isfile(self.path):
            if self.name.endswith(".root"):
                return static_url('weboot:static/folder_chart_32.png', self.request)
                
        return static_url('weboot:static/close_32.png', self.request)
        
    @property
    def content(self):
        def link(p):
            url = self.request.resource_url(self, p)
            return '<p><a href="{0}">{1}</a></p>'.format(url, p)
        return "".join(link(p) for p in self.ls)
    
    @property
    def items(self):
        items = [self[i] for i in listdir(self.path)]
        items = [i for i in items if i]
        items.sort(key=lambda o: o.name)
        return items
    
    @property
    def keys(self):
        return sorted(listdir(self.path))
    
    def __iter__(self):
        return iter(self.keys)
            
    def __getitem__(self, key):
        path = pjoin(self.path, key)
        if isfile(path) and path.endswith(".markdown"):
            return MarkdownResource.from_parent(self, key, path)
        
        if isfile(path) and path.endswith(".root"):
            # TODO(pwaller): This belongs inside the RootFileTraverser 
            #                 constructor
            # File
            f = R.TFile(path)
            if f.IsZombie() or not f.IsOpen():
                raise HTTPNotFound("Failed to open {0}".format(path))
            return RootFileTraverser.from_parent(self, key, f)
            
        elif isdir(path):
            # Subdirectory
            return FilesystemTraverser.from_parent(self, key, path)
            
        elif "*" in key:
            return MultipleTraverser.from_listable(self, key)
