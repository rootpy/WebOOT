from pyramid.security import Everyone, Authenticated

class ShibbolethAuthenticationPolicy(object):
    """ An object representing a Pyramid authentication policy. """

    def authenticated_userid(self, request):
        """ Return the authenticated userid or ``None`` if no
        authenticated userid can be found. This method of the policy
        should ensure that a record exists in whatever persistent store is
        used related to the user (the user should not have been deleted);
        if a record associated with the current id does not exist in a
        persistent store, it should return ``None``."""
        return request.environ.get("HTTP_ADFS_LOGIN", None)
    
    def effective_principals(self, request):
        """ Return a sequence representing the effective principals
        including the userid and any groups belonged to by the current
        user, including 'system' groups such as
        ``pyramid.security.Everyone`` and
        ``pyramid.security.Authenticated``. """
        groups = request.environ.get("HTTP_ADFS_GROUP", "").split(";")
        return [Everyone, Authenticated] + groups

    def forget(self, request):
        """ Return a set of headers suitable for 'forgetting' the
        current user on subsequent requests. """
        raise HTTPFound(location="https://login.cern.ch/adfs/ls/?wa=wsignout1.0")

