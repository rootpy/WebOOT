
from weboot.utils.thousands import split_thousands
from weboot.utils.histogram import normalize_by_axis

from weboot.resources.multitraverser import MultipleTraverser
from ..object import RootObject

class HistogramRebinned(RootObject):
    def __getitem__(self, what):
        h = self.obj.Clone()
        h = h.Rebin(int(what))
        return RootObject.from_parent(self, what, h)

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
            content.append('<img src="../../!range/{slice_ax}!{0}!{0}/!project/{proj_ax}/?render" />'.format(i, slice_ax=a2, proj_ax=a1))
        return content

    def __getitem__(self, what):
        if self.axinfo: 
            # Already got axis information, forget about it.
            return
        axinfo = what.split("!")
        return MultiProjector.from_parent(self, what, self.obj, axinfo)

class Exploder(RootObject):

    def __getitem__(self, ax):
        assert ax in "xyz"

        axis = get_haxis(self.obj, ax)

        def build_bin(i):
            r = Ranger.from_parent(self.__parent__, "!range", self.obj)
            r = r["{0}!{1}!{1}".format(ax, i)]
            s = "bin {0:03d}: [{1}, {2}) {3}"
            lo = axis.GetBinLowEdge(i) if i else "-inf"
            up = axis.GetBinUpEdge(i) if i != axis.GetNbins()+1 else "+inf"
            s = s.format(i, lo, up, axis.GetTitle())
            return s, r

        new_contexts = [build_bin(i) for i in xrange(1, axis.GetNbins())]
        
        return MultipleTraverser.from_parent(self, ax, new_contexts)

class Projector(RootObject):
    def __getitem__(self, what):
        if "".join(sorted(what)) not in ("x", "y", "z", "xy", "xz", "yz"):
            raise HTTPMethodNotAllowed("Bad parameter '{0}', expected axes".format(what))
        if self.obj.GetDimension() == 2 and len(what) == 1:
            projected_hist = get_xyz_func(self.obj, "Projection{ax}", what)()
            return RootObject.from_parent(self, what, projected_hist)
        
        # Thread safety, histograms are named by anything which remains in the 
        # option string, and they clobber each other, yay ROOT!
        
        from random import randint
        random_name = str(randint(0, 2**32-1))
        optstring = "{0}{1}".format(what, random_name)
        h = self.obj.Project3D(optstring)
        h.SetName(h.GetName()[:-len(random_name)])
        return RootObject.from_parent(self, what, h)
        
class Profiler(RootObject):
    def __getitem__(self, what):
        if "".join(sorted(what)) not in ("x", "y", "z", "xy", "xz", "yz"):
            raise HTTPMethodNotAllowed("Bad parameter '{0}', expected axes".format(what))
        if self.obj.GetDimension() == 2 and len(what) == 1:
            other_axis = "x"
            if what == "x": 
                other_axis = "y"
            ya = get_xyz_func(self.obj, "Get{ax}axis", other_axis)()
            new_hist = get_xyz_func(self.obj, "Profile{ax}", what)()
            new_hist.GetYaxis().SetTitle(ya.GetTitle())
            new_hist.SetTitle(self.obj.GetTitle())
            return RootObject.from_parent(self, what, new_hist)
        if len(what) == 2:
            new_hist = self.obj.Project3DProfile(what)
            xa = get_xyz_func(self.obj, "Get{ax}axis", what[0])()
            ya = get_xyz_func(self.obj, "Get{ax}axis", what[1])()
            new_hist.GetXaxis().SetTitle(xa.GetTitle())
            new_hist.GetYaxis().SetTitle(ya.GetTitle())
            return RootObject.from_parent(self, what, new_hist)
        return RootObject.from_parent(self, what, self.obj.Project3DProfile(what))

class Ranger(RootObject):
    def __getitem__(self, what):
        ax, lo, hi = what.split("!")
        h = self.obj.Clone()
        get_haxis(h, ax).SetRange(int(lo), int(hi))
        return RootObject.from_parent(self, what, h)

class NormalizeAxis(RootObject):
    def __getitem__(self, what):
        if "".join(sorted(what)) not in ("x", "y"):
            raise HTTPMethodNotAllowed("Bad parameter '{0}', expected x or y axis".format(what))
        h = normalize_by_axis(self.obj, what == "x")
        return RootObject.from_parent(self, what, h)
    
