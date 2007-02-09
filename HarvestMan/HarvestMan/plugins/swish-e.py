""" Swish-e plugin to HarvestMan. This plugin modifies the
behaviour of HarvestMan to work with swish-e search engine.

The data format is according to the guidelines given
at http://swish-e.org/docs/swish-run.html#indexing.

Created Feb 8 2007     Anand B Pillai <abpillai@gmail.com>
"""

import hooks
from common import GetObject

def save_url(self, urlobj):

    url = urlobj.get_full_url()
    self.connect(url, urlobj, True, self._cfg.retryfailed)

    return 7

def download_url(self, caller, urlobj):

    # If not document type, skip it
    if not urlobj.is_document():
        return ''
    
    self._fetcherstatus[caller] = urlobj.get_full_url()
    server = urlobj.get_domain()
    conn_factory = GetObject('connectorfactory')
    
    # This call will block if we exceed the number of connections
    conn = conn_factory.create_connector( server )
    res = conn.save_url( urlobj )
        
    conn_factory.remove_connector(server)

    self.update_file_stats( urlobj, res )

    data = conn.get_data()

    if not data:
        fetchurl = urlobj.get_full_url()
        extrainfo( "Failed to download url", fetchurl)
        self.update_failed_files(urlobj)
    else:
        # Print data to stdout
        print 'Path-Name:',urlobj.get_full_url()
        print 'Content-Length:',len(data)
        print 'Last-Mtime:',conn.get_last_modified_time()
        print
        # Swish-e seems to be very sensitive to any additional
        # blank lines between content and headers. So stripping
        # the data of trailing and preceding newlines is important.
        print data.strip()
        
    return data

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
        hooks.register_plugin_function('connector:save_url_hook',save_url)
        hooks.register_plugin_function('datamgr:download_url_hook',download_url)
        # Turn off caching, since no files are saved
        cfg.pagecache = 0
        # Turn off console-logging
        logger = GetObject('logger')
        logger.disableConsoleLogging()
        # Turn off session-saver feature
        cfg.savesessions = False
