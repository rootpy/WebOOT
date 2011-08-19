from pyramid.config import Configurator
from pyramid.events import subscriber, NewRequest

import pymongo

import ROOT as R
R.PyConfig.IgnoreCommandLineOptions = True

def setup_root():
    R.gROOT.SetBatch()
    R.TH1.SetDefaultSumw2()
    R.TH1.AddDirectory(False)
    R.gROOT.SetStyle("Plain")
    R.gStyle.SetPalette(1)

from weboot.resources import Root, FilesystemTraverser

def start_mongo(db_path):
    print "Starting mongo"
    from atexit import register
    #from multiprocessing import Process
    from subprocess import Popen
    p = Popen(["mongod", "--dbpath", db_path])
    from time import sleep
    sleep(1)
    register(p.kill)

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    setup_root()

    config = Configurator(root_factory=Root, settings=settings)

    config.add_view('weboot.views.my_view',
                    context='weboot:resources.Root',
                    renderer='weboot:templates/mytemplate.pt')
    

    for ctx in ['weboot:resources.FilesystemTraverser',
                'weboot:resources.RootFileTraverser',
                'weboot:resources.BasketBrowser',
                'weboot:resources.BasketTraverser']:
        config.add_view('weboot.views.view_listing',
                        context=ctx,
                        renderer='weboot:templates/listing.pt')
                    
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

