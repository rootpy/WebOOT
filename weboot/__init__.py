# Must be first import
from .logger import log_manager, log_trace; log = log_manager.getLogger("weboot")

from pkg_resources import resource_string
__version__ = resource_string(__name__, "version.txt")

import sys

from pyramid.config import Configurator
from pyramid.events import subscriber, NewRequest

# Database
from auto_mongo import MongoStartFailure, configure_mongo

import ROOT as R
# Prevent ROOT from intercepting commandline args
R.PyConfig.IgnoreCommandLineOptions = True

from weboot.resources.home import HomeResource


def setup_root():
    R.gROOT.SetBatch()
    R.TH1.SetDefaultSumw2(False)
    R.TH1.AddDirectory(False)
    R.gROOT.SetStyle("Plain")
    R.gStyle.SetPalette(1)

@log_trace(log)
def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    setup_root()

    from .shibboleth import ShibbolethAuthenticationPolicy

    config = Configurator(root_factory=HomeResource, 
                          authentication_policy=ShibbolethAuthenticationPolicy(),
                          settings=settings)

    config.add_view('weboot.views.home.view_home',
                    context='weboot:resources.home.HomeResource',
                    renderer='weboot:templates/home.pt')

    # This view is mainly debugging information
    config.add_view('weboot.views.env.view_environ',
                    context='weboot:resources.home.EnvResource',
                    renderer='weboot:templates/env.pt')

    config.add_view("weboot.views.user.view_user",
                    context="weboot:resources.user.UserResource")

    config.add_view("weboot.views.user.view_new_user",
                    context="weboot:resources.user.NewUserResource")
    
    # Listings of diverse type
    for ctx in ['weboot:resources.vfs.VFSTraverser',
                'weboot:resources.baskets.BasketBrowser',
                'weboot:resources.baskets.BasketTraverser',
                'weboot:resources.root.ttree.DrawTTree',
                ]:
        config.add_view('weboot.views.listing.view_listing',
                        context=ctx,
                        renderer='weboot:templates/listing.pt')
    
    # Result view:
    config.add_view("weboot.views.view_root_object",
                    renderer='weboot:templates/result.pt', 
                    context="weboot:resources.root.object.RootObject")
                    
    config.add_view("weboot.views.view_root_object",
                    renderer='weboot:templates/result.pt', 
                    context="weboot:resources.combination.Combination")

    config.add_view("weboot.views.multitraverse.view_multitraverse", 
                    context="weboot:resources.multitraverser.MultipleTraverser",
                    renderer='weboot:templates/result.pt')

                    
    config.add_view("weboot.views.multitraverse.view_multitraverse_render", 
                    context="weboot:resources.multitraverser.MultipleTraverser",
                    request_param="render")

                    
    config.add_view("weboot.views.root.object.view_root_object_render",
                    context="weboot:resources.root.object.RootObject",
                    request_param="render")


                    
                    
    config.add_view("weboot.resources.renderable.renderer_view",
                    context="weboot:resources.renderable.Renderer")
    
    config.add_static_view('static', 'weboot:static')
    
    try:
        db = configure_mongo(config, settings)
        def request_setup_db(event):
            event.request.db = db
        config.add_subscriber(request_setup_db, NewRequest)        
    except MongoStartFailure as e:
        log.warning("MongoDB failed to start: {0}".format(e))
        def no_mongo_db(event):
            event.request.db = None
        config.add_subscriber(no_mongo_db, NewRequest)
    
    config.scan("weboot.views")
    
    return config.make_wsgi_app()

