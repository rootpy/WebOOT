import re

from array import array


def fixup_hist_units(orig_hist):
    hist = orig_hist
    if "[MeV]" in orig_hist.GetXaxis().GetTitle():
        hist = histaxes_mev_to_gev(orig_hist)
    hist = meaningful_yaxis(hist)
    # else:
        #
    return hist

unit_re = re.compile(r"(\[[^\]]+\])")


def meaningful_yaxis(orig_hist):
    hist = orig_hist.Clone()
    x_title = orig_hist.GetXaxis().GetTitle()
    y_title = orig_hist.GetYaxis().GetTitle()
    if not y_title:
        y_title = "N"
    x_units = unit_re.search(x_title)
    if x_units:

        # if not x_units: return hist
        # assert x_units, "Couldn't find unit on x-axis: %s" % x_title
        xunit = x_units.groups()[0]
        if xunit not in hist.GetYaxis().GetTitle():
            hist.Scale(1, "width")
            hist.GetYaxis().SetTitle("%s / %s" % (y_title, xunit))
    elif hist.GetXaxis().IsVariableBinSize():
        hist.Scale(1, "width")
        hist.GetYaxis().SetTitle("%s / (unit %s)" % (y_title, hist.GetXaxis().GetTitle()))

    else:
        assert not hist.GetXaxis().IsVariableBinSize(), "Doesn't make sense.."
        hist.Scale(1, "width")
        hist.GetYaxis().SetTitle("%s / %.3f" % (y_title, hist.GetXaxis().GetBinWidth(1)))
    return hist


def histaxes_mev_to_gev(orig_hist):
    """
    If an axis contains "[MeV]" in its title, rescale it to GeV and
    update the title.
    """
    hist = orig_hist.Clone()
    for axis in (hist.GetXaxis(), hist.GetYaxis()):
        if "[MeV]" in axis.GetTitle():
            axis.SetTitle(axis.GetTitle().replace("[MeV]", "[GeV]"))
            scale_axis(axis, 1e-3)

    return hist


def get_bin_positions(axis):
    bins = axis.GetXbins()
    if bins.fN:
        return [bins[i] for i in xrange(bins.fN)]
    xn, xmin, xmax = axis.GetNbins(), axis.GetXmin(), axis.GetXmax()
    bwidth = (xmax - xmin) / xn
    return [xmin + bwidth * i for i in xrange(xn)] + [xmax]


def scale_axis(axis, scale):
    bins = get_bin_positions(axis)
    new_bins = array("d", (bin * scale for bin in bins))
    axis.Set(axis.GetNbins(), new_bins)


def normalize_by_axis(orig_hist, xaxis=True):
    """
    Normalise rows or columns of a 2D histogram
    xaxis = True => normalize Y bins in each X bin to the sum of the X bin.
    """
    hist = orig_hist.Clone()

    if xaxis:
        Project, axis = hist.ProjectionY, hist.GetXaxis()
    else:
        Project, axis = hist.ProjectionX, hist.GetYaxis()

    for bin in xrange(0, axis.GetNbins() + 2):

        # Note: this gets garbage collected if _creates is set on the funciton
        # object (as it is in init_root)
        proj = Project("slice", bin, bin)
        integral = proj.Integral()
        if integral:
            proj.Scale(1. / integral)

        # Insert slice
        insert_slice(proj, hist, bin, not xaxis)

    return hist


def insert_slice(hist, into, slice_bin, xaxis=True):
    """
    Insert a 1D histogram `hist` into a row or column of a 2D histogram `into`
    """
    if xaxis:
        for bin in xrange(0, hist.GetNbinsX() + 2):
            into.SetBinContent(bin, slice_bin, hist.GetBinContent(bin))

    else:
        for bin in xrange(0, hist.GetNbinsX() + 2):
            into.SetBinContent(slice_bin, bin, hist.GetBinContent(bin))
