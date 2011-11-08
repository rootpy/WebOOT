import ROOT as R

from weboot.resources.actions import action

from weboot.resources.root.object import RootObject

class Histogram(RootObject):
    def __init__(self, request, root_object):
        super(Histogram, self).__init__(request, root_object)
        
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
