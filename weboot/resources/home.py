"""
This file contains the Home object
"""

from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.security import authenticated_userid

from .actions import HasActions
from .locationaware import LocationAware
from .renderable import Renderer
from .user import UserResource

# ** Additional imports appear below to avoid circular dependencies ** #


class EnvResource(LocationAware):
    def __init__(self, request):
        self.request = request


class StackResource(Renderer):
    def __init__(self, request):
        self.request = request

    @property
    def content(self):

        import sys
        import traceback

        frames = sorted(sys._current_frames().iteritems())

        active, waiting = [], []
        for thread_id, f in frames:

            if "wait" in f.f_code.co_name:
                waiting.append("  {0}".format(thread_id))
                continue

            s = "".join(traceback.format_stack(f))
            stack = "Thread: {0}\n{1}".format(thread_id, s)
            active.append(stack)

        response = "Current stack (ignoring {1} waiting):\n\n{0}".format(
            "\n\n".join(active), len(waiting))
        return Response(response, content_type="text/plain")


class HomeResource(LocationAware, dict):
    def __init__(self, request):
        super(HomeResource, self).__init__(request)

        self.add("browse", VFSTraverser)
        self.add("env", EnvResource)
        self.add("stack", StackResource)

        if self.request.db:
            self.add("baskets", BasketBrowser)

    def add(self, name, cls, *args, **kwargs):
        self[name] = cls.from_parent(self, name, *args, **kwargs)

    def __getitem__(self, fragment):
        if fragment in self:
            return self.get(fragment)

        if fragment.startswith("~"):
            return UserResource.make(self, fragment)

        if fragment == "me":
            request_user = authenticated_userid(self.request)
            return HTTPFound(location=self.sub_url("~{0}".format(request_user)))

        raise KeyError("{0} not found on the HomeResource".format(fragment))


from .baskets import BasketBrowser
from .vfs import VFSTraverser
