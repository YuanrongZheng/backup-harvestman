#! /usr/bin/env python
# -- coding: latin-1
""" Hget - Extensible, modular, multithreaded Internet
    downloader program in the spirit of wget, using
    HarvestMan codebase. 
    
    Version      - 1.0 beta 1.

    Author: Anand B Pillai <abpillai at gmail dot com>

    HGET is free software. See the file LICENSE.txt for information
    on the terms and conditions of usage, and a DISCLAIMER of ALL WARRANTIES.

 Modification History

    Created: April 19 2004 Anand B Pillai

Copyright(C) 2007, Anand B Pillai

"""

import sys, os
import re
import connector
import urlparser
import config

from common.common import *
from harvestman import HarvestMan

VERSION='1.0'
MATURITY='beta 1'

class Hget(HarvestMan):
    """ Web getter class for HarvestMan which defines
    a wget like interface for downloading files on the
    command line with HTTP/1.0 Multipart support """

    def grab_url(self):
        """ Download URL """
                
        bw = self.calculate_bandwidth()
        
        # Calculate max file size
        # Max-file size is estimated based on maximum of
        # 1 hour of download.
        if bw:
            maxsz = bw*3600
        else:
            # If cannot get bandwidth, put a default max
            # file size of 50 MB
            maxsz = 52428800
            
        self._cfg.maxfilesize = maxsz
        
        try:
            # Set url thread pool to write mode
            # In this mode, each thread flushes data to
            # disk as files, instead of keeping data
            # in-memory.
            pool = GetObject('datamanager').get_url_threadpool()
            # Set number of connections to two plus numparts
            self._cfg.connections = self._cfg.numparts + 2
            self._cfg.requests = self._cfg.numparts + 2
            conn = connector.HarvestManUrlConnector()
            try:
                urlobj = urlparser.HarvestManUrlParser(self._cfg.urls[0])
                ret = conn.url_to_file(urlobj)
            except urlparser.HarvestManUrlParserError, e:
                print str(e)
                print 'Error: Invalid URL "%s"' % self._cfg.urls[0]
                
        except KeyboardInterrupt:
            reader = conn.get_reader()
            if reader: reader.stop()
            print ''

    def _prepare(self):
        """ Do the basic things and get ready """

        # Init Config Object
        InitConfig()
        # Initialize logger object
        InitLogger()
        
        SetUserAgent(self.USER_AGENT)

        self._cfg = GetObject('config')
        self._cfg.appname = 'Hget'
        self._cfg.version = VERSION
        self._cfg.maturity = MATURITY
        
        # Get program options
        self._cfg.parse_arguments()

        self.register_common_objects()
        self.create_initial_directories()
        
        if os.name == 'posix':
            # Calculate bandwidth and set max file size
            bw = self.calculate_bandwidth()
            # Max file size is calculated as bw*timeout
            # where timeout => max time for a worker thread
            if bw: self._cfg.maxfilesize = bw*self._cfg.timeout
        
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
    
