from os.path import basename

import markdown

from pyramid.response import Response

from .actions import action
from .locationaware import LocationAware
from .renderable import Renderer, Renderable


class MarkdownRenderer(Renderer):
    @property
    def content(self):
        markdown_source = self.resource_to_render.source

        if self.format in ("source", "plain"):
            return Response(markdown_source, content_type="text/plain")

        if self.format == "markdown":
            markedup = markdown.markdown(markdown_source)
            return Response(markedup, content_type="text/html")

        raise RuntimeError("bad format")


class MarkdownResource(Renderer, Renderable, LocationAware):

    renderer = MarkdownRenderer

    section = "documents"

    def __init__(self, request, path=None):
        self.request = request
        self.path = path

    @property
    def source(self):
        with open(self.path) as fd:
            return fd.read()

    @property
    def content(self):
        return self["!render"]["markdown"].content

    @property
    def name(self):
        return basename(self.path[:-len(".markdown")])

    @action
    def plain(self, key):
        """
        Return unrendered markdown
        """
        return Response(self.source, content_type="text/plain")
