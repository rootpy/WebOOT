

# PyTrie! https://bitbucket.org/gsakkis/pytrie/src/804df264a06f/pytrie.py

from os import listdir
from os.path import basename, exists, isfile, isdir, join as pjoin

import re
import fnmatch

from pyramid.httpexceptions import HTTPError, HTTPFound, HTTPNotFound, HTTPMethodNotAllowed
from pyramid.traversal import traverse
from pyramid.url import static_url

import ROOT as R

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

class LocationAware(object):
    __name__ = ""
    __parent__ = None

    @property
    def forward_url(self):
        pass

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
        self['result'] = FilesystemTraverser.from_parent(self, "result")
        self['browse'] = FilesystemTraverser.from_parent(self, "browse")
        self['baskets'] = BasketBrowser.from_parent(self, "baskets")


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
    def section(self):
        if issubclass(self.cls, R.TH1):
            return "hist"
        if "TParameter" in self.cls.__name__:
            return "parameters"
    
    @property
    def content(self):
        if issubclass(self.cls, R.TH1):
            try:
                return ['<p><img id="plot" src="{0}" /></p>'.format(self["!render"].url)]
            except HTTPError as e:
                pass               
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
            if issubclass(self.cls, R.TH1):
                return self.sub_url("!render", query={"resolution": 25})
        except HTTPError as e:
            # Catch HTTP errors, fall back
            pass
        return static_url('weboot:static/close_32.png', self.request)
    
    def __getitem__(self, what):
        if what == "!render":
            return RootObjectRender.from_parent(self, "!render", self.obj)
            
        elif what == "!project":
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
            self.request.db.baskets.insert({"basket":"my_basket", "url": self.url, "name": self.name})
            print "adding %s to basket" % self.url
            return HTTPFound(location=self.url)

class HistogramTable(RootObject):
    @property
    def content(self):
        if "cut" not in self.name:
            raise HTTPMethodNotAllowed("Table only works on cutflow histograms")
    
        h = self.obj    
        xa = h.GetXaxis()
        content = []
        content.append('<table style="float:left"><thead><tr><th>Bin</th><th>Content</th><th width="200px">% prev</th></tr></thead>')
        prev = h[1]
        for i in xrange(1, xa.GetNbins()):
            a = xa.GetBinLabel(i), int(h[i]), h[i] / prev if prev else 0
            prev = h[i]
            content.append('<tr><td>{0}</td><td style="text-align:right; font-family: monospace">{1}</td><td style="text-align: right;">{2:.3%}</td></tr>'.format(*a))
        content.append("</table>")
        content.append('<div style="float:right;"><img src="../!render?resolution=50&logy" /></div><div style="clear:both;"></div>')
        return content

def get_haxis(h, ax):
    return getattr(h, "Get{0}axis".format(ax.upper()))()

class MultiProjector(RootObject):

    def __init__(self, request, root_obj, axinfo=None):
        super(MultiProjector, self).__init__(request, root_obj)
        self.axinfo = axinfo

    @property
    def content(self):
        if not self.axinfo:
            raise HTTPMethodNotAllowed("Bad parameters, expecting /[projection_axis]![slice_axis]")
        #return ["Incoming..", str(self.axinfo)]
        content = []
        a1, a2 = self.axinfo
        nbins = get_haxis(self.obj, a2).GetNbins()
        for i in xrange(1, nbins):
            content.append('<img src="../../!range/{slice_ax}!{0}!{0}/!project/{proj_ax}/!render/" />'.format(i, slice_ax=a2, proj_ax=a1))
        return content

    def __getitem__(self, what):
        if self.axinfo: 
            # Already got axis information, forget about it.
            return
        axinfo = what.split("!")
        return MultiProjector.from_parent(self, what, self.obj, axinfo)

class Projector(RootObject):
    def __getitem__(self, what):
        if "".join(sorted(what)) not in ("x", "y", "z", "xy", "xz", "yz"):
            raise HTTPMethodNotAllowed("Bad parameter '{0}', expected axes".format(what))
        return RootObject.from_parent(self, what, self.obj.Project3D(what))
        
class Profiler(RootObject):
    def __getitem__(self, what):
        if "".join(sorted(what)) not in ("x", "y", "z", "xy", "xz", "yz"):
            raise HTTPMethodNotAllowed("Bad parameter '{0}', expected axes".format(what))
        if len(what) == 2:
            return RootObject.from_parent(self, what, self.obj.Project3DProfile(what))
        return RootObject.from_parent(self, what, self.obj.Project3DProfile(what))

class Ranger(RootObject):
    def __getitem__(self, what):
        ax, lo, hi = what.split("!")
        h = self.obj.Clone()
        get_haxis(h, ax).SetRange(int(lo), int(hi))
        return RootObject.from_parent(self, what, h)

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
            self.request.db.baskets.insert({"basket":"my_basket", "url": self.url, "name": self.name})
            print "adding %s to basket" % self.url
            return HTTPFound(location=self.url)
        
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

class TObjArrayTraverser(RootFileTraverser):
    
    def __init__(self, request, obj_array):
        super(TObjArrayTraverser, self).__init__(request, obj_array)
        mapping = self.mapping = {}
        for i, item in enumerate(obj_array):
            orig_name = name = item.GetName()
            n = 0
            while name in mapping:
                name = "{0};{1}".format(orig_name, n)
                n += 1
            mapping[name] = i                    
    
    @property
    def path(self):
        return self.__name__
    
    @property
    def items(self):
        keys = [self[k.GetName()] for k in list(self.rootfile)]
        keys.sort(key=lambda k: k.name)
        return keys
    
    def __getitem__(self, subpath):
        if subpath not in self.mapping:
            return
        root_obj = self.rootfile.At(self.mapping[subpath])
        return RootObject.from_parent(self, subpath, root_obj)

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

        #raise KeyError(subpath)

class BasketBrowser(LocationAware):
    section = "directory"

    def __init__(self, request, path=None):
        self.request = request
        self.path = path
    
    @property
    def name(self):
        if self.path:
            return basename(self.path)
        else:
            return "baskets"
    
    @property
    def icon_url(self):
        return static_url('weboot:static/folder_32.png', self.request)
        
    @property
    def content(self):
        def link(p):
            url = self.request.resource_url(self, p)
            return '<p><a href="{0}">{1}</a></p>'.format(url, p)
        return "".join(link(p) for p in self.ls)
    
    @property
    def items(self):
        if self.path:
            baskets = self.request.db.baskets.find({"basket" : "/^%s/" % self.path})
        else:
            baskets = self.request.db.baskets.find()
        n = self.path.count("/")+1 if self.path else 0
        items = set(b["basket"] for b in baskets)
        items = set(i.split("/")[n] for i in items if len(i.split("/")) > n)
        items = [self[i] for i in sorted(items)]
        items = [i for i in items if i]
        return items
    
    def __getitem__(self, subpath):
        if self.path:
            path = pjoin(self.path, subpath)
        else:
            path = subpath
        basket = self.request.db.baskets.find({"basket" : path})
        if basket: 
            return BasketTraverser.from_parent(self, subpath, basket)
        else:
            return BasketBrowser.from_parent(self, subpath)

class BasketTraverser(LocationAware):
    section = "directory"

    def __init__(self, request, basket=None):
        self.request = request
        self.basket = list(basket)
    
    @property
    def name(self):
        return self.__name__
    
    @property
    def icon_url(self):
        return static_url('weboot:static/folder_chart_32.png', self.request)
        
    @property
    def content(self):
        def link(url, p):
            return '<p><a href="{0}">{1}</a></p>'.format(url, p)
        return "".join(link(p['url'], p['name']) for p in self.basket)
    
    @property
    def items(self):
        return [self[i] for i in range(len(self.basket))]
    
    def __getitem__(self, subpath):
        b = self.basket[int(subpath)]
        return traverse(Root(self.request), b['url'])["context"]
