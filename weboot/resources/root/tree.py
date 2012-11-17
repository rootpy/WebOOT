import ROOT as R

from weboot.resources.actions import action

from ..multitraverser import MultipleTraverser

from .histogram import Histogram
from .object import RootObject

class Tree(RootObject):
    def __init__(self, request, root_object, selection="", binning=""):
        self.selection = selection
        self.binning = binning
        super(Tree, self).__init__(request, root_object)
    
    @property
    def content(self):
        content = ('<a href="!draw/{0}/">{0}</a><br />'.format(l.GetName())
                   for l in self.obj.GetListOfLeaves())
        return ["<p><pre>{0}</pre></p>".format("\n".join(content))]
        
    @action
    def select(self, parent, key, arg):
        if MultipleTraverser.should_multitraverse(arg):
            return MultipleTraverser.from_listable(parent, arg, self)
        return Tree.from_parent(parent, key, self.o, arg, self.binning)
    
    @action
    def binning(self, parent, key, arg):
        return Tree.from_parent(parent, key, self.o, self.selection, arg)
        
    @action
    def draw(self, parent, key, arg):
        if MultipleTraverser.should_multitraverse(arg):
            return MultipleTraverser.from_listable(parent, arg, self)
            
        def draw(t):
        
            if self.binning:
                # TODO(pwaller): gDirectory needs to be thread-unique. Otherwise:
                #       bad bad, sad sad.
                # TODO(pwaller): Parse self.binning, call appropriate h.
                n, low, hi = self.binning.split(",")
                n, low, hi = int(n), float(low), float(hi)
                h = R.TH1D("htemp", arg, n, low, hi)
                h.SetDirectory(R.gDirectory)
                # BUG: TODO(pwaller): Memory leak
                R.SetOwnership(h, False)
        
            drawn = t.Draw(arg + ">>htemp", self.selection, "goff")
            
            if self.binning:
                h.SetDirectory(None)
            else:
                h = t.GetHistogram()
            if not h:
                raise RuntimeError("Bad draw: '%s' selection='%s'",
                                      arg, self.selection)
            return h
                    
        arg = arg.replace(".", "*")
        return Histogram.from_parent(parent, key, self.o.transform(draw))
    
    @property
    def items(self):
        items = [self[i] for i in self]
        items = [i for i in items if i]
        items.sort(key=lambda o: o.name)
        return items
    
    def keys(self):
        return sorted(leaf.GetName() for leaf in self.obj.GetListOfLeaves())
    
    def __iter__(self):
        return iter(self.keys())

