
from os import listdir
from os.path import basename, exists, isfile, isdir, join as pjoin

import re
import fnmatch

from pyramid.httpexceptions import HTTPNotFound
from pyramid.traversal import traverse
from pyramid.url import static_url

import ROOT as R

def get_key_class(key):
    class_name = key.GetClassName()
    try:
        class_object = getattr(R, class_name)
        return class_object
    except AttributeError:
        return None

class ListingItem(object):    
    @property
    def icon_path(self):
        """
        Default Icon
        """
        return static_url('weboot:static/folder_32.png', self.request)

class LocationAware(object):
    __name__ = ""
    __parent__ = None

    def sub_url(self, *args, **kwargs):
        return self.request.resource_url(self, *args, **kwargs)

    @property
    def url(self):
        return self.sub_url()

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
        #self['result'] = FilesystemTraverser.from_parent(self, "result")
        self['browse'] = FilesystemTraverser.from_parent(self, "browse")

class RootObjectRender(LocationAware):
    """
    A ROOT object being rendered
    """
    def __init__(self, request, root_object):
        self.request = request
        self.o = root_object

class RootObject(LocationAware, ListingItem):
    """
    A page that shows a ROOT object
    """
    def __init__(self, request, root_object):
        self.request = request
        self.o = root_object
        self.cls = get_key_class(self.o)
    
    @property
    def name(self):
        return self.o.GetName()
        
    @property
    def path(self):
        return self.o.GetName()
        
    @property
    def icon_url(self):
        if issubclass(self.cls, R.TH1):
            return self.sub_url("!render", query={"resolution": 25})
        return static_url('weboot:static/close_32.png', self.request)
    
    def __getitem__(self, what):
        if what == "!render":
            return RootObjectRender.from_parent(self, "!render", self.o.ReadObj())

class MultipleTraverser(LocationAware):
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

class RootFileTraverser(LocationAware):
    """
    A traverser to go across ROOT files
    """
    def __init__(self, request, rootfile):
        self.request, self.rootfile = request, rootfile
    
    @property
    def name(self):
        return basename(self.rootfile.GetName())
        
    @property
    def icon_url(self):
        return static_url('weboot:static/folder_32.png', self.request)
        
    @property
    def path(self):
        return self.rootfile.GetPath()
        
    @property
    def content(self):
        keys = [k.GetName() for k in self.rootfile.GetListOfKeys()]
        def link(p):
            url = self.request.resource_url(self, p)
            return '<p><a href="{0}">{1}</a><img src="{0}/render?resolution=25" height="10%"/></p>'.format(url, p)
        return "".join(link(p) for p in keys)
    
    @property
    def items(self):
        keys = [self[k.GetName()] for k in self.rootfile.GetListOfKeys()]
        keys.sort(key=lambda k: k.name)
        return keys
        
    def __getitem__(self, subpath):
        print "Traversing root object at", subpath
        
        if "*" in subpath:
            keys = [l.GetName() for l in self.rootfile.GetListOfKeys()]
            pattern = re.compile(fnmatch.translate(subpath))
            print "Matching keys:", [f for f in keys if pattern.match(f)]
            contexts = [(f, traverse(self, f)["context"])
                        for f in keys if pattern.match(f)]
            return MultipleTraverser.from_parent(self, subpath, contexts)
            
        leaf = self.rootfile.GetKey(subpath)
        if not leaf:
            raise KeyError(subpath)
        leaf_cls = get_key_class(leaf)
        print "--", self.rootfile, subpath, leaf.GetClassName()
        if not leaf:
            raise HTTPNotFound(subpath)
            
        if issubclass(leaf_cls, R.TDirectory):
            leaf = self.rootfile.Get(subpath)
            return RootFileTraverser.from_parent(self, subpath, leaf)
            
        return RootObject.from_parent(self, subpath, leaf)

class FilesystemTraverser(LocationAware):
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
    
    def __getitem__(self, subpath):
        path = pjoin(self.path, subpath)
        if isfile(path) and path.endswith(".root"):
            # File
            f = R.TFile(path)
            if f.IsZombie() or not f.IsOpen():
                raise HTTPNotFound("Failed to open {0}".format(path))
            return RootFileTraverser.from_parent(self, subpath, f)
            
        elif isdir(path):
            # Subdirectory
            return FilesystemTraverser.from_parent(self, subpath, path)
            
        elif "*" in subpath:
            # Pattern
            pattern = re.compile(fnmatch.translate(subpath))
            contexts = [(f, traverse(self, f)["context"])
                        for f in listdir(self.path) if pattern.match(f)]
            return MultipleTraverser.from_parent(self, subpath, contexts)

        raise KeyError(subpath)
