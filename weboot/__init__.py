from pyramid.config import Configurator
from pyramid.events import subscriber, NewRequest

import pymongo

import ROOT as R
R.PyConfig.IgnoreCommandLineOptions = True

def setup_root():
    R.gROOT.SetBatch()

from weboot.resources import Root, FilesystemTraverser


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    setup_root()

    config = Configurator(root_factory=Root, settings=settings)

    config.add_view('weboot.views.my_view',
                    context='weboot:resources.Root',
                    renderer='weboot:templates/mytemplate.pt')
                    
    config.add_view('weboot.views.view_listing',
                    context='weboot:resources.FilesystemTraverser',
                    renderer='weboot:templates/listing.pt')
                    
    config.add_view('weboot.views.view_listing',
                    context='weboot:resources.RootFileTraverser',
                    renderer='weboot:templates/listing.pt')
                    
    config.add_static_view('static', 'weboot:static')
    
    def add_mongo_db(event):
        settings = event.request.registry.settings
        url = settings['mongodb.url']
        db_name = settings['mongodb.db_name']
        db = settings['mongodb_conn'][db_name]
        event.request.db = db
        
    mongo_url = settings.get('mongodb.url', None)
    if mongo_url:
        conn = pymongo.Connection(settings['mongodb.url'])
        config.registry.settings['mongodb_conn'] = conn
        config.add_subscriber(add_mongo_db, NewRequest)
    
    config.scan("weboot.views")
    
    return config.make_wsgi_app()

