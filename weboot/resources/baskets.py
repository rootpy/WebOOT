
from pyramid.traversal import traverse, resource_path
from pyramid.url import static_url

import ROOT as R

from .locationaware import LocationAware
from .home import HomeResource

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
        return "".join(link(p['path'], p['name']) for p in self.basket)
    
    @property
    def items(self):
        return [self[i] for i in range(len(self.basket))]
    
    def __getitem__(self, subpath):
    
        if not isinstance(subpath, int) and "*" in subpath:
            things = self.items
            raise
            # Pattern            
            pattern = re.compile(fnmatch.translate(subpath))
            contexts = [(f, traverse(self, f)["context"])
                        for f in listdir(self.path) if pattern.match(f)]
            return MultipleTraverser.from_parent(self, subpath, contexts)
            
        b = self.basket[int(subpath)]
        return traverse(HomeResource(self.request), b['path'])["context"]
