from .. import log; log = log.getChild(__name__)

from collections import defaultdict
from pprint import pformat

import ROOT as R

from pyramid.location import lineage
from pyramid.response import Response

from weboot.resources.multitraverser import MultipleTraverser
from .root.canvas import render_canvas

from .breadcrumb import build_breadcrumbs

def get_missing_ordering(length, ordering):
    return ordering + tuple(x for x in xrange(length) if x not in ordering)

def rearrange_contexts(table, ordering=()):
    if not table:
        return table
    # Note, I want to filter out all but the longest match, probably 
    # (or shortest? or optional?)
    assert len(set(map(len, table))) == 1, "Unequal depths matched!"

    # Is there any possible utility to this?
    assert len(set(ordering)) == len(ordering), "Multiple axes specified repeatedly"

    # Build the complete ordering list
    #ordering = get_missing_ordering(len(table[0]), ordering)
    
    result = []
    for element in table:
        result.append([element[i] for i in ordering])
    
    return result
    
def dictize(table, depth=None):
    result = defaultdict(list)
    for element in table:
        result[element[0]].append(element[1:])
    for key, element in sorted(result.iteritems()):
        if not depth: # matches depth == 0 AND depth == None (!)
            element.sort()
        else:
            result[key] = dictize(element, depth - 1)
    return dict(result)

def fill_missing_pieces(result):
    
    total = set()
    nonplot_part_by_key = {}
    for key, table in result.iteritems():
        this = nonplot_part_by_key[key] = set()
        for element in table:
            nonplot_parts = tuple(element[:-1])
            this.add(nonplot_parts)
            total.add(nonplot_parts)
    
    #result = {}
    for key, values in result.iteritems():
        for el in total - nonplot_part_by_key[key]:
            values.append(list(el) + [None])  
        values.sort()


def build_plot_view(request, values):
    content = []
    
    for value in values:
        content.append("<pre>{0}</pre>".format(value[:-1]))
    
    for value in values:
        #content.append("<pre>{0}\n</pre>".format(value))
        if not value[-1]:
            content.append("<pre>N/A</pre>")
            continue
        content.append('<img class="plot" title="{0!r}" src="{1.icon_url}" />'.format(value[:-1], value[-1], request.query_string))
    return content

def find_nth(lst, what, n):
    assert n >= 0
    assert n < len(lst)
    pos = lst.index(what)
    for i in xrange(n):
        pos = lst.index(what, pos+1)
    return pos

def view_multitraverse(multitravese_context, request):
    content = []
    prev_idx = None
    for index_tuple, context in sorted(multitravese_context.indexed_contexts):
        print index_tuple, context.icon, context
        if not context.icon:
            # TODO(pwaller): If a context doesn't have an icon, we should
            #                 show something else, but I haven't decided what 
            #                 yet
            continue
        str_index_tuple = map(str, index_tuple)
        this_idx = str_index_tuple[0]
        if prev_idx != this_idx:
            content.append("<h2>{0}</h2>".format(this_idx))
        prev_idx = str_index_tuple[0]
        content.append('<img class="plot" src="{1.icon_url}?{2}" title="{0}" />'
                       .format(" / ".join(str_index_tuple), context, 
                       request.environ.get("QUERY_STRING", "")))
    
    return dict(path=build_breadcrumbs(multitravese_context),
                content="\n".join(content))
    """
    A = content.append
    
    #A(repr(context))
    
    def trav(c, depth=0):
        A((" "*depth) + repr(c))
        if isinstance(c, MultipleTraverser):
            for cc in c.contexts:
                trav(cc, depth+1)
        elif isinstance(c, tuple):
            name, c = c
            A((" "*depth) + name)
            trav(c, depth+1)
            
            
    trav(context)
    
    A("")
    A("")
    A("")
    
    for a, b in context.flattened:
        A(repr(a) + repr(b))
    
    return Response("\n".join(content), content_type="text/plain")
    return dict(path=build_breadcrumbs(context),
                content="\n".join(content))
    """
    
    result = context.flattened
    #raise RuntimeError("Yarg.")
    #return Response(pformat(result), content_type="text/plain")
    ordering = tuple(xrange(len(result[0])))
    if request.params.get("transpose"):
        ordering = tuple(map(int, request.params["transpose"].split(",")))
        ordering = get_missing_ordering(len(result[0]), ordering)
        result = rearrange_contexts(result, ordering)
    
    result = dictize(result)
    fill_missing_pieces(result)
    
    l = list(reversed(list(l.__name__ for l in lineage(context))))
    
        
    for name, value in sorted(result.iteritems()):
        #name = subcontext.name
        content.append("<p>{name}</p>".format(name=name))
        
        content.extend(build_plot_view(request, value))
        
        continue
        
        url = "https://hep.ph.liv.ac.uk/~pwaller/weboot"
        l1 = l[:]
        # 
        l1[find_nth(l1, "*", ordering[0])] = name
        #l1[l.index("*", l.index("*")+1)] = name
        
        url += "/".join(l1)
        
        content.append('<img class="plot" src="{0}?{1}" />'.format(url, request.query_string))
        
        
        """
        if isinstance(subcontext, MultipleTraverser):
            subcontent = []
            for subsubcontext in subcontext:
                subname = subsubcontext.name
                subcontent.append('<img class="plot" src="{0.url}?render&resolution=30&{1}" />'.format(subsubcontext, request.query_string))
            
            content.append('<p>{0}</p><div>{1}</div>'.format(name, "".join(subcontent)))
            continue
        
        content.append('<p>{0}</p><div><img class="plot" src="{1.url}?render&resolution=50&{2}" /></div>'.format(name, subcontext, request.query_string))
        """
    return dict(path=build_breadcrumbs(context),
                content="\n".join(content))

def view_multitraverse_render(context, request):
    content = "\n".join(str(fc.obj) for name, fc in context.contexts)
    with render_canvas() as c:
        if "logx" in request.params: c.SetLogx()
        if "logy" in request.params: c.SetLogy()
        if "logz" in request.params: c.SetLogz()
        
        objs = [fc.obj for name, fc in context.contexts]
        
        for obj, col in zip(objs, [R.kBlue, R.kRed, R.kGreen]):
            obj.SetLineColor(col)
            obj.SetLineWidth(2)
        
        if "shape" in request.params:
            #objs.pop(0)
            for obj in objs:
                obj.Scale(1. / obj.Integral())
                
        max_value = max(o.GetMaximum() for o in objs) * 1.1
        
        obj = objs.pop(0)
        #obj.GetXaxis().SetRangeUser(0, 100e3)
        obj.Draw("hist")
        obj.SetMaximum(max_value)
        
        for obj in objs:
            obj.Draw("hist same")
            
        return c._weboot_canvas_to_response()
            
    return Response("Hello, world" + content, content_type="text/plain")
