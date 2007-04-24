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

        # print self._cfg.maxfilesize
        
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
            # Set mode
            conn.set_data_mode(pool.get_data_mode())
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
        self._cfg.nocrawl = True
        # Need to make a config param out of it
        self._cfg.flushdata = True
        
        # Get program options
        self._cfg.parse_arguments()

        self.register_common_objects()
        self.create_initial_directories()
        
        # Calculate bandwidth and set max file size
        bw = self.calculate_bandwidth()
        # Max file size is calculated on basis of
        # maximum 15 minutes of continous download.
        if bw: self._cfg.maxfilesize = bw*900
        else: self._cfg.maxfilesize = 10485760

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
    
