""" Swish-e plugin to HarvestMan. This plugin modifies the
behaviour of HarvestMan to work with swish-e search engine.

The data format is according to the guidelines given
at http://swish-e.org/docs/swish-run.html#indexing.

Created  Feb 8 2007     Anand B Pillai <abpillai at gmail dot com>
Modified Feb 17 2007    Anand B Pillai Modified logic to use callbacks
                                       instead of hooks. The logic is
                                       in a post callback registered
                                       at context crawler:fetcher_process_url_callback.

Copyright (C) 2007 Anand B Pillai

"""

__version__ = '1.5 b1'
__author__ = 'Anand B Pillai'

import hooks
from common.common import GetObject
from types import StringTypes

def process_url_further(self, data):
    """ Post process url callback for swish-e """
    
    if (type(data) in StringTypes) and len(data):
        if self.wp.can_index:
            print 'Path-Name:',self._urlobject.get_full_filename()
            print 'Content-Length:',len(data)
            print
            # Swish-e seems to be very sensitive to any additional
            # blank lines between content and headers. So stripping
            # the data of trailing and preceding newlines is important.
            print data.strip()      
            

def apply_plugin():
    """ Apply the plugin - overrideable method """

    # This method is expected to perform the following steps.
    # 1. Register the required hook/plugin function
    # 2. Get the config object and set/override any required settings
    # 3. Print any informational messages.

    # The first step is required, the last two are of course optional
    # depending upon the required application of the plugin.

    cfg = GetObject('config')

    # Makes sense to activate the plugin only if swish-integration
    # is enabled.
    if cfg.swishplugin:
        hooks.register_post_callback_method('crawler:fetcher_process_url_callback',process_url_further)
        # Turn off caching, since no files are saved
        cfg.pagecache = 0
        # Turn off console-logging
        logger = GetObject('logger')
        logger.disableConsoleLogging()
        # Turn off session-saver feature
        cfg.savesessions = False
