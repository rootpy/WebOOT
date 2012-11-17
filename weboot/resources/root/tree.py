
from tempfile import NamedTemporaryFile

import ROOT as R

from ..actions import action, ResponseContext
from ..multitraverser import MultipleTraverser

from .histogram import Histogram
from .object import RootObject

class Tree(RootObject):
    def __init__(self, request, root_object, selection=(), binning=""):
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
        newsel = self.selection + (arg,)
        return Tree.from_parent(parent, key, self.o, newsel, self.binning)
    
    @action
    def binning(self, parent, key, arg):
        return Tree.from_parent(parent, key, self.o, self.selection, arg)
        
    @property
    def select_value(self):
        """
        Take the values in self.selection and make them into a form suitable to
        pass to TTree::Draw by multiplying each of the components together.
        """
        return " * ".join(map(lambda x: "({0})".format(x), self.selection))
        
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
        
            nvar = len(arg.split(":"))

            opts = "goff "
            if nvar > 4:
                opts += "para "

            drawn = t.Draw(arg + ">>htemp", self.select_value, opts)
            
            if nvar > 4:
                h = t.GetPlayer().GetSelector().GetObject()
            elif self.binning:
                h.SetDirectory(None)
            else:
                h = t.GetHistogram()
            if not h:
                raise RuntimeError("Bad draw: '%s' selection='%s'",
                                      arg, self.select_value)
            return h
                    
        arg = arg.replace(".", "*")
        return Histogram.from_parent(parent, key, self.o.transform(draw))
    
    @action
    def scan(self, parent, key, arg):
        def scan(t):

            nmax = int(self.request.params.get("n", 100))
            with NamedTemporaryFile(suffix=".scan") as tmpfile:
                t.SetScanField(0)
                t.GetPlayer().SetScanFileName(tmpfile.name)
                t.GetPlayer().SetScanRedirect(True)
                n = t.Scan(arg, self.selection, "colsize=30", nmax)
                status = t.GetPlayer().GetSelector().GetStatus()
                if status < 0:
                    return "Unable to compile expression. (TODO: Show reason)\n  value: {0}\n  selection: {1}".format(
                        arg, self.selection)

                tree_data = tmpfile.read()
            return "Scanning {0} entries (status {2}):\n\n{1}".format(n, tree_data, status)
        return ResponseContext.from_parent(parent, key, scan(self.obj), content_type="text/plain")

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

