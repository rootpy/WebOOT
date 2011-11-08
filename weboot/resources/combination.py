import ROOT as R

from .locationaware import LocationAware
from .renderable import Renderable, Renderer

class CombinationStackRenderer(Renderer):
    def render(self, canvas, keep_alive):
        
        params = self.request.params
        names, histograms = zip(*self.resource_to_render.stack)
        print "Rendering stack with {0} histograms".format(len(histograms))
        
        objs = [h.obj for h in histograms]
        
        for obj, col in zip(objs, [R.kBlue, R.kRed, R.kGreen, R.kBlack, R.kBlack, R.kBlack]):
            obj.SetLineColor(col)
            obj.SetLineWidth(2)
        
        if "shape" in params:
            for obj in objs:
                obj.Scale(1. / obj.Integral())
        
        max_value = max(o.GetMaximum() for o in objs) * 1.1
        
        
        obj = objs.pop(0)
        obj.Draw("hist")
        obj.SetMaximum(max_value)
        obj.SetMinimum(0)
        
        for obj in objs:
            obj.Draw("hist same")
            
        return
        
        if "unit_fixup" in params:
            h = fixup_hist_units(h)
        
        if "nostat" in params:
            h.SetStats(False)
        
        if "notitle" in params:
            h.SetTitle("")
        
        # TODO(pwaller): bring back draw options
        h.Draw()
        
class CombinationDualRenderer(Renderer):
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
    
class Combination(LocationAware, Renderable):
    renderer = CombinationStackRenderer
    
    def __init__(self, request, stack, composition_type):
        super(Combination, self).__init__(request)
        self.stack = stack
        self.composition_type = composition_type
        
        if self.composition_type == "dual":
            self.renderer = CombinationDualRenderer
    
    @property
    def content(self):
        return ['<p><img class="plot" src="{0}" /></p>'.format(self.rendered("png").url)]
