from itertools import groupby

from pyramid.httpexceptions import HTTPNotFound
from pyramid.traversal import traverse
from pyramid.url import static_url

from .locationaware import LocationAware
#from .root.stackplot import StackPlot

def flatten_contexts(table, parents=()):
    for name, element in table.contexts:
        if isinstance(element, MultipleTraverser):
            for sub in flatten_contexts(element, parents + (name,)):
                yield sub
        else:
            yield parents + (name, element)

class StackPlot(LocationAware):
    def __init__(self, request, plots):
        super(StackPlot, self).__init__(request)
        self.plots = plots

    @property
    def content(self):
        return ['<p><img class="plot" src="{0}" /></p>'.format(self.sub_url(query={"render":None, "resolution":70}))]

    def __getitem__(self, argument):
        return

class Transposer(LocationAware):
    """
    Records how a MultipleTraverser has been transposed
    """
    def __init__(self, request, traverser):
        super(Transposer, self).__init__(request)
        self.traverser = traverser

    def __getitem__(self, argument):
        # TODO(pwaller): argument validation, maybe a function call
        traverser.transposition = argument
        return traverser

class Composer(LocationAware):
    def __init__(self, request, traverser):
        super(Composer, self).__init__(request)
        self.traverser = traverser

    def __getitem__(self, argument):
        if argument == "stack":
            plots = self.traverser.flattened
            if len(plots[0]) == 2:
                return StackPlot.from_parent(self, argument, plots)
            nth = lambda x: x[-2]
            contexts = []
            p = MultipleTraverser.from_parent(self, argument, contexts)
            for key, elements in groupby(plots, nth):
                contexts.append((key, StackPlot.from_parent(p, key, list(elements))))
            return p
            #raise RuntimeError
            
            #return StackPlot.from_parent(self, argument, plots_by_nth)

class MultipleTraverser(LocationAware):
    def __init__(self, request, contexts):
        self.request = request
        self.contexts = contexts
        self.transposition = None
    
    @property
    def path(self):
        # TODO(pwaller): Fix/delete me
        return "MultipleTraverser"
    
    @property
    def content(self):
        # TODO(pwaller): Fix/delete me
        return "Hello! I have some contexts.."
        
    @property
    def flattened(self):
        flat = list(flatten_contexts(self))
        # TODO(pwaller): apply transpose
        return flat
    
    def __getitem__(self, subpath):
        if subpath == "!transpose":
            return Transposer.from_parent(self, subpath, self)
        
        elif subpath == "!compose":
            return Composer.from_parent(self, subpath, self)
        
        new_contexts = [(f, traverse(c, subpath)["context"])
                        for f, c in self.contexts]
                        
        if all(x is None for f, x in new_contexts):
            raise HTTPNotFound("Failed to traverse at {0}".format(subpath))
        
        # Filter out bad contexts    
        new_contexts = [(f, c) for f, c in new_contexts if c]
        
        return MultipleTraverser.from_parent(self, subpath, new_contexts)
