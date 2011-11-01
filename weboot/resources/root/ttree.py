from weboot import log; log = log.getChild("weboot.resources.root.ttree")

import ROOT as R

from .object import RootObject

def extract_buffer(b, n):
    return [b[i] for i in xrange(n)]

@log.trace()
def draw_ttree(t, params, what):
    
    #test_entries = 1000
    #every_n_events = t.GetEntries() // test_entries
    #selection = "Entry$ % {0} == 0".format(every_n_events)
    
    drawn = t.Draw(what, "1", "goff") #, test_entries)
    
    h = t.GetHistogram()
    
    log.info("Drawn {0} with {1} entries".format(what, drawn))
    
    return h

class DrawTTree(RootObject):
    @property
    def content(self):
        keys = [k.GetName() for k in self.obj.GetListOfLeaves()]
        def link(p):
            url = self.request.resource_url(self, p)
            return '<p><a href="{0}">{1}</a><img src="{0}/render?resolution=25&hist" height="10%"/></p>'.format(url, p)
        return "".join(link(p) for p in keys)
        
    @property
    def items(self):
        keys = [self[k.GetName()] for k in self.obj.GetListOfLeaves()]
        keys = [k for k in keys if k]
        keys.sort(key=lambda k: k.name)
        return keys
        
    def __getitem__(self, what):
        t = self.obj
        
        h = draw_ttree(t, self.request.params, what)
        #numbers = extract_buffer(t.GetV1(), n)
        #xmin, xmax = 
        
        #hist = R.TH1D("variable", "variable", 200, xmin, xmax)
        
        #drawn = t.Draw(what, selection, "goff", test_entries)
        
        return RootObject.from_parent(self, what, h)

