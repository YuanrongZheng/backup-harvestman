""" Simulator plugin for HarvestMan. This
plugin changes the behaviour of HarvestMan
to only simulate crawling without actually
downloading anything.

Created Feb 7 2007  Anand B Pillai <abpillai at gmail dot com>

Copyright (C) 2007 Anand B Pillai
   
"""

__version__ = '1.5 b1'
__author__ = 'Anand B Pillai'


import hooks

def save_url(self, urlobj):

    # For simulation, we need to modify the behaviour
    # of save_url function in HarvestManUrlConnector class.
    # This is achieved by injecting this function as a plugin
    # Note that the signatures of both functions have to
    # be the same.

    url = urlobj.get_full_url()
    self.connect(url, urlobj, True, self._cfg.retryfailed)

    return 6

def apply_plugin():
    """ All plugin modules need to define this method """

    # This method is expected to perform the following steps.
    # 1. Register the required hook function
    # 2. Get the config object and set/override any required settings
    # 3. Print any informational messages.

    # The first step is required, the last two are of course optional
    # depending upon the required application of the plugin.
    
    from common.common import GetObject
    
    cfg = GetObject('config')
    if cfg.simulate:
        hooks.register_plugin_function('connector:save_url_hook', save_url)
        # Turn off caching, since no files are saved
        cfg.pagecache = 0
        print 'Simulation mode turned on. Crawl will be simulated and no files will be saved.'
