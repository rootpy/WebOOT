from pyramid.config import Configurator
from weboot.resources import Root, FilesystemTraverser

import ROOT as R
R.PyConfig.IgnoreCommandLineOptions = True

def setup_root():
    R.gROOT.SetBatch()

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    setup_root()

    config = Configurator(root_factory=Root, settings=settings)

    config.add_view('weboot.views.my_view',
                    context='weboot:resources.Root',
                    renderer='weboot:templates/mytemplate.pt')
                    
    config.add_static_view('static', 'weboot:static')
    
    #config.add_route("result", "/result/*traverse", factory=FilesystemTraverser)
    
    config.scan("weboot.views")
    
    return config.make_wsgi_app()

