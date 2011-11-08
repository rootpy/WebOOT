import fnmatch
import re

from itertools import groupby

from pyramid.httpexceptions import HTTPNotFound
from pyramid.location import lineage
from pyramid.traversal import traverse
from pyramid.url import static_url

from weboot.resources.actions import action
from weboot.resources.combination import Combination
from .locationaware import LocationAware
#from .root.stackplot import StackPlot



def transpose_fragments_fixup(fragments, to_fill):
    """
    Remove the slot `to_fill` from any "!transpose" operations in `fragments`
    and fixup any remaining transpose operations
    """
    skip = False
    result = []
    for this, next in zip(fragments, fragments[1:] + [None]):
        if skip:
            skip = False
            continue
            
        if this == "!transpose":
            skip = True
            # Get the list of indices which aren't the one which has been filled
            transpose_indices = [i for i in map(int, next.split(","))
                                 if i != to_fill]
            # An axis has been lost, subsequent axes need renumbering
            transpose_indices = [i-1 if i > to_fill else i 
                                 for i in transpose_indices]
            # Ignore empty transposes or transposes of axis 0
            if transpose_indices and not transpose_indices == [0]:
                result.append(this)
                result.append(",".join(map(str, transpose_indices)))
            continue
        result.append(this)
    return result
        
class MultipleTraverser(LocationAware):
    """
    Represents an arbitrary-dimensioned matrix of objects
    """
    def __init__(self, request, indexed_contexts, order=1, slot_filler=None, 
                 ordering=None):
        """
        Create a multiple traverser
        
        `index_contexts` is a list of (index_tuple, context) where index_tuple
            contains one name per dimension of the traverser.
        """
        self.request = request
        
        self.indexed_contexts = indexed_contexts
        self.order = order
        self.slot_filler = slot_filler
        self.ordering = tuple(xrange(self.order)) if ordering is None else ordering
        
        if indexed_contexts:
            assert all(len(x) == order for x, y in indexed_contexts)

    @staticmethod
    def default_slot_filler(multipletraverser, key):
        return multipletraverser.__parent__[key]

    @classmethod
    def from_listable(cls, parent, key):
        """
        Build a MultipleTraverser by matching `key` against iter(parent)
        """
        pattern = re.compile(fnmatch.translate(key))
        match = pattern.match
        indexed_contexts = [((f,), parent[f]) for f in parent if match(f)]
        slot_filler = getattr(parent, "slot_filler", cls.default_slot_filler)
        return cls.from_parent(parent, key, indexed_contexts, slot_filler=slot_filler)
    
    @property
    def flattened(self):
        return self.indexed_contexts

    def fill_slot(self, index, value):
        """
        Fill the `index`th slot of the URL with `value`
        """
        fragments, fillers = [], []
        
        # Build a list of URL fragments (resources) and slot fillers
        for i, resource in enumerate(reversed(list(lineage(self)))):
            if isinstance(resource, MultipleTraverser) and resource.slot_filler:
                fillers.append((i, resource.slot_filler))
            fragments.append(resource)
        
        assert index < len(fillers)
        
        # Index into the path for filling the `index`th slot and a function
        # which fills it
        to_fill = self.ordering[index]
        filler_index, filler_function = fillers[to_fill]
        
        # Get the (as yet incomplete) resource with the slot filled
        filled_traverser = filler_function(fragments[filler_index], value)
        
        # Get the path which needs to be appended to this traverser
        remaining_fragments = [f.__name__ for f in fragments[filler_index+1:]]
        remaining_fragments = transpose_fragments_fixup(remaining_fragments, to_fill)
        
        # Traverse any remaining parts of the path, if they exist
        remaining_path = "/".join(remaining_fragments)
        if remaining_path:
            filled_traverser = traverse(filled_traverser, remaining_path)["context"]
            
        return filled_traverser

    def fill_slots(self, index_values):
        """
        Call fill_slot repeatedly, correcting for the changes required to the indices
        """
        result = self
        # Process in sorted order so that we can correct the fill index
        for n_removed, (slot, value) in enumerate(sorted(index_values)):
            result = result.fill_slot(slot - n_removed, value)
        return result

    def __repr__(self):
        s = ('<{self.__class__.__name__} url="{self.url}" order={self.order} '
             'nitems={n} slot_filler={self.slot_filler}>')
        return s.format(self=self, n=len(self.indexed_contexts))

    def get_missing_ordering(self, ordering):
        """
        Returns the "complete ordering", in the sense that it contains all 
        indices, given `ordering`, a possibly incomplete list of indices.
        """
        return ordering + tuple(x for x in xrange(self.order) if x not in ordering)
    
    @action
    def archive(self, parent, key, format):
        """
        !archive/bz2/png
        Create an archive (e.g.) .zip of by calling !render on all contexts
        """
        raise NotImplementedError()
        
    @action
    def reorder(self, parent, key):
        """
        !reorder
        Not yet implemented: Somehow re-order indexed_contexts according to the 
        first index of index_tuple
        """
        raise NotImplementedError()
    
    @action
    def select(self, parent, key, selection):
        selection_set = set(selection.split(","))
        indexed_contexts = [(index_tuple, context)
                            for index_tuple, context in self.indexed_contexts
                            if index_tuple[0] in selection_set]
        
        return self.from_parent(parent, key, indexed_contexts,
            order=self.order, ordering=self.ordering)
    
    @action
    def transpose(self, parent, key, axes):
        """
        !tranpose
        """
        int_axes = axes.split(",")
        assert all(s.isdigit() for s in int_axes), (
            "Invalid transpose parameters. "
            "Expected comma separated integers, got {0!r}".format(axes))
            
        int_axes = tuple(map(int, int_axes))
        
        # Check for invalid
        assert not any(i >= self.order for i in int_axes), (
            "Transpose beyond available dimensions N={0}, transpose={1}. "
            "No transpose argument is allowed to be >=N."
            ).format(self.order, int_axes)
        
        complete_ordering = self.get_missing_ordering(int_axes)
        
        # Build a new indexed_contexts list with the indices re-ordered
        new_contexts = []
        for index_tuple, obj in self.indexed_contexts:
            new_index_tuple = tuple(index_tuple[i] for i in complete_ordering)
            new_contexts.append((new_index_tuple, obj))
        
        new_ordering = tuple(self.ordering[i] for i in complete_ordering)
        
        return MultipleTraverser.from_parent(parent, key, new_contexts,
                                              order=self.order, ordering=new_ordering)
    
    @action
    def compose(self, parent, key, composition_type):
        """
        !compose/composition_type
        Compose the first axis into a set of combination objects in terms of the other axes        
        """
        
        to_compose = {}
        for index_tuple, o in self.indexed_contexts:
            to_compose.setdefault(index_tuple[1:], []).append((index_tuple[0], o))
            
        new_contexts = []
        for index_tuple, stack in sorted(to_compose.iteritems()):
            filled = self.fill_slots(enumerate(index_tuple, 1))["!compose"]
            composed = Combination.from_parent(filled, key, stack, composition_type)
            new_contexts.append((index_tuple, composed))
        
        if self.order == 1:
            assert len(new_contexts) == 1
            idx, composition = new_contexts[0]
            assert idx == ()
            return composition
            
        # Otherwise build a multitraverser whose order is reduced by one.
        return MultipleTraverser.from_parent(parent, composition_type, new_contexts,
                                              order=self.order-1)
    
    def __getitem__(self, key):
        res = self.try_action(key)
        if res: return res
        
        # Traverse inside each of the contained contexts
        new_contexts = []
        for index_tuple, context in self.indexed_contexts:
            if context is None: continue
            new_contexts.append((index_tuple, context[key]))
        
        # Check that new_contexts either contains all MultiTraversers, or none.
        mts = set(isinstance(c, MultipleTraverser) for i, c in new_contexts)
        assert len(mts) == 1, "Uneven shape encountered"
        all_multitraversers = mts.pop()
        
        if all_multitraversers:
            slot_fillers = [c.slot_filler for i, c in new_contexts]
            assert len(set(slot_fillers)) == 1, "Incompatible slot fillers"
            slot_filler = slot_fillers[0]
            
            flattened_contexts = []
            for index_tuple, context in new_contexts:
                for idx, sub_context in context.indexed_contexts:
                    new_index_tuple = index_tuple + idx
                    flattened_contexts.append((new_index_tuple, sub_context))
            
            return MultipleTraverser.from_parent(self, key, flattened_contexts,
                                               self.order+1, slot_filler)
        else:
            return MultipleTraverser.from_parent(self, key, new_contexts, self.order)
