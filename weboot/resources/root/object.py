from pyramid.url import static_url

import ROOT as R

from ..locationaware import LocationAware


def get_key_class(key):
    if not isinstance(key, R.TKey):
        return type(key)
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

class RootObject(LocationAware, ListingItem):
    """
    A page that shows a ROOT object
    """
    def __init__(self, request, root_object):
        self.request = request
        self.o = root_object
        self.cls = get_key_class(self.o)
    
    @property
    def section(self):
        if issubclass(self.cls, R.TH1):
            return "hist"
        if "TParameter" in self.cls.__name__:
            return "parameters"
    
    @property
    def content(self):
        if issubclass(self.cls, (R.TH1, R.TGraph, R.TCanvas)):
            try:
                return ['<p><img id="plot" src="{0}" /></p>'.format(self.sub_url(query={"render":None}))]
            except HTTPError as e:
                pass
        if self.cls.__name__.startswith("TParameter"):
            p = self.obj
            return ["<p>{0} : {1}</p>".format(p.GetName(), p.GetVal())]
        if issubclass(self.cls, R.TObjString):
            from cPickle import loads
            from pprint import pformat
            content = pformat(dict(loads(self.obj.GetString().Data())))
            return ["<p><pre>{0}</pre></p>".format(content)]
            
        if issubclass(self.cls, R.TTree):
            content = ('<a href="!tohist/{0}/">{0}</a><br />'.format(l.GetName())
                       for l in self.obj.GetListOfLeaves())
            return ["<p><pre>{0}</pre></p>".format("\n".join(content))]
            
        return ["<p>Hm, I don't know how to render a {0}</p>".format(self.cls.__name__)]
    
    @property
    def obj(self):
        if isinstance(self.o, R.TKey):
            return self.o.ReadObj()
        return self.o
    
    @property
    def name(self):
        return self.o.GetName()
        
    @property
    def path(self):
        return self.o.GetName()
        
    @property
    def icon_url(self):
        try:
            if issubclass(self.cls, (R.TH1, R.TGraph, R.TCanvas)):
                return self.sub_url(query={"resolution": 25, "render":None})
        except HTTPError as e:
            # Catch HTTP errors, fall back
            pass
        return static_url('weboot:static/close_32.png', self.request)
    
    def __getitem__(self, what):
        # TODO: fix this mess
        from .histogram.actions import (Projector, Profiler, 
            Ranger, MultiProjector, HistogramTable, HistogramRebinned)
        from .ttree import DrawTTree
            
        if what == "!project":
            return Projector.from_parent(self, "!project", self.o)
            
        elif what == "!profile":
            return Profiler.from_parent(self, "!profile", self.o)
            
        elif what == "!range":
            return Ranger.from_parent(self, "!range", self.o)
            
        elif what == "!projecteach":
            return MultiProjector.from_parent(self, "!projecteach", self.o)
            
        elif what == "!table":
            return HistogramTable.from_parent(self, "!table", self.o)

        elif what == "!basket":
            self.request.db.baskets.insert({"basket":"my_basket", "path": resource_path(self), "name": self.name})
            print "adding %s to basket" % self.url
            return HTTPFound(location=self.url)
            
        elif what == "!rebin":
            return HistogramRebinned.from_parent(self, "!rebin", self.o)
        
        elif what == "!tohist":
            return DrawTTree.from_parent(self, "!tohist", self.o)


