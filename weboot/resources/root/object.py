from pyramid.httpexceptions import HTTPFound
from pyramid.traversal import resource_path
from pyramid.url import static_url

import ROOT as R

from weboot.resources.actions import action
from ..locationaware import LocationAware

from .util import get_root_class


class ListingItem(object):    
    @property
    def icon_path(self):
        """
        Default Icon
        """
        return static_url('weboot:static/folder_32.png', self.request)

class RootObject(LocationAware, ListingItem):
    """
    A page that shows a ROOT object
    """
    def __init__(self, request, root_object):
        self.request = request
        self.o = root_object
        self.cls = get_root_class(self.o.class_name)
    
    @property
    def section(self):
        if issubclass(self.cls, R.TH1):
            return "hist"
        if "TParameter" in self.cls.__name__:
            return "parameters"
    
    @property
    def content(self):
        if issubclass(self.cls, R.TObjString):
            from cPickle import loads
            from pprint import pformat
            content = pformat(dict(loads(self.obj.GetString().Data())))
            return ["<p><pre>{0}</pre></p>".format(content)]
            
        return ["<p>Hm, I don't know how to render a {0}</p>".format(self.cls.__name__)]
    
    @property
    def obj(self):
        return self.o.get()
    
    @property
    def name(self):
        return self.o.name
        
    @property
    def path(self):
        return self.o.name
        
    @property
    def icon_url(self):
        return static_url('weboot:static/close_32.png', self.request)
    
    def __getitem__(self, key):
        res = self.try_action(key)
        if res: return res
        
        # TODO(pwaller): fix this mess
        from .histogram import FreqHist, HistogramTable
        from .ttree import DrawTTree
            
        if key == "!table":
            return HistogramTable.from_parent(self, "!table", self.o)

        elif key == "!basket":
            self.request.db.baskets.insert({"basket":"my_basket", "path": resource_path(self), "name": self.name})
            print "adding %s to basket" % self.url
            return HTTPFound(location=self.url)
        
        elif key == "!freqhist":
            return FreqHist.from_parent(self, "!freqhist", self.o)
            
        elif key == "!tohist":
            return DrawTTree.from_parent(self, "!tohist", self.o)



