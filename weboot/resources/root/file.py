from os.path import basename, exists, isfile, isdir, join as pjoin

import fnmatch
import re

from pyramid.traversal import traverse
from pyramid.url import static_url

import ROOT as R

from ..locationaware import LocationAware
from ..multitraverser import MultipleTraverser
from .object import get_key_class, RootObject


class RootFileTraverser(LocationAware):
    """
    A traverser to go across ROOT files
    """
    section = "root_file"
    
    def __init__(self, request, rootfile):
        self.request, self.rootfile = request, rootfile
    
    @property
    def name(self):
        return basename(self.rootfile.GetName())
        
    @property
    def icon_url(self):
        return static_url('weboot:static/folder_chart_32.png', self.request)
        
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

        if subpath == "!basket":
            self.request.db.baskets.insert({"basket":"my_basket", "path": resource_path(self), "name": self.name})
            print "adding %s to basket" % self.url
            return HTTPFound(location=self.url)
        
        if subpath == "!selectclass":
            return SelectClass.from_parent(self, subpath, self.rootfile)
        
        if "*" in subpath:
            keys = [l.GetName() for l in self.rootfile.GetListOfKeys()]
            pattern = re.compile(fnmatch.translate(subpath))
            print "Matching keys:", [f for f in keys if pattern.match(f)]
            contexts = [(f, traverse(self, f)["context"])
                        for f in keys if pattern.match(f)]
            return MultipleTraverser.from_parent(self, subpath, contexts)
            
        leaf = self.rootfile.GetKey(subpath)
        if not leaf:
            return
            
        leaf_cls = get_key_class(leaf)
        print "--", self.rootfile, subpath, leaf.GetClassName()
                
        if not leaf:
            raise HTTPNotFound(subpath)
            
        if issubclass(leaf_cls, R.TDirectory):
            leaf = self.rootfile.Get(subpath)
            return RootFileTraverser.from_parent(self, subpath, leaf)
        
        if issubclass(leaf_cls, R.TObjArray):
            leaf = self.rootfile.Get(subpath)
            return TObjArrayTraverser.from_parent(self, subpath, leaf)
        
        return RootObject.from_parent(self, subpath, leaf)
        
class SelectClass(RootFileTraverser):
    def __init__(self, request, rootfile, selection=None):
        super(SelectClass, self).__init__(request, rootfile)
        self.keys = rootfile.GetListOfKeys()
        self.selection = selection
    
    @property
    def items(self):
        if not self.selection:
            return []
        keys = [self[k.GetName()] for k in self.keys if k.GetClassName() == self.selection]
        keys.sort(key=lambda k: k.name)
        return keys
        
    
    def __getitem__(self, subpath):
        if self.selection:
            if "*" in subpath:
                keys = sorted([k.GetName() for k in self.rootfile.GetListOfKeys() 
                               if k.GetClassName() == self.selection])
                pattern = re.compile(fnmatch.translate(subpath))
                contexts = [(f, traverse(self, f)["context"])
                            for f in keys if pattern.match(f)]
                return MultipleTraverser.from_parent(self, subpath, contexts)
            try:
                key = (k for k in self.keys 
                       if k.GetName() == subpath and 
                          k.GetClassName() == self.selection
                      ).next()
            except StopIteration:
                return
            else:
                return super(SelectClass, self).__getitem__(subpath)
        else:
            return self.from_parent(self, subpath, self.rootfile, subpath)
