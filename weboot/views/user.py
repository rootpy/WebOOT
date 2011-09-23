from pyramid.response import Response
from pyramid.security import authenticated_userid, effective_principals
                
def view_user(context, request):
    
    return Response("You are looking at user: {0} - {1} <pre>{2}</pre>".format(context.user, authenticated_userid(request), "\n".join(sorted(effective_principals(request)))))
    
def view_new_user(context, request):
    return Response("Welcome, new user: {0}".format(context.user))
