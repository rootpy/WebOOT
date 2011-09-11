import ROOT as R

from .object import RootObject

class DrawTTree(RootObject):
    def __getitem__(self, what):
        t = self.obj
        #h = R.TH1F("histo", "histo", 100, 0, 200000)
        #R.gDirectory.cd("Rint:/")
        #h.SetDirectory(R.gDirectory)
        drawn = t.Draw("{0} >> histo".format(what), "1", "goff")
        #h.SetDirectory(None)
        #print "DRAWN:", drawn
        h = R.gDirectory.Get("histo")
        #raise
        #raise
        return RootObject.from_parent(self, what, h)

