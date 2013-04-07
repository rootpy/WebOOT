from contextlib import contextmanager
from rootpy.memory.keepalive import keepalive

from weboot.resources.root.object import RootObject
from weboot.resources.renderable import Renderable, RootRenderer


class CanvasRenderer(RootRenderer):

    @property
    @contextmanager
    def canvas(self):
        with RootRenderer.global_canvas_lock:
            yield self.resource_to_render.obj

    def render(self, canvas):
        """
        Do nothing. The canvas came from elsewhere
        """
        pass


class Canvas(Renderable, RootObject):

    renderer = CanvasRenderer

    def __init__(self, request, root_object):
        super(Canvas, self).__init__(request, root_object)

    @property
    def content(self):
        rendered = self["!render"]["png"]["!resolution"]["100"]
        return ['<p><img class="plot" src="{0}" /></p>'.format(rendered.sub_url(query={"todo-removeme": 1}))]
