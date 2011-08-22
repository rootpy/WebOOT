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
            a = xa.GetBinLabel(i), int(h[i]), h[i] / prev if prev else 0
            prev = h[i]
            content.append('<tr><td>{0}</td><td style="text-align:right; font-family: monospace">{1}</td><td style="text-align: right;">{2:.3%}</td></tr>'.format(*a))
        content.append("</table>")
        content.append('<div style="float:right;"><img src="../?render&resolution=50&logy" /></div><div style="clear:both;"></div>')
        return content

def get_haxis(h, ax):
    return getattr(h, "Get{0}axis".format(ax.upper()))()

def get_xyz_func(obj, func, ax):
    return getattr(obj, func.format(ax=ax.upper()))

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

class Projector(RootObject):
    def __getitem__(self, what):
        if "".join(sorted(what)) not in ("x", "y", "z", "xy", "xz", "yz"):
            raise HTTPMethodNotAllowed("Bad parameter '{0}', expected axes".format(what))
        return RootObject.from_parent(self, what, self.obj.Project3D(what))
        
class Profiler(RootObject):
    def __getitem__(self, what):
        if "".join(sorted(what)) not in ("x", "y", "z", "xy", "xz", "yz"):
            raise HTTPMethodNotAllowed("Bad parameter '{0}', expected axes".format(what))
        if self.obj.GetDimension() == 2 and len(what) == 1:
            profile_hist = get_xyz_func(self.obj, "Profile{ax}", what)()
            return RootObject.from_parent(self, what, profile_hist)
        if len(what) == 2:
            return RootObject.from_parent(self, what, self.obj.Project3DProfile(what))
        return RootObject.from_parent(self, what, self.obj.Project3DProfile(what))

class Ranger(RootObject):
    def __getitem__(self, what):
        ax, lo, hi = what.split("!")
        h = self.obj.Clone()
        get_haxis(h, ax).SetRange(int(lo), int(hi))
        return RootObject.from_parent(self, what, h)

