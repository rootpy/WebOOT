from pyramid.httpexceptions import HTTPFound, HTTPMethodNotAllowed
from pyramid.traversal import resource_path
from pyramid.url import static_url

import ROOT as R

from weboot.resources.actions import action
from ..locationaware import LocationAware

from .util import get_root_class


class ListingItem(object):
    @property
    def icon_path(self):
        """
        Default Icon
        """
        return static_url('weboot:static/folder_32.png', self.request)


class RootObject(LocationAware, ListingItem):
    """
    A page that shows a ROOT object
    """
    def __init__(self, request, root_object):
        self.request = request
        self.o = root_object
        self.cls = get_root_class(self.o.class_name)

    @property
    def section(self):
        if not self.cls:
            return
        if issubclass(self.cls, R.TH1):
            return "hist"
        if "TParameter" in self.cls.__name__:
            return "parameters"

    @property
    def content(self):
        if self.cls and issubclass(self.cls, R.TObjString):
            from cPickle import loads
            from pprint import pformat
            content = pformat(dict(loads(self.obj.GetString().Data())))
            return ["<p><pre>{0}</pre></p>".format(content)]

        return ["<p>Hm, I don't know how to render a {0}</p>".format(self.cls.__name__)]

    @property
    def obj(self):
        o = self.o.get()
        return o

    @property
    def name(self):
        return self.o.name

    @property
    def path(self):
        return self.o.name

    @property
    def icon_url(self):
        return static_url('weboot:static/close_32.png', self.request)

    @action
    def basket(self, parent, key):
        if not self.request.db:
            raise HTTPMethodNotAllowed("baskets not available - no connect to database")
        else:
            self.request.db.baskets.insert({"basket": "my_basket",
                                            "path": resource_path(self), "name": self.name})
            log.debug("adding {0} to basket".format(self.url))
            return HTTPFound(location=self.url)
