from socket import gethostname, gethostbyaddr


def view_home(request):
    
    remote_host = "your machine"
    remote_addr = request.environ.get("REMOTE_ADDR", None)
    if remote_addr:
        remote_host, _, _ = gethostbyaddr(remote_addr)
    
    return {
        'project':'WebOOT', 
        'user': request.environ.get("HTTP_ADFS_FIRSTNAME", "uh, I didn't catch your name"), 
        'login': request.environ.get("HTTP_ADFS_LOGIN", "localuser"), 
        'host': gethostname(),
        'remote_host': remote_host,
        'env': ''}
