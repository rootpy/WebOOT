import ROOT as R

from rootpy.memory.keepalive import keepalive

from pyramid.location import lineage

from .actions import action
from .locationaware import LocationAware
from .renderable import Renderable, Renderer, RootRenderer

from weboot import log
log = log.getChild("combination")

etabins = [0, 0.6, 0.8, 1.15, 1.37, 1.52, 1.81, 2.01, 2.37, 2.47]

cuts = {
    "DeltaE": [92, 92, 99, 111, -9999., 92, 110, 148, -9999.],
    #"E233" : None,
    #"E237" : None,
    #"E277" : [0.1],
    #"Emax2" : None, # Not used
    #"Emaxs1" : None,# Not used
    #"Emins1" : None,# Not used
    "Eratio": [0.63, 0.84, 0.823, 0.887, 9999., 0.88, 0.710, 0.780, 9999.],

    #"Ethad" : None,# Not used
    #"Ethad1" : None,# Not used

    "Rhad": [0.0089, 0.007, 0.006, 0.008, -9999., 0.019, 0.015, 0.0137, -9999.],
    "Rhad1": [0.0089, 0.007, 0.006, 0.008, -9999., 0.019, 0.015, 0.0137, -9999.],

    # Unused in current lowlumi_photons menu
    #"deltaEmax2" : None,
    #"deltaEs" : None,

    #"f1" : [0.005],
    #"f1core" : None,
    #"f3core" : None,

    "fside": [0.284, 0.36, 0.36, 0.514, -9999., 0.67, 0.211, 0.181, -9999.],
    "reta": [0.950784, 0.9398, 0.9418, 0.9458, 9999., 0.932066, 0.928, 0.924, 9999.],
    "rphi": [0.954, 0.95, 0.59, 0.82, 9999., 0.93, 0.947, 0.935, 9999.],
    "weta2": [0.0107194, 0.011459, 0.010759, 0.011359, -9999., 0.0114125, 0.0110, 0.0125, -9999.],
    "ws3": [0.66, 0.69, 0.697, 0.81, -9999., 0.73, 0.651, 0.610, -9999.],
    "wstot": [2.95, 4.4, 3.26, 3.4, -9999., 3.8, 2.4, 1.64, -9999.],
}


def get_legend(data=[], signal=[], mc=[], mc_sum=None):
    llen = 1 + len(data) + len(mc) + len(signal)
    mtop, mright, width, hinc = 0.10, 0.25, 0.20, 0.01
    x1, y1 = 1.0 - mright - width, 1.0 - mtop
    x2, y2 = 1.0 - mtop, 1.0 - mright - hinc * llen
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
    if not mc_sum is None:
        # omit this entry for 2D histogram
        legend.AddEntry(mc_sum, name(mc_sum), "flp")
    for h in mc:  # sorted by initial XS
        legend.AddEntry(h, name(h), "f")
    for s in signal:
        legend.AddEntry(s, name(s), "l")
    return legend


def get_lumi_label(lumi="1.02", unit="fb", energy="7 TeV"):
    x, y = 0.15, 0.75
    n = R.TLatex()
    n.SetNDC()
    n.SetTextFont(32)
    n.SetTextColor(R.kBlack)
    n.DrawLatex(x, y, "#sqrt{s} = %s, #intL dt ~ %s %s^{-1}" % (energy, lumi, unit))
    return n


def create_mc_sum(mc_list):
    if not mc_list:
        return None, None
    mc_sum = mc_list[0].Clone("mc_sum")
    mc_sum.SetDirectory(0)
    for h in mc_list[1:]:
        for b in xrange(1, h.GetXaxis().GetNbins() + 1):
            # If there is negative weight in one channel, it should not
            # be subtracted from other channels
            if not (0 < h.GetBinContent(b)):
                h.SetBinContent(b, 0.0)
            # Sometimes negative Errors occur - they play havoc with the
            # Display of error bands...
            if not (0 < h.GetBinError(b)):
                h.SetBinError(b, 0.0)
        mc_sum.Add(h)
    for b in xrange(1, mc_sum.GetXaxis().GetNbins() + 1):
        # Sometimes negative Errors occur - they play havoc with the
        # Display of error bands...
        if not (0 < mc_sum.GetBinError(b)):
            h.SetBinError(b, 0.0)

    mc_sum.SetMarkerSize(0)
    mc_sum.SetLineColor(R.kRed)
    mc_sum_line = mc_sum.Clone("mc_sum_line")
    mc_sum_line.SetDirectory(0)
    mc_sum_line.SetFillStyle(0)
    mc_sum_line.SetFillColor(R.kWhite)
    mc_sum_line.SetFillStyle(0)
    mc_sum.SetFillColor(R.kOrange)
    mc_sum.SetFillStyle(3006)
    mc_sum.SetTitle("SM (stat)")
    return mc_sum_line, mc_sum

# NB: [ATLAS Preliminary label for when plots are approved only:


def preliminary(approved=False):
    # x, y = 0.21, 0.65
    x, y = 0.15, 0.85
    l = R.TLatex()
    l.SetNDC()
    l.SetTextFont(42)
    l.SetTextColor(R.kBlack)
    if approved:
        l.DrawLatex(x, y, "#bf{#it{ATLAS preliminary}}")
    else:
        l.DrawLatex(x, y, "#bf{#it{ATLAS work in progress}}")
    return l


class CombinationStackRenderer(RootRenderer):

    # This is a Hack
    @action
    def slot(self, parent, key, name):
        params = {"slot": name}
        params.update(self.params)
        args = parent, key, self.resource_to_render, self.format, params
        return self.from_parent(*args)

    def render(self, canvas):

        params = self.request.params
        names, histograms = zip(*self.resource_to_render.stack)
        # print "Rendering stack with {0} histograms".format(len(histograms))

        names = [n for n in names]
        histograms = [h for h in histograms]
        objs = [h.obj for h in histograms]

        if "sum" in params:

            hsum = objs[0].Clone("sum")
            keepalive(canvas, hsum)
            hsum.SetTitle("sum")

            for h in objs[1:]:
                hsum.Add(h)

            names.append("sum")
            objs.append(hsum)

        colordict = {
            "all": R.kBlue,
            "signal": R.kGreen,
            "fake": R.kRed,
        }

        for name, obj, col in zip(names, objs, [R.kBlue, R.kRed, R.kGreen, R.kViolet, R.kAzure + 6, R.kOrange]):
            col = col + 1
            # obj.SetTitle(""); obj.SetStats(False)
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
        min_value = min(o.GetMinimum() for o in objs)

        if min_value != objs[0].GetMinimum():
            old_minvalue = min_value
            # Apply a correction to include a bit more than just the lower bound
            min_value = min_value - (max_value - min_value) * 0.1
            # If this takes us below zero but the old minimum value was close
            # to zero, just use zero.
            if min_value < 0 and abs(old_minvalue) < 1e-8:
                min_value = 0

        obj = objs[0]  # .pop(0)
        from root.histogram import build_draw_params
        dp = "hist e0x0"  # build_draw_params(obj, self.request.params, True)

        obj.Draw(dp)
        obj.SetMaximum(max_value)
        # obj.SetMinimum(0)

        for obj in objs[1:]:
            obj.Draw(dp + " same")

        logy = canvas.GetLogy()
        canvas.SetLogy(False)
        canvas.Update()
        canvas_yrange = ymin, ymax = canvas.GetUymin(), canvas.GetUymax()
        canvas.SetLogy(logy)
        canvas.Update()

        def line(x, yrange):
            ymin, ymax = yrange
            args = x, ymin, x, ymax
            l = R.TLine(*args)
            l.SetLineWidth(3)
            l.SetLineStyle(2)
            l.Draw()
            keepalive(canvas, l)

        # Draw cuts
        slot = self.request.params.get("slot", None)
        if not slot:
            # Determine slot from path
            for p in lineage(self):
                if p.__name__ in cuts:
                    slot = p.__name__

        if slot:
            for x, yrange in zip(cuts[slot], zip(etabins, etabins[1:])):
                if canvas.GetUxmin() < x < canvas.GetUxmax():
                    line(x, canvas_yrange if obj.GetDimension() != 2 else yrange)

        if self.request.params.get("legend", None) is not None:
            log.debug("Drawing legend: {0}".format(objs))
            for n, o in zip(names, objs):
                o.SetTitle(n)
            legend = get_legend(mc=objs)
            legend.Draw()

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

    def render(self, canvas):

        params = self.request.params
        names, histograms = zip(*self.resource_to_render.stack)
        # print "Rendering stack with {0} histograms".format(len(histograms))

        objs = [h.obj for h in histograms]

        colordict = {
            "all": R.kBlue,
            "signal": R.kGreen,
            "fake": R.kRed,
        }

        from ROOT import kAzure, kBlue, kWhite, kRed, kBlack, kGray, kGreen, kYellow, kTeal, kCyan, kMagenta, kSpring
        clrs = [kWhite, kGreen, kYellow, kBlue, kCyan, kMagenta, kBlack, kGray, kRed, kAzure]

        mc = []
        signals = []
        data = []
        name_of = {}

        def is_data(h, name):
            # log.info("Got histogram: {0} - {1}".format(h.GetName(), name))
            # return h.GetTitle().lower().startswith("data")
            return "data" in name

        def is_signal(h):
            return h.GetTitle().lower().startswith("higgs")

        for name, obj in zip(names, objs):
            name_of[obj] = name
            obj.SetStats(False)
            if not obj.GetTitle():
                obj.SetTitle(name.replace(".root", ""))
            if is_data(obj, name):
                data.append(obj)
            elif is_signal(obj):
                signals.append(obj)
            else:
                mc.append(obj)

            # obj.SetFillStyle(1001)

        for h in data:
            h.SetMarkerStyle(20)
            h.SetMarkerSize(1.2)
            h.SetFillStyle(0)

        mc.sort(key=lambda h: h.GetMaximum())
        for h, col in zip(reversed(mc), clrs):
            if name_of[h] in colordict:
                col = colordict[name_of[h]]
            log.warning("Giving %s the color %s" % (name_of[h], col))
            h.SetMarkerColor(col)
            h.SetLineColor(R.kBlack)
            h.SetLineWidth(2)
            h.SetFillColor(col)
            h.SetFillStyle(1001)

        for h, col in zip(reversed(signals), (R.kRed, R.kBlue, R.kGreen)):
            h.SetLineColor(col)
            h.SetLineWidth(2)
            h.SetLineStyle(2)

        # get min/max
        ymax = sum(h.GetMaximum() for h in mc)
        ymin = sum(h.GetMinimum() for h in mc)
        if data or signals:
            ymax = max(ymax, max(h.GetMaximum() for h in data + signals))
            ymin = min(ymin, min(h.GetMinimum() for h in data + signals))
        ymax += 1
        ymax *= (1.5 if not canvas.GetLogy() else 120)
        ymin = max(5e-1, ymin)

        # Create Stack of MC
        mcstack = R.THStack()
        for h in mc:
            mcstack.Add(h)
        keepalive(canvas, mcstack)

        axis = None
        mc_sum_line, mc_sum_error = None, None
        if mc:
            axis = mcstack
            mcstack.Draw("Hist")
            mc_sum_line, mc_sum_error = create_mc_sum(mc)
            keepalive(canvas, mc_sum_line)
            keepalive(canvas, mc_sum_error)

        for signal in signals:
            if mc:
                signal.Add(mc_sum_line)
            if not axis:
                axis = signal
                signal.Draw("hist")
            else:
                signal.Draw("hist same")

        if mc:
            mc_sum_error.Draw("e2same")
            mc_sum_line.Draw("hist same")

        for d in data:
            if not axis:
                axis = d
                d.Draw("pe")
            else:
                d.Draw("pe same")

        axis.SetMaximum(ymax)
        axis.SetMinimum(ymin)
        axis.GetXaxis().SetRange(objs[0].GetXaxis().GetFirst(), objs[0].GetXaxis().GetLast())
        axis.GetXaxis().SetTitle(objs[0].GetXaxis().GetTitle())
        if not self.request.params.get("xlabel", None) is None:
            axis.GetXaxis().SetTitle(self.request.params["xlabel"])
        if not self.request.params.get("ylabel", None) is None:
            axis.GetYaxis().SetTitle(self.request.params["ylabel"])

        logy = canvas.GetLogy()
        canvas.SetLogy(False)
        canvas.Update()
        ymin, ymax = canvas.GetUymin(), canvas.GetUymax()
        canvas.SetLogy(logy)
        canvas.Update()

        def line(x):
            args = x, ymin, x, ymax
            l = R.TLine(*args)
            l.SetLineWidth(1)
            l.SetLineStyle(2)
            l.Draw()
            keepalive(canvas, l)

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
            legend = get_legend(mc=mc, data=data, signal=signals, mc_sum=mc_sum_error)
            legend.Draw()

        if not self.request.params.get("lumi", None) is None:
            label = get_lumi_label(lumi=self.request.params["lumi"])
            label.Draw()

        p = preliminary()
        p.Draw("hist e0x0")

        return

        if "unit_fixup" in params:
            h = fixup_hist_units(h)

        if "nostat" in params:
            h.SetStats(False)

        if "notitle" in params:
            h.SetTitle("")

        # TODO(pwaller): bring back draw options
        h.Draw("hist e0x0")


class CombinationDualRenderer(RootRenderer):
    def render(self, canvas):

        params = self.request.params
        names, histograms = zip(*self.resource_to_render.stack)
        assert len(names) == 2

        objs = [h.obj for h in histograms]

        h1, h2 = objs

        p1 = R.TPad("pad", "", 0, 0, 1, 1)
        keepalive(canvas, p1)
        p1.Draw()
        p1.cd()

        h1.SetLineColor(R.kGreen)
        h1.Draw()
        # return

        p2 = R.TPad("overlay", "", 0, 0, 1, 1)
        keepalive(canvas, p2)
        p2.SetFillStyle(4000)
        p2.SetFrameFillStyle(4000)
        p2.Draw()
        p2.cd()
        h2.SetLineColor(R.kRed)
        h2.Draw("Y+")


class CombinationEffRenderer(RootRenderer):
    def render(self, canvas):

        params = self.request.params
        names, histograms = zip(*self.resource_to_render.stack)
        assert len(names) == 2

        h1, h2 = sorted([h.obj for h in histograms], key=lambda x: x.GetEntries())

        eff = R.TEfficiency(h1, h2)
        keepalive(canvas, eff)

        eff.SetFillColor(R.kRed)
        eff.Draw("AP")


class CombinationDiffRenderer(RootRenderer):
    def render(self, canvas):

        params = self.request.params
        names, histograms = zip(*self.resource_to_render.stack)
        assert len(names) == 2

        h1, h2 = [h.obj for h in histograms]

        h = h2.Clone()

        h.Add(h1, -1)
        h.Draw()


class CombinationDivRenderer(RootRenderer):
    def render(self, canvas):

        params = self.request.params

        print params

        names, histograms = zip(*self.resource_to_render.stack)
        assert len(names) == 2

        h1, h2 = [h.obj for h in histograms]

        h = h2.Clone()

        h.Divide(h, h1, 1, 1)
        h.Draw()


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

        # object_types =

        # print "Object types:", object_types

        # assert len(object_types) == 1, "Tried to combine objects of differen types?"
        # stack_type = object_types.pop()
        # if not issubclass(stack_type, Renderable):
            # print "Can't combine:", stack_type
            # raise NotImplementedError()
            # return

        # print "Combinable!", stack_type

        if self.composition_type == "stack":
            self.renderer = CombinationStackRenderer

        if self.composition_type == "dual":
            self.renderer = CombinationDualRenderer

        if self.composition_type == "ebke":
            self.renderer = EbkeCombinationStackRenderer

        if self.composition_type == "eff":
            self.renderer = CombinationEffRenderer

        if self.composition_type == "diff":
            self.renderer = CombinationDiffRenderer

        if self.composition_type == "div":
            self.renderer = CombinationDivRenderer

        log.debug("Using renderer: {0}".format(self.renderer))

    @property
    def object_types(self):
        return set(type(context) for name, context in self.stack)

    @property
    def _supported_formats(self):
        # hm, kludge.
        supported_sets = [c._supported_formats for n, c in self.stack]
        return reduce(set.union, supported_sets)

    @property
    def content(self):
        assert len(self.object_types) == 1
        print "Got combination:", self.url
        print "Got rendered:", self.rendered("png").url
        return ['<p><img class="plot" src="{0}?{1}" /></p>'.format(self.rendered("png").url, self.request.environ.get("QUERY_STRING", ""))]

    def keys(self):
        if any(hasattr(t, "keys") for t in self.object_types):
            keys = [set(x.keys()) for n, x in self.stack if hasattr(x, "keys")]
            result = reduce(set.union, keys, set())
            return result
        return []
        # if all(hasattr(
        # return sorted(name for name, context in self.stack)

    def __iter__(self):
        return iter(self.keys())

    def __getitem__(self, key):

        if not isinstance(key, basestring):
            key = str(key)

        if "*" in key:
            from .multitraverser import MultipleTraverser
            return MultipleTraverser.from_listable(self, key)

        stack = [(n, c) for n, c in [(n, c[key]) for n, c in self.stack if c] if c]
        return self.from_parent(self, key, stack, self.composition_type)
