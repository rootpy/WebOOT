
from os import listdir
from os.path import exists, isfile, isdir, join as pjoin

from pyramid.httpexceptions import HTTPNotFound

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
        
    def __repr__(self):
        return '<RootObject h="{0}">'.format(self.o)

class RootFileTraverser(LocationAware):
    def __init__(self, request, rootfile):
        self.request, self.rootfile = request, rootfile
        
    @property
    def content(self):
        keys = [k.GetName() for k in self.rootfile.GetListOfKeys()]
        def link(p):
            url = self.request.resource_url(self, p)
            return '<p><a href="{0}">{1}</a></p>'.format(url, p)
        return "".join(link(p) for p in keys)
        
    def __getitem__(self, subpath):
        leaf = self.rootfile.Get(subpath)
        if not leaf:
            raise HTTPNotFound()
        if isinstance(leaf, R.TDirectory):
            return RootFileTraverser.from_parent(self, subpath, leaf)
        return RootObject.from_parent(self, subpath, leaf)

class FilesystemTraverser(LocationAware):
    def __init__(self, request):
        self.request = request
        self.path = request.registry.settings["results_path"]
    
    @property
    def content(self):
        def link(p):
            url = self.request.resource_url(self, p)
            return '<p><a href="{0}">{1}</a></p>'.format(url, p)
        return "".join(link(p) for p in listdir(self.path))
    
    def __getitem__(self, subpath):
        path = self.path = pjoin(self.path, subpath)
        #print "Attempting traversal on", path, subpath
        if isfile(path):
            f = R.TFile(path)
            if f.IsZombie() or not f.IsOpen():
                raise HTTPNotFound("Failed to open {0}".format(path))
            return RootFileTraverser.from_parent(self, subpath, f)
        return FilesystemTraverser.from_parent(self, subpath, path=self.path)

