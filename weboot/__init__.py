import ROOT as R
R.gROOT.SetBatch()

import rootpy
log = rootpy.log["/weboot"]

import rootpy.plotting

from pkg_resources import resource_string
__version__ = "0.1"

import sys

from pyramid.config import Configurator
from pyramid.events import subscriber, NewRequest

# Database
# from auto_mongo import MongoStartFailure, configure_mongo


from weboot.resources.home import HomeResource

def setup_root():
    R.gROOT.SetBatch()
    R.TH1.SetDefaultSumw2(True)
    R.TH1.AddDirectory(False)

    # R.TTree.Draw._threaded = True

    # Disable stack traces by default
    # R.gEnv.SetValue("Root.Stacktrace", "no")

#@log.trace()
def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    setup_root()

    from .shibboleth import ShibbolethAuthenticationPolicy

    config = Configurator(root_factory=HomeResource, 
                          authentication_policy=ShibbolethAuthenticationPolicy(),
                          settings=settings)

    # Home page
    config.add_view('weboot.views.home.view_home',
                    context='weboot:resources.home.HomeResource',
                    renderer='weboot:templates/home.pt')

    # This view is mainly debugging information
    config.add_view('weboot.views.env.view_environ',
                    context='weboot:resources.home.EnvResource',
                    renderer='weboot:templates/env.pt')

    # /~username/
    config.add_view("weboot.views.user.view_user",
                    context="weboot:resources.user.UserResource")

    # /~this-username-doesn't-exist/
    config.add_view("weboot.views.user.view_new_user",
                    context="weboot:resources.user.NewUserResource")
    
    # Things which can be listed.
    # (TODO: context=`Listable` type?)
    for ctx in ['weboot:resources.vfs.VFSTraverser',
                'weboot:resources.baskets.BasketBrowser',
                'weboot:resources.baskets.BasketTraverser',
                'weboot:resources.root.ttree.DrawTTree',
                ]:
        config.add_view('weboot.views.listing.view_listing',
                        context=ctx,
                        renderer='weboot:templates/listing.pt')
    
    # Visiting a ROOT object
    config.add_view("weboot.views.view_root_object",
                    renderer='weboot:templates/result.pt', 
                    context="weboot:resources.root.object.RootObject")
                    
    # /resource (use a default renderer if available)
    # TODO: If enabled, this currently breaks `RootObject`.
    # config.add_view("weboot.resources.renderable.default_renderer_view",
                    # context="weboot:resources.renderable.Renderable")
    #config.add_view("weboot.resources.renderable.default_renderer_view",
                    #context="weboot:resources._markdown.MarkdownResource")
                    
    # Combination plot
    config.add_view("weboot.views.view_root_object",
                    renderer='weboot:templates/result.pt', 
                    context="weboot:resources.combination.Combination")

    # Multi traverser
    config.add_view("weboot.views.multitraverse.view_multitraverse", 
                    context="weboot:resources.multitraverser.MultipleTraverser",
                    renderer='weboot:templates/result.pt')
                    
    # /!render/type
    # (because !render/type returns a Renderer object)
    config.add_view("weboot.resources.renderable.renderer_view",
                    context="weboot:resources.renderable.Renderer")
    
    config.add_static_view('static', 'weboot:static')
    
    # For now, disable mongodb.
    """
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
    """
    
    def no_mongo_db(event):
        event.request.db = None
    config.add_subscriber(no_mongo_db, NewRequest)
    
    config.scan("weboot.views")
    
    return config.make_wsgi_app()

