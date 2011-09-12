from pyramid.config import Configurator
from pyramid.events import subscriber, NewRequest

# Database
import pymongo

import ROOT as R
# Prevent ROOT from intercepting 
R.PyConfig.IgnoreCommandLineOptions = True

from weboot.resources.home import HomeResource


def setup_root():
    R.gROOT.SetBatch()
    R.TH1.SetDefaultSumw2()
    R.TH1.AddDirectory(False)
    R.gROOT.SetStyle("Plain")
    R.gStyle.SetPalette(1)


def start_mongo(db_path):
    print "Starting mongo"
    from atexit import register
    #from multiprocessing import Process
    from subprocess import Popen
    try:
        p = Popen(["mongod", "--dbpath", db_path])
    except OSError as err:
        raise RuntimeError("mongod not found - please comment mongo bits in your ini file or install mongod!")

    from time import sleep
    sleep(1)
    register(p.kill)

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    setup_root()

    config = Configurator(root_factory=HomeResource, settings=settings)

    config.add_view('weboot.views.my_view',
                    context='weboot:resources.home.HomeResource',
                    renderer='weboot:templates/mytemplate.pt')
                    
    config.add_view('weboot.views.view_environ',
                    context='weboot:resources.home.EnvResource',
                    renderer='weboot:templates/env.pt')
    

    for ctx in ['weboot:resources.filesystem.FilesystemTraverser',
                'weboot:resources.root.file.RootFileTraverser',
                'weboot:resources.baskets.BasketBrowser',
                'weboot:resources.baskets.BasketTraverser']:
        config.add_view('weboot.views.view_listing',
                        context=ctx,
                        renderer='weboot:templates/listing.pt')
    
    config.add_view("weboot.views.view_multitraverse", 
                    context="weboot:resources.multitraverser.MultipleTraverser",
                    renderer='weboot:templates/result.pt')
                    
    config.add_view("weboot.views.view_multitraverse_render", 
                    context="weboot:resources.multitraverser.MultipleTraverser",
                    request_param="render")
                    
    config.add_view("weboot.views.view_root_object",
                    renderer='weboot:templates/result.pt', 
                    context="weboot:resources.root.object.RootObject")
                    
    config.add_view("weboot.views.view_root_object_render",
                    context="weboot:resources.root.object.RootObject",
                    request_param="render")
    
    config.add_static_view('static', 'weboot:static')
    
    def add_mongo_db(event):
        settings = event.request.registry.settings
        url = settings['mongo.url']
        dbname = settings['mongo.dbname']
        db = settings['mongodb_conn'][dbname]
        event.request.db = db
        
    mongo_url = settings.get('mongo.url', None)
    if mongo_url:
        mongo_dbpath = settings.get("mongo.dbpath", None)
        
        if mongo_dbpath:
            start_mongo(mongo_dbpath)
    
        config.registry.settings['mongodb_conn'] = pymongo.Connection(mongo_url)
        config.add_subscriber(add_mongo_db, NewRequest)
    
    config.scan("weboot.views")
    
    return config.make_wsgi_app()

