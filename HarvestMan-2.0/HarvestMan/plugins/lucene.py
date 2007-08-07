""" Lucene plugin to HarvestMan. This plugin modifies the
behaviour of HarvestMan to create an index of crawled
files by using PyLucene

Created  Aug 7 2007     Anand B Pillai <abpillai at gmail dot com>

Copyright (C) 2007 Anand B Pillai

"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

import PyLucene
import sys, os
import hookswrapper
import time
import threading

from common.common import *
from types import StringTypes

# We keep all Lucene Documents here until they are indexed at the end
doclist = []

def init_further(self, arg):
    """ Post-callback for init method """

    storeDir = "index"
    if not os.path.exists(storeDir):
        os.mkdir(storeDir)

    store = PyLucene.FSDirectory.getDirectory(storeDir, True)
    
    self.lucene_writer = PyLucene.IndexWriter(store, PyLucene.StandardAnalyzer(), True)
    self.lucene_writer.setMaxFieldLength(1048576)
    
def process_url_further(self, data):
    """ Post process url callback for pylucene """
    
    doc = PyLucene.Document()
    # Let us point to the web URL of the document
    path = self._urlobject.get_full_url()
    # filename - The disk filename of the document
    filename = self._urlobject.get_full_filename()
    
    doc.add(PyLucene.Field("name", filename,
                           PyLucene.Field.Store.YES,
                           PyLucene.Field.Index.UN_TOKENIZED))
    doc.add(PyLucene.Field("path", path,
                           PyLucene.Field.Store.YES,
                           PyLucene.Field.Index.UN_TOKENIZED))
    if data and len(data) > 0:
        doc.add(PyLucene.Field("contents", data,
                               PyLucene.Field.Store.YES,
                               PyLucene.Field.Index.TOKENIZED))
    else:
        extrainfo("warning: no content in %s" % filename)

    global doclist
    doclist.append(doc)

    return data

def before_finalize(self):
    """ Pre callback for finalize method """

    moreinfo("Creating lucene index")
    for doc in doclist:
        self.lucene_writer.addDocument(doc)
        
    moreinfo('Optimizing lucene index')
    self.lucene_writer.optimize()
    self.lucene_writer.close()
        
def apply_plugin():
    """ Apply the plugin - overrideable method """

    # This method is expected to perform the following steps.
    # 1. Register the required hook/plugin function
    # 2. Get the config object and set/override any required settings
    # 3. Print any informational messages.

    # The first step is required, the last two are of course optional
    # depending upon the required application of the plugin.

    cfg = GetObject('config')

    hookswrapper.register_post_callback_method('harvestmanklass:init_callback',
                                               init_further)    
    hookswrapper.register_post_callback_method('crawler:fetcher_process_url_callback',
                                               process_url_further)
    hookswrapper.register_pre_callback_method('harvestmanklass:finalize_callback',
                                               before_finalize)
    #logger.disableConsoleLogging()
    # Turn off session-saver feature
    cfg.savesessions = False
    # Turn off interrupt handling
    # cfg.ignoreinterrupts = True
    # No need for localising
    cfg.localise = 0
    # Turn off image downloading
    cfg.images = 0
