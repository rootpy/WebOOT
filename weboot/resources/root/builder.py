"""
Code to "build" a WebOOT Resource of the correct tyep based on a root object
"""

import ROOT as R

from .util import get_root_class

from .object import RootObject

from .canvas import Canvas
from .graph import Graph
from .histogram import Histogram
from .parameter import Parameter
from .tree import Tree

# Used in build_root_object
# More frequently encountered object types should be earlier
RESOURCE_MAPPING = [
    (R.TH1, Histogram),
    (R.TGraph, Graph),
    (R.TGraph2D, Graph),
    (R.TCanvas, Canvas),
    ("TParameter", Parameter),
    (R.TTree, Tree),
]


def build_root_object(parent, key, obj):
    cls = get_root_class(obj.class_name)

    # Find the resource_type for the matching super class
    for root_type, resource_type in RESOURCE_MAPPING:
        if isinstance(root_type, basestring):
            # Deal with templated types by matching them against the string
            if cls and cls.__name__.startswith(root_type):
                break
            continue
        if cls and issubclass(cls, root_type):
            break
    else:
        # Wow, a use for the for-else construct?
        resource_type = RootObject

    return resource_type.from_parent(parent, key, obj)
