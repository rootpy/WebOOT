from os import access, W_OK, R_OK
from os.path import exists

from pyramid.security import authenticated_userid

from .vfs import VFSTraverser
from .locationaware import LocationAware


class UserResource(LocationAware):
    """
    Represents any kind of user
    """

    def __init__(self, request, user):
        super(UserResource, self).__init__(request)
        self.user = user

    @property
    def path(self):
        return self.storage_path(self.user)

    @classmethod
    def storage_path(cls, user):
        return "/afs/cern.ch/user/{initial}/{username}/weboot/".format(initial=user[0], username=user)

    @classmethod
    def check_exists(cls, user):
        "Check that the directory exists"
        return exists(cls.storage_path(user))

    @classmethod
    def check_readable(cls, user):
        "Check that the directory is writable"
        return access(cls.storage_path(user), R_OK)

    @classmethod
    def make(cls, parent, fragment):
        """
        Build an appropriate user resource object for the requseting user
        """
        request_user = authenticated_userid(parent.request)
        view_user = fragment[1:]

        resource_type = cls
        if request_user == view_user:
            if not cls.check_exists(view_user):
                resource_type = NewUserResource
            else:
                resource_type = OwnUserResource
        else:
            resource_type = UnknownUserResource

        return resource_type.from_parent(parent, fragment, view_user)

    def __getitem__(self, fragment):
        if fragment == "browse":
            return VFSTraverser.from_parent(self, fragment, self.path)


class UnknownUserResource(UserResource):
    """
    Display information for a user
    """


class OwnUserResource(UserResource):
    """
    Represents the user who is viewing the page
    """


class NewUserResource(OwnUserResource):
    """
    Displayed when a user tries to view themselves for the first time
    (i.e, ~user/weboot doesn't exist)
    """
