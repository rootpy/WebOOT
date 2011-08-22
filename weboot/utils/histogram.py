import re

def fixup_hist_units(orig_hist):
    if "[MeV]" in orig_hist.GetXaxis().GetTitle():
        hist = histaxes_mev_to_gev(orig_hist)
        hist = meaningful_yaxis(hist)
    else:
        hist = orig_hist
    return hist

unit_re = re.compile(r"(\[[^\]]+\])")
def meaningful_yaxis(orig_hist):
    hist = orig_hist.Clone()
    x_title = orig_hist.GetXaxis().GetTitle()
    y_title = orig_hist.GetYaxis().GetTitle()
    if not y_title:
        y_title = "N"
    x_units = unit_re.search(x_title)
    if not x_units: return hist
    assert x_units, "Couldn't find unit on x-axis: %s" % x_title
    xunit = x_units.groups()[0]
    if xunit not in hist.GetYaxis().GetTitle():
        hist.Scale(1, "width")
        hist.GetYaxis().SetTitle("%s / %s" % (y_title, xunit))
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
    return [xmin + bwidth*i for i in xrange(xn)] + [xmax]

def scale_axis(axis, scale):
    bins = get_bin_positions(axis)
    new_bins = array("d", (bin*scale for bin in bins))
    axis.Set(axis.GetNbins(), new_bins)

