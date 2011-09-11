
from pyramid.httpexceptions import HTTPNotFound
from pyramid.traversal import traverse
from pyramid.url import static_url

from .locationaware import LocationAware


class MultipleTraverser(LocationAware):
    def __init__(self, request, contexts):
        self.request = request
        self.contexts = contexts
    
    @property
    def path(self):
        return "MultipleTraverser"
    
    @property
    def content(self):
        return "Hello! I have some contexts.."
    
    def __getitem__(self, subpath):
        print "Attempting to traverse {0} contexts at {1}".format(len(self.contexts), subpath)
        new_contexts = [(f, traverse(c, subpath)["context"])
                        for f, c in self.contexts]
        if all(x is None for f, x in new_contexts):
            raise HTTPNotFound("Failed to traverse at {0}".format(subpath))
        new_contexts = [(f, r) for f, r in new_contexts if r]
        return MultipleTraverser.from_parent(self, subpath, new_contexts)
