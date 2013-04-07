"""
Renderable objects
"""

from contextlib import contextmanager
from random import randint
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
from thread import get_ident, allocate_lock

from pyramid.response import Response

import ROOT as R

from rootpy import ROOTError

from weboot import log
log = log.getChild("renderable")

from .actions import HasActions, action
from .locationaware import LocationAware


def renderer_view(context, request):
    log.debug("renderer_view {0}".format(context))
    return context.content


def context_renderable_as(context, format):
    """
    Test if `context` can be rendered as `format`.

    Not a method of Renderable so that we can ask it of non-Renderables.
    """
    if not isinstance(context, Renderable):
        return False
    renderer = getattr(context, "renderer", None)
    assert renderer is not None, "context has renderer == None {0}".format(context)

    assert hasattr(renderer, "_supported_formats"), (
        "Renderer class should define `_supported_formats` as a set of "
        "supported format names")
    return format in renderer._supported_formats


def convert_eps(input_name, resolution=100, target_type="png"):
    """
    Call convert on an eps file in order to rewrite it to another type.
    This is typically faster and prettier (e.g. anti-aliasing) than ROOT's png
    files.
    """
    with NamedTemporaryFile(suffix=".png") as tmpfile:
        options = ["-density", str(resolution)]
        p = Popen(["convert"] + options + [input_name, tmpfile.name])
        p.wait()
        with open(tmpfile.name) as fd:
            content = fd.read()

    return content


class Renderable(HasActions):
    """
    Classes inheriting from Renderable gain a !render action
    """
    renderer = None

    @property
    def icon(self):
        if not context_renderable_as(self, "png"):
            return None
            raise RuntimeError("Error rendering icon for {0}: "
                               "not renderable as png".format(self))

        icon_resolution = self.request.params.get("iconres", 25)
        return self.rendered("png")["!resolution"][icon_resolution]

    def rendered(self, format):
        if not context_renderable_as(self, format):
            raise RuntimeError("Error rendering {0}: "
                               "not renderable as {1}".format(self, format))
        return self["!render"][format]

    @property
    def icon_url(self):
        return self.icon.url

    @action
    def render(self, parent, key, format):
        """
        !render/format
        """
        if not hasattr(self, "renderer"):
            raise RuntimeError("{0} inherits from Renderable but doesn't "
                               "define `renderer`".format(type(self)))
        return self.renderer.from_parent(parent, key, self, format)


class Renderer(LocationAware):
    """
    The base renderer
    """
    RESOLUTION_DEFAULT, RESOLUTION_MAX = 100, 200

    _supported_formats = set()

    def __init__(self, request, resource_to_render, format, params=None):
        super(Renderer, self).__init__(request)
        log.debug("New {0} renderer {1}".format(format, resource_to_render))
        self.resource_to_render = resource_to_render
        self.format = format
        self.params = params or {}

    @action
    def resolution(self, parent, key, resolution):
        params = {"resolution": resolution}
        params.update(self.params)
        args = parent, key, self.resource_to_render, self.format, params
        return self.from_parent(*args)

    @property
    def filename(self):
        """
        The filename for this rendering
        """
        return self.resource_to_render.__name__ + "." + self.format

    def render(self, canvas, keep_alive):
        raise NotImplementedError("Implement this class in the subclass")


class RootRenderer(Renderer):

    global_canvas_lock = allocate_lock()

    # This set could be bigger but currently lists the ones I have tested/used
    _supported_formats = set(["png", "eps", "pdf"])

    @property
    @contextmanager
    def canvas(self):
        # We need a thread-specific name, otherwise if two canvases exist with the
        # same name we can get a crash
        with RootRenderer.global_canvas_lock:
            # TODO(pwaller): Investigate removing this kludge now we have
            #                 a global canvas lock
            canvas_name = str(get_ident()) + str(randint(0, int(1e14)))
            log.debug("Operating with canvas {0} ({1} alive)"
                      .format(canvas_name, len(R.gROOT.GetListOfCanvases())))
            assert not R.gROOT.GetListOfCanvases().FindObject(canvas_name), (
                "Canvas collision")

            c = R.TCanvas(canvas_name)
            # Rendering code gets run here.
            yield c
            # Make the canvas go away immediately.
            # Don't wait for GC.
            c.IsA().Destructor(c)

    def configure_canvas(self, params, c):
        """
        Setup canvas options (only log axes at the moment)
        """
        if "logx" in params:
            c.SetLogx()
        if "logy" in params:
            c.SetLogy()
        if "logz" in params:
            c.SetLogz()

    @property
    def content(self):
        # TODO(pwaller): Remove defunct raise/parentage
        if self.format == "raise":
            class UserThrow(RuntimeError):
                pass
            raise UserThrow("Stopping because you asked me to.")

        log.debug("Rendering {0} from {1}".format(self.format, self))
        params = self.params
        params.update(self.request.params)

        resolution = int(params.get("resolution", self.RESOLUTION_DEFAULT))
        resolution = min(resolution, self.RESOLUTION_MAX)

        rootformat = "eps"
        if self.format == "pdf":
            rootformat = "pdf"

        with NamedTemporaryFile(suffix="." + rootformat) as tmpfile:
            with self.canvas as canvas:
                self.configure_canvas(params, canvas)
                self.render(canvas)

                canvas.Update()
                try:
                    canvas.SaveAs(tmpfile.name)
                except ROOTError as err:
                    if "illegal number of points" in err.msg:
                        log.warning('problem plotting canvas "%s", error from ROOT "%s"',
                                    canvas.GetName(), err.msg)
                    else:
                        raise

            log.info("RENDERING {0} -- {1}".format(self.format, rootformat))
            if self.format == rootformat:
                # No conversion necessary, ROOT did it directly.
                # grab the file from disk
                with open(tmpfile.name) as eps_fd:
                    content = eps_fd.read()
            else:
                # convert_eps releases the GIL by doing the work off-process.
                # This is where the speed comes from.
                content = convert_eps(tmpfile.name, resolution, self.format)

            # print "Made EPS: {0:5.2f} content = {1:5.2f}".format(len(epsdata) /
            # 1024., len(content) / 1024.)

            extra_args = {}
            if "attach" in params:
                log.error("Attaching rendered image")
                # Give the file a sensible name, rather than the last fragment
                # of the URL which was visited.
                extra_args.update(content_disposition=(
                    "Content-Disposition: attachment; filename={0};"
                    .format(self.filename)))

            return Response(content,
                            content_type="image/{0}".format(self.format), **extra_args)
