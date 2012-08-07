import ROOT as R


from weboot.utils.thousands import split_thousands
from weboot.utils.histogram import normalize_by_axis

from weboot.resources.actions import action
from weboot.resources.renderable import Renderable, RootRenderer
from weboot.resources.locationaware import LocationAware
from weboot.resources.multitraverser import MultipleTraverser

from weboot.resources.root.object import RootObject

class HistogramTable(RootObject):
    """
    TODO(pwaller): Fixme
    """
    @property
    def content(self):
        if "cut" not in self.name:
            #raise HTTPMethodNotAllowed("Table only works on cutflow histograms")
            return
    
        h = self.obj    
        xa = h.GetXaxis()
        content = []
        content.append('<table style="float:left"><thead><tr><th>Bin</th><th>Content</th><th width="200px">% prev</th></tr></thead>')
        prev = h[1]
        for i in xrange(1, xa.GetNbins()+1):
            count = split_thousands("{0:.2f}".format(h[i]))
            a = xa.GetBinLabel(i), count, h[i] / prev if prev else 0
            prev = h[i]
            content.append('<tr><td>{0}</td><td style="text-align:right; font-family: monospace">{1}</td><td style="text-align: right;">{2:.3%}</td></tr>'.format(*a))
        content.append("</table>")
        content.append('<div style="float:right;"><img src="../?render&resolution=50&logy" /></div><div style="clear:both;"></div>')
        return content

def get_xyz_func(obj, func, ax):
    return getattr(obj, func.format(ax=ax.upper()))
    
def get_haxis(h, ax):
    return get_xyz_func(h, "Get{ax}axis", ax)()

def make_int(x):
    if isinstance(x, (int, long)): return x
    if isinstance(x, basestring):
        try:
            return int(x)
        except ValueError:
            pass
    raise RuntimeError("Expected integer, got '{0!r}'".format(x))

def make_float(x):
    if isinstance(x, basestring):
        try:
            return float(x)
        except ValueError:
            pass
    else:
        return float(x)
    raise RuntimeError("Expected number, got '{0!r}'".format(x))


def build_draw_params(h, params, box2d=False):
    options = []
    O = options.append
    if isinstance(h, R.TH3):
        O("box")
    elif isinstance(h, R.TH2):
        O("box" if box2d else "colz")
    if "hist" in params:
        O("hist")
    if "e0x0" in params:
        O("e0x0")
    opts = " ".join(options)
    return opts

class HistogramRenderer(RootRenderer):
    def render(self, canvas, keep_alive):
        params = self.request.params
        h = self.resource_to_render.obj
        
        if "unit_fixup" in params:
            h = fixup_hist_units(h)
        
        if "nostat" in params:
            h.SetStats(False)
        
        if "notitle" in params:
            h.SetTitle("")
        
        # TODO(pwaller): bring back draw options
        h.Draw(build_draw_params(h, params))

class Histogram(Renderable, RootObject):
    renderer = HistogramRenderer

    def __init__(self, request, root_object):
        super(Histogram, self).__init__(request, root_object)
        
    @action
    def range(self, parent, key, axis, first, last):
        """
        TH*/!range/axis/first/last
        Apply a range to an axis for projection purposes
        """
        if axis.lower() not in "xyz":
            #raise HTTPMethodNotAllowed("Bad parameter '{0}', expected axes".format(axes))
            return
        
        first = make_float(first)
        last = make_float(last)
        
        def tf(hist):
            #hist = h.Clone()
            get_haxis(hist, axis).SetRangeUser(first, last)
            return hist
        return Histogram.from_parent(parent, key, self.o.transform(tf))

    @action
    def binrange(self, parent, key, axis, first, last):
        """
        TH*/!binrange/axis/first/last
        Apply a range to an axis for projection purposes
        """
        if axis.lower() not in "xyz":
            raise HTTPMethodNotAllowed("Bad parameter '{0}', expected axes".format(axes))
        
        first = make_int(first)
        last = make_int(last)

        def tf(h):
            hist = h.Clone()
            get_haxis(hist, axis).SetRange(int(first), int(last))
            return hist
        return Histogram.from_parent(parent, key, self.o.transform(tf))
    
    @action
    def rebin(self, parent, key, n):
        """
        TH1/!rebin/divisor
        Rebin a 1D histogram
        """
        n = make_int(n)
        def rebin(h): 
	    new_hist = h.Clone()
	    new_hist.Rebin(n)
       	    new_hist.GetXaxis().SetRange(self.obj.GetXaxis().GetFirst(), self.obj.GetXaxis().GetLast())
            new_hist.GetYaxis().SetRange(self.obj.GetYaxis().GetFirst(), self.obj.GetYaxis().GetLast())
            new_hist.GetZaxis().SetRange(self.obj.GetZaxis().GetFirst(), self.obj.GetZaxis().GetLast())
            return new_hist
        return Histogram.from_parent(parent, key, self.o.transform(rebin))
    
    @staticmethod
    def multiproject_slot_filler(multitraverser, key):
        return multitraverser.__parent__[key]
    
    @action
    def project(self, parent, key, axes):
        """
        TH{2/3}/!project/axes
        Project axes out of 2D and 3D histograms
        """
        
        if "," in axes:
            projections = axes.split(",")
            
            new_contexts = [((p,), self["!project"][p]) for p in projections]
            
            return MultipleTraverser.from_parent(parent, key, new_contexts,
                slot_filler=self.multiproject_slot_filler)
        
        if "".join(sorted(axes)) not in ("x", "y", "z", "xy", "xz", "yz"):
            #raise HTTPMethodNotAllowed("Bad parameter '{0}', expected axes".format(axes))
            return
        
        if self.obj.GetDimension() == 1:
            if axes == "x":
                # Only x projection is valid for 1D histogram
                return Histogram.from_parent(parent, key, self.o)
            return
            
        if self.obj.GetDimension() == 2 and len(axes) == 1:
            def project(hist):
                return get_xyz_func(hist, "Projection{ax}", axes)()
            return Histogram.from_parent(parent, key, self.o.transform(project))
       
	def project(hist): 
            # Thread safety, histograms are named by anything which remains in the 
            # option string, and they clobber each other, yay ROOT!
            from random import randint
            random_name = str(randint(0, 2**32-1))
            optstring = "{0}{1}".format(axes, random_name)
            h = hist.Project3D(optstring)
            h.SetName(h.GetName()[:-len(random_name)])
            return h
        
        return Histogram.from_parent(parent, key, self.o.transform(project))
    
    @action
    def profile(self, parent, key, axes):
        """
        TH{2,3}/!profile/axes
        Create a TProfile
        """
    
        if "".join(sorted(axes)) not in ("x", "y", "z", "xy", "xz", "yz"):
            #raise HTTPMethodNotAllowed("Bad parameter '{0}', expected axes".format(axes))
            return

        def tf(h):
            
            if self.obj.GetDimension() == 2 and len(axes) == 1:
                other_axis = "x"
                if axes == "x": 
                    other_axis = "y"
                ya = get_xyz_func(self.obj, "Get{ax}axis", other_axis)()
                new_hist = get_xyz_func(self.obj, "Profile{ax}", axes)()
                new_hist.GetYaxis().SetTitle(ya.GetTitle())
                new_hist.SetTitle(self.obj.GetTitle())
                return new_hist

            if len(axes) == 2:
                new_hist = self.obj.Project3DProfile(axes)
                xa = get_xyz_func(self.obj, "Get{ax}axis", axes[0])()
                ya = get_xyz_func(self.obj, "Get{ax}axis", axes[1])()
                new_hist.GetXaxis().SetTitle(xa.GetTitle())
                new_hist.GetYaxis().SetTitle(ya.GetTitle())
                return new_hist

            return self.obj.Project3DProfile(axes)
    
        return Histogram.from_parent(parent, key, self.o.transform(tf))

    @staticmethod
    def explode_slot_filler(multipletraverser, key):
        axis, bin = key.axis, key.bin
        #raise RuntimeError
        return multipletraverser.__parent__.__parent__["!range"][axis][bin][bin]
        
    class ExplodeSlotKey(object):
        """
        Give bins a pretty name whilst retaining the information needed to 
        re-apply the ranges.
        """
        def __init__(self, axis, bin, pretty_name):
            self.axis, self.bin, self.pretty_name = axis, bin, pretty_name
        
        @property
        def tup(self): return self.axis, self.bin, self.pretty_name
        def __eq__(self, rhs): return self.tup == rhs.tup
        def __lt__(self, rhs): return self.pretty_name < rhs.pretty_name
        def __hash__(self): return hash(self.tup)
        def __str__(self): return self.pretty_name
        def __repr__(self): return repr(self.pretty_name)
    
    @action
    def explode(self, parent, key, ax):
        """
        TH{2,3}/!explode/axis
        Returns many histograms, one per bin in axis `ax`, with the range configured.
        """
        assert ax in "xyz"

        axis = get_haxis(self.obj, ax)

        def build_bin(i):
            r = self["!range"][ax][i][i]
            s = "bin {0:03d}: [{1}, {2}) {3}"
            lo = axis.GetBinLowEdge(i) if i else "-inf"
            up = axis.GetBinUpEdge(i) if i != axis.GetNbins()+1 else "+inf"
            s = s.format(i, lo, up, axis.GetTitle())
            return ((self.ExplodeSlotKey(ax, i, s),), r)

        new_contexts = [build_bin(i) for i in xrange(1, axis.GetNbins()+1)]
        
        return MultipleTraverser.from_parent(parent, ax, new_contexts, 
            slot_filler=self.explode_slot_filler)
    
    @action
    def normaxis(self, parent, key, axes):
        """
        TH2/!normaxis/axis
        Normalize 2D histogram in bins of an axis
        """
        if "".join(sorted(axes)) not in ("x", "y"):
            #raise HTTPMethodNotAllowed("Bad parameter '{0}', expected x or y axis".format(axes))
            return
            
        def tf(h):

            h = normalize_by_axis(self.obj, axes == "x")
            return h

        return Histogram.from_parent(parent, key, self.o.transform(tf))

    @action
    def normalize(self, parent, key, target_integral):
        """
        TH{1,2,3}/!normalize/[float target_integral]/
        Normalize histogram to `target_integral`
        """

        def tf(h):
            h = self.obj.Clone()
            h.Scale(float(target_integral)/h.Integral())
            return h

        return Histogram.from_parent(parent, key, self.o.transform(tf))
    
    @property
    def content(self):
        return ['<p><img class="plot" src="{0}" /></p>'.format(self.sub_url(query={"render":None, "resolution":70}))]
        
class FreqHist(Histogram):
    def __init__(self, request, root_object):
        from cPickle import loads
        freqs = loads(root_object.ReadObj().GetString().Data())
        total = sum(freqs.values())
        n = len(freqs)
                
        root_object = R.TH1D("frequencies", "frequencies;frequencies;%", n, 0, n)
        
        from yaml import load
        # TODO(pwaller): use resource string
        pdgs = load(open("pdg.yaml"))
        
        for i, (pdgid, value) in enumerate(sorted(freqs.iteritems(), key=lambda (k, v): v, reverse=True), 1):
            root_object.SetBinContent(i, value)
            root_object.SetBinError(i, value**0.5)
            root_object.GetXaxis().SetBinLabel(i, pdgs.get(pdgid, "?"))
            
        root_object.GetXaxis().SetLabelSize(0.02)
    
        root_object.Scale(100. / total)
        super(FreqHist, self).__init__(request, root_object)
