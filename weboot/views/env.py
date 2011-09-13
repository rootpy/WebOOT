from pprint import pformat


def view_environ(request):    
    return {'env': pformat(request.environ)}
