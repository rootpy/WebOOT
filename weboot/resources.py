
from os import listdir
from os.path import exists, isfile, isdir, join as pjoin

import re
import fnmatch

from pyramid.httpexceptions import HTTPNotFound
from pyramid.traversal import traverse

import ROOT as R

class LocationAware(object):
    __name__ = ""
    __parent__ = None

    @classmethod
    def from_parent(cls, parent, name, *args, **kwargs):
        c = cls(parent.request, *args)
        c.__name__ = name
        c.__parent__ = parent
        c.__dict__.update(kwargs)
        return c
        
class Root(dict, LocationAware):
    def __init__(self, request):
        self.request = request
        self['result'] = FilesystemTraverser.from_parent(self, "result")
        
class RootObject(LocationAware):
    def __init__(self, request, root_object):
        self.request = request
        self.o = root_object

class DirectoryTraverser(object):
    pass

class RootFileTraverser(LocationAware, DirectoryTraverser):
    def __init__(self, request, rootfile):
        self.request, self.rootfile = request, rootfile
        
    @property
    def path(self):
        return self.rootfile.GetPath()
        
    @property
    def content(self):
        keys = [k.GetName() for k in self.rootfile.GetListOfKeys()]
        def link(p):
            url = self.request.resource_url(self, p)
            return '<p><a href="{0}">{1}</a><img src="{0}" width="10%" height="10%"/></p>'.format(url, p)
        return "".join(link(p) for p in keys)
        
    def __getitem__(self, subpath):
        print "Traversing root object at", subpath
        if "*" in subpath:
            keys = [l.GetName() for l in self.rootfile.GetListOfKeys()]
            pattern = re.compile(fnmatch.translate(subpath))
            print "Matching keys:", [f for f in keys if pattern.match(f)]
            contexts = [(f, traverse(self, f)["context"])
                        for f in keys if pattern.match(f)]
            return MultipleTraverser.from_parent(self, subpath, contexts)
        leaf = self.rootfile.Get(subpath)
        if not leaf:
            raise HTTPNotFound()
        if isinstance(leaf, R.TDirectory):
            return RootFileTraverser.from_parent(self, subpath, leaf)
            
        return RootObject.from_parent(self, subpath, leaf)

class MultipleTraverser(LocationAware, DirectoryTraverser):
    def __init__(self, request, contexts):
        self.request = request
        self.contexts = contexts
    
    @property
    def path(self):
        return "MultipleTraverser"
    
    @property
    def content(self):
        return "Hello! I have some contexts.."
    
    def __getitem__(self, subpath):
        print "Attempting to traverse {0} contexts at {1}".format(len(self.contexts), subpath)
        new_contexts = [(f, traverse(c, subpath)["context"])
                        for f, c in self.contexts]
        if all(x is None for f, x in new_contexts):
            raise HTTPNotFound("Failed to traverse at {0}".format(subpath))
        return MultipleTraverser.from_parent(self, subpath, new_contexts)

class FilesystemTraverser(LocationAware):
    def __init__(self, request):
        self.request = request
        self.path = request.registry.settings["results_path"]
    
    @property
    def content(self):
        def link(p):
            url = self.request.resource_url(self, p)
            return '<p><a href="{0}">{1}</a></p>'.format(url, p)
        return "".join(link(p) for p in self.ls)
    
    @property
    def ls(self):
        return sorted(listdir(self.path))
    
    def __getitem__(self, subpath):
        path = pjoin(self.path, subpath)
        if isfile(path):
            f = R.TFile(path)
            if f.IsZombie() or not f.IsOpen():
                raise HTTPNotFound("Failed to open {0}".format(path))
            return RootFileTraverser.from_parent(self, subpath, f)
            
        elif isdir(path):
            return FilesystemTraverser.from_parent(self, subpath, path=path)
            
        elif "*" in subpath:
            pattern = re.compile(fnmatch.translate(subpath))
            contexts = [(f, traverse(self, f)["context"])
                        for f in listdir(self.path) if pattern.match(f)]
            return MultipleTraverser.from_parent(self, subpath, contexts)

