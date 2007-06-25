#! /usr/bin/env python
# -- coding: latin-1
""" Hget - Extensible, modular, multithreaded Internet
    downloader program in the spirit of wget, using
    HarvestMan codebase, with HTTP multipart support.
    
    Version      - 1.0 beta 1.

    Author: Anand B Pillai <abpillai at gmail dot com>

    HGET is free software. See the file LICENSE.txt for information
    on the terms and conditions of usage, and a DISCLAIMER of ALL WARRANTIES.

 Modification History

    Created: April 19 2007 Anand B Pillai

     April 20 2007 Added more command-line options   Anand
     April 24 2007 Made connector module to flush data  Anand
                   to tempfiles when run with hget.
     April 25 2007 Implementation of hget features is  Anand
                   completed!
     April 30 2007 Many fixes/enhancements to hget.
                   1. Reconnection of a lost connection does not
                   lose already downloaded data.
                   2. Closing of files of threads when download is
                   aborted.
                   3. Thread count shows current number of threads
                   which are actually doing downloads, reflecting
                   the activity.
                   4. Final printing of time taken, average bandwidth
                   and file size.

     May 10 2007   Added support for sf.net mirrors in multipart.
     
Copyright(C) 2007, Anand B Pillai

"""

import sys, os
import re
import connector
import urlparser
import config
import logger
import datamgr

from common.common import *
from harvestmanklass import HarvestMan

VERSION='1.0'
MATURITY='beta 1'

class Hget(HarvestMan):
    """ Web getter class for HarvestMan which defines
    a wget like interface for downloading files on the
    command line with HTTP/1.0 Multipart support """

    def grab_url(self):
        """ Download URL """

        # print self._cfg.maxfilesize
        try:
            url = self._cfg.urls[0]
        except IndexError, e:
            print 'Error: No URL given. Run with -h or no arguments to see usage.\n'
            return -1

        # monitor = datamgr.HarvestManUrlThreadPoolMonitor()
        # monitor.start()
        
        try:
            dmgr = GetObject('datamanager')
            dmgr.initialize()
            
            pool = dmgr.get_url_threadpool()
            # print self._cfg.requests, self._cfg.connections
            conn = connector.HarvestManUrlConnector()
            # Set mode to flush/inmem
            conn.set_data_mode(pool.get_data_mode())
            
            try: 
                urlobj = urlparser.HarvestManUrlParser(url)
                ret = conn.url_to_file(urlobj)
            except urlparser.HarvestManUrlParserError, e:
                print str(e)
                print 'Error: Invalid URL "%s"' % url
                
        except KeyboardInterrupt:
            reader = conn.get_reader()
            if reader: reader.stop()
            print '\n\nDownload aborted by user interrupt.'
            # If flushdata mode, delete temporary files
            if self._cfg.flushdata:
                print 'Cleaning up temporary files...'
                fname1 = conn.get_tmpfname()
                if fname1: os.remove(fname1)

                lthreads = pool.get_threads()
                lfiles = []
                for t in lthreads:
                    fname = t.get_tmpfname()
                    if fname: lfiles.append(fname)
                    t.close_file()
                    
                pool.end_all_threads()

                for f in lfiles:
                    try:
                        os.remove(f)
                    except (IOError, OSError), e:
                        print 'Error: ',e
                        pass
                    
                print 'Done'
                
            print ''

        # monitor.stop()
        
    def create_initial_directories(self):
        """ Create the initial directories for Hget """

        super(Hget, self).create_initial_directories()
        # Create temporary directory for saving files
        if not self._cfg.hgetnotemp:
            try:
                tmp = GetMyTempDir()
                if not os.path.isdir(tmp):
                    os.makedirs(tmp)
                # Could not make tempdir, set hgetnotemp to True
                if not os.path.isdir(tmp):
                    self._cfg.hgetnotemp = True
            except Exception, e:
                pass

    def _prepare(self):
        """ Do the basic things and get ready """

        # Init Config Object
        InitConfig(config.HarvestManStateObject)
        # Initialize logger object
        InitLogger(logger.HarvestManLogger)
        
        SetUserAgent(self.USER_AGENT)

        self._cfg = GetObject('config')
        self._cfg.appname = 'Hget'
        self._cfg.version = VERSION
        self._cfg.maturity = MATURITY
        self._cfg.nocrawl = True

        # Get program options
        self._cfg.parse_arguments()

        self._cfg.flushdata = not self._cfg.inmem
        # Set number of connections to two plus numparts
        self._cfg.connections = 2*self._cfg.numparts
        self._cfg.requests = 2*self._cfg.numparts
        # Thread pool size need to be only equal to numparts
        # self._cfg.threadpoolsize = self._cfg.numparts
        # Set verbosity
        # print self._cfg.hgetverbose
        if self._cfg.hgetverbose:
            self._cfg.verbosity=2
            self._cfg.verbosities
        else:
            self._cfg.verbosity = 1

        SetLogSeverity()

        self.register_common_objects()
        self.create_initial_directories()
        
        # Calculate bandwidth and set max file size
        # bw = self.calculate_bandwidth()
        # Max file size is calculated on basis of
        # maximum 15 minutes of continous download.
        # if bw: self._cfg.maxfilesize = bw*900
        self._cfg.maxfilesize = 10485760

    def main(self):
        """ Main routine """

        # Add help option if no arguments are given
        if len(sys.argv)<2:
            sys.argv.append('-h')
            
        self._prepare()
        self.grab_url()
        return 0

if __name__ == "__main__":
    h = Hget()
    h.main()
    
