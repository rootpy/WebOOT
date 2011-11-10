import ROOT as R

from pyramid.location import lineage

from .actions import action
from .locationaware import LocationAware
from .renderable import Renderable, Renderer, RootRenderer

from weboot import log; log = log.getChild("combination")

etabins = [0.6, 0.8, 1.15, 1.37, 1.52, 1.81, 2.01, 2.37, 2.47]

cuts = {
    "DeltaE" : [92,92,99,111,-9999.,92,110,148,-9999.],
    #"E233" : None,
    #"E237" : None,
    #"E277" : [0.1],
    #"Emax2" : None, # Not used
    #"Emaxs1" : None,# Not used
    #"Emins1" : None,# Not used
    "Eratio" : [0.63,0.84,0.823,0.887,9999.,0.88,0.710,0.780,9999.],
    
    #"Ethad" : None,# Not used
    #"Ethad1" : None,# Not used
    
    "Rhad"  : [0.0089,0.007,0.006,0.008,-9999.,0.019,0.015,0.0137,-9999.],
    "Rhad1" : [0.0089,0.007,0.006,0.008,-9999.,0.019,0.015,0.0137,-9999.],
    
    # Unused in current lowlumi_photons menu
    #"deltaEmax2" : None,
    #"deltaEs" : None,
    
    #"f1" : [0.005],
    #"f1core" : None,
    #"f3core" : None,
    
    "fside" : [0.284,     0.36,     0.36,0.514,-9999.,0.67,0.211,0.181,-9999.],
    "reta"  : [0.950784,  0.9398,   0.9418, 0.9458, 9999., 0.932066, 0.928, 0.924, 9999.],
    "rphi"  : [0.954,     0.95,     0.59,0.82,9999.,0.93,0.947,0.935,9999.],
    "weta2" : [0.0107194, 0.011459, 0.010759, 0.011359, -9999., 0.0114125, 0.0110, 0.0125, -9999.],
    "ws3"   : [0.66,      0.69,     0.697,0.81,-9999.,0.73,0.651,0.610,-9999.],
    "wstot" : [2.95,      4.4,      3.26,3.4,-9999.,3.8,2.4,1.64,-9999.],
}

def get_legend(data=[], signal=[], mc=[], sum_mc=None):
    llen = 1 + len(data) + len(mc) + len(signal)
    mtop, mright, width, hinc = 0.07, 0.25, 0.15, 0.01
    x1, y1 = 1.0 - mright - width, 1.0 - mtop
    x2, y2 = 1.0 - mtop, 1.0 - mright - hinc*llen
    print x1, y1, x2, y2
    legend = R.TLegend(x1, y1, x2, y2)
    legend.SetNColumns(2)
    legend.SetColumnSeparation(0.05)
    legend.SetBorderSize(0)
    legend.SetTextFont(42)
    legend.SetTextSize(0.04)
    legend.SetFillColor(0)
    legend.SetFillStyle(0)
    legend.SetLineColor(0)
    def name(h):
        return h.GetTitle()
    for d in data:
        legend.AddEntry(d, name(d), "p")
    if not sum_mc is None:
        # omit this entry for 2D histogram
        legend.AddEntry(sum_mc, name(sum_mc), "flp")
    for h in mc: # sorted by initial XS
        legend.AddEntry(h, name(h), "f")
    for s in signal:
       legend.AddEntry(s, name(s), "l")
    return legend

def get_lumi_label(lumi="1.02", unit="fb", energy="7 TeV"):
    x, y = 0.15, 0.75
    n = TLatex()
    n.SetNDC()
    n.SetTextFont(32)
    n.SetTextColor(kBlack)
    n.DrawLatex(x, y,"#sqrt{s} = %s, #intL dt ~ %s %s^{-1}" % (energy, lumi, unit))
    return n

class CombinationStackRenderer(RootRenderer):

    # This is a Hack
    @action
    def slot(self, parent, key, name):
        params = {"slot": name}
        params.update(self.params)
        args = parent, key, self.resource_to_render, self.format, params
        return self.from_parent(*args)
        
    def render(self, canvas, keep_alive):
        
        params = self.request.params
        names, histograms = zip(*self.resource_to_render.stack)
        #print "Rendering stack with {0} histograms".format(len(histograms))
        
        objs = [h.obj for h in histograms]
        
        colordict = {
            "all"   :R.kBlue,
            "signal":R.kGreen,
            "fake"  :R.kRed,
        }
        
        for name, obj, col in zip(names, objs, [R.kBlue, R.kRed, R.kGreen, R.kBlack, R.kBlack, R.kBlack]):
            obj.SetTitle(""); obj.SetStats(False)
            if name in colordict:
                obj.SetLineColor(colordict[name])
            else:
                obj.SetLineColor(col)
            obj.SetMarkerColor(col)
            obj.SetLineWidth(2)
        
        if "shape" in params:
            for obj in objs:
                if obj.Integral():
                    obj.Scale(1. / obj.Integral())
        
        max_value = max(o.GetMaximum() for o in objs) * 1.1
        
        
        obj = objs.pop(0)
        obj.Draw("")
        obj.SetMaximum(max_value)
        #obj.SetMinimum(0)
        
        for obj in objs:
            obj.Draw("same")
        
        logy = canvas.GetLogy()
        canvas.SetLogy(False)
        canvas.Update()
        ymin, ymax = canvas.GetUymin(), canvas.GetUymax()
        canvas.SetLogy(logy)
        canvas.Update()
        
        def line(x):
            args = x, ymin, x, ymax
            l = R.TLine(*args)
            l.SetLineWidth(1); l.SetLineStyle(2)
            l.Draw()
            keep_alive(l)
        
        # Draw cuts
        slot = self.request.params.get("slot", None)
        if not slot:
            # Determine slot from path
            for p in lineage(self):
                if p.__name__ in cuts:
                    slot = p.__name__
                    
        if slot:
            for x in set(cuts[slot]):
                if canvas.GetUxmin() < x < canvas.GetUxmax():
                    line(x)
        
        
        return
        
        if "unit_fixup" in params:
            h = fixup_hist_units(h)
        
        if "nostat" in params:
            h.SetStats(False)
        
        if "notitle" in params:
            h.SetTitle("")
        
        # TODO(pwaller): bring back draw options
        h.Draw()

class EbkeCombinationStackRenderer(RootRenderer):

    # This is a Hack
    @action
    def slot(self, parent, key, name):
        params = {"slot": name}
        params.update(self.params)
        args = parent, key, self.resource_to_render, self.format, params
        return self.from_parent(*args)
        
    def render(self, canvas, keep_alive):
        
        params = self.request.params
        names, histograms = zip(*self.resource_to_render.stack)
        #print "Rendering stack with {0} histograms".format(len(histograms))
        
        objs = [h.obj for h in histograms]


        colordict = {
            "all"   :R.kBlue,
            "signal":R.kGreen,
            "fake"  :R.kRed,
        }
        
        from ROOT import kAzure, kBlue, kWhite, kRed, kBlack, kGray, kGreen, kYellow, kTeal, kCyan, kMagenta, kSpring
        clrs = (kWhite, kRed, kBlack, kGray, kGreen, kYellow, kTeal, kCyan, kSpring, kBlue, kMagenta)

        for name, obj in zip(names, objs):
            #obj.SetTitle("");
            obj.SetStats(False)
            obj.SetLineWidth(2)

        for name, obj, col in zip(names, objs, clrs):
            if name in colordict:
                obj.SetLineColor(colordict[name])
            else:
                obj.SetLineColor(col)
            obj.SetMarkerColor(col)
        
        if "shape" in params:
            for obj in objs:
                if obj.Integral():
                    obj.Scale(1. / obj.Integral())
        
        max_value = max(o.GetMaximum() for o in objs) * 1.1


        obj = objs.pop(0)
        obj.Draw("")
        obj.SetMaximum(max_value)
        #obj.SetMinimum(0)
        
        for obj in objs:
            obj.Draw("same")
         


        logy = canvas.GetLogy()
        canvas.SetLogy(False)
        canvas.Update()
        ymin, ymax = canvas.GetUymin(), canvas.GetUymax()
        canvas.SetLogy(logy)
        canvas.Update()
        
        def line(x):
            args = x, ymin, x, ymax
            l = R.TLine(*args)
            l.SetLineWidth(1); l.SetLineStyle(2)
            l.Draw()
            keep_alive(l)
        
        # Draw cuts
        slot = self.request.params.get("slot", None)
        if not slot:
            # Determine slot from path
            for p in lineage(self):
                if p.__name__ in cuts:
                    slot = p.__name__
                    
        if slot:
            for x in set(cuts[slot]):
                if canvas.GetUxmin() < x < canvas.GetUxmax():
                    line(x)
        
        if not self.request.params.get("legend", None) is None:
            legend = get_legend(mc=objs)
            legend.Draw()
            keep_alive(legend)
        
        return
        
        if "unit_fixup" in params:
            h = fixup_hist_units(h)
        
        if "nostat" in params:
            h.SetStats(False)
        
        if "notitle" in params:
            h.SetTitle("")
        
        # TODO(pwaller): bring back draw options
        h.Draw()
        
class CombinationDualRenderer(RootRenderer):
    def render(self, canvas, keep_alive):
                
        params = self.request.params
        names, histograms = zip(*self.resource_to_render.stack)
        assert len(names) == 2
        
        objs = [h.obj for h in histograms]
        
        h1, h2 = objs
        
        p1 = R.TPad("pad", "", 0, 0, 1, 1); keep_alive(p1)
        p1.Draw()
        p1.cd()
        
        h1.SetLineColor(R.kGreen)
        h1.Draw()
        #return
        
        p2 = R.TPad("overlay", "", 0, 0, 1, 1); keep_alive(p2)
        p2.SetFillStyle(4000)
        p2.SetFrameFillStyle(4000)
        p2.Draw()
        p2.cd()
        h2.SetLineColor(R.kRed)
        h2.Draw("Y+")

class UnknownCombinationRenderer(Renderer):
    """
    Used to indicate that we don't know what to do with this combination
    """

class Combination(Renderable, LocationAware):
    renderer = UnknownCombinationRenderer
    
    def __init__(self, request, stack, composition_type):
        super(Combination, self).__init__(request)
        self.stack = stack
        self.composition_type = composition_type
        
        object_types = set(type(context) for name, context in self.stack)
        
        print "Object types:", object_types
        
        assert len(object_types) == 1, "Tried to combine objects of differen types?"
        stack_type = object_types.pop()
        if not issubclass(stack_type, Renderable):
            print "Can't combine:", stack_type
            #raise NotImplementedError()
            return
        
        print "Combinable!", stack_type
        
        if self.composition_type == "stack":
            self.renderer = CombinationStackRenderer

        if self.composition_type == "dual":
            self.renderer = CombinationDualRenderer

        if self.composition_type == "ebke":
            self.renderer = EbkeCombinationStackRenderer
            
        print "Using renderer:", self.renderer
    
    @property
    def _supported_formats(self):
        # hm, kludge.
        supported_sets = [c._supported_formats for n, c in self.stack]
        return reduce(set.union, supported_sets)
    
    @property
    def content(self):
        print "Got combination:", self.url
        print "Got rendered:", self.rendered("png").url
        return ['<p><img class="plot" src="{0}?{1}" /></p>'.format(self.rendered("png").url, self.request.environ.get("QUERY_STRING", ""))]
