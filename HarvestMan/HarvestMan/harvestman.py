#!/usr/bin/env python
# -- coding: latin-1

""" HarvestMan - Multithreaded internet spider program
    using urllib2 and other python modules.
    
    Version      - 1.4.5 final

   Author: Anand B Pillai.

 HARVESTMAN is totally free software. See the file LICENSE.txt for
 information on the terms and conditions of usage, and a DISCLAIMER
 of ALL WARRANTIES. The same license agreement applies to all other
 python software modules used in this program.

 Modification History
 
  Oct 10 2003         Anand          1.3 a1 release.
  Jan 2 2004          Anand          1.3.1 bug fix version.
  Feb 24 2004         Anand          1.3.3 version release.
  Apr 20 2004         Anand          1.3.4 version release.
  Jun 14 2004         Anand          1.3.9 release.
  Sep 20 2004         Anand          1.4 development. Added methods
                                     to set locales. Patch release
                                     P001391 to fix bug #B1095681194.6 .
  Oct 20 2004         Anand          Fix for setting locales on Win32.
  Oct 25 2004         Anand          Changes for url server support.
                                     Added an exit handler.
  Nov 3  2004         Anand          1.4 alpha 3 release.
                                     * Url server run in a separate
                                     thread.
                                     * Changes in urltracker module
                                     in storing url objects.
                                     * Url server mode set as default.
                                     * Error handling fixes.
     Dec 17 2004                     1.4 final release.
     May 18 2005                     1.4.5 development - alpha1 version.
     July 13 2005                    1.4.5 development - alpha2 started.
                                     Many bugfixes, thanks to Morten Olsen@EIAO.
     August 1 2005                   Preparing for 1.4.5 beta 1. Most of the
                                     stuff is done. Done testing new command
                                     line options and verification on M$ Windoze
                                     platform.
     Aug 19 2005                     1.4.5 final release.
"""     

__revision__ = '1.4.5'
__author__ = 'Anand Pillai'

import os, sys
from sgmllib import SGMLParseError
from shutil import copy

# Our modules
# Url queue module
import urlqueue
# Connector module
import connector
# Rules module
import rules
# Data manager module
import datamgr
# Utils module
import utils
import time
# Url server
import urlserver

# Globals/lookup module
from common import *

class harvestMan(object):
    """ Top level application class """

    def __init__(self):
        """ Constructor """

        # project start page (on disk)
        self._projectstartpage = 'file://'
        # error file descriptor
        self.USER_AGENT = "HarvestMan 1.4"
        
    def finish(self):
        """ Actions to take after download is over """

        # Localise file links
        # This code sits in the data manager class
        dmgr = GetObject('datamanager')
        dmgr.post_download_setup()

        if not self._cfg.testing:
            if self._cfg.browsepage:
                browser = utils.HarvestManBrowser()
                browser.make_project_browse_page()

        # Clean up lists inside data manager
        GetObject('datamanager').clean_up()
        # Clean up lists inside rules module
        GetObject('ruleschecker').clean_up()        
        # FIXME: Better way to signal global module that
        # we are done.
        Finish()
            
    def welcome_message(self):
        """ Print a welcome message """
        
        print 'Starting %s...' % self._cfg.progname
        print 'Copyright (C) 2004-2005, Anand Pillai'
        print 'WWW: http://harvestman.freezope.org'
        print ' '

    def register_common_objects(self):
        """ Register common objects required by all projects """

        # Set myself
        SetObject(self)

        # Set verbosity in logger object
        GetObject('logger').verbosity = self._cfg.verbosity
        
        # Data manager object
        dmgr = datamgr.harvestManDataManager()
        SetObject(dmgr)
        
        # Rules checker object
        ruleschecker = rules.harvestManRulesChecker()
        # Create rules for filters
        ruleschecker.make_filters()
        
        SetObject(ruleschecker)
        
        # Connector object
        conn = connector.HarvestManNetworkConnector()
        SetObject(conn)

        # Connector factory
        conn_factory = connector.HarvestManUrlConnectorFactory(self._cfg.connections)
        SetObject(conn_factory)

        tracker_queue = urlqueue.HarvestManCrawlerQueue()
        SetObject(tracker_queue)

        # Start url server if requested
        if self._cfg.urlserver:
            import socket

            host, port = self._cfg.urlhost, self._cfg.urlport
            # Initialize server
            try:
                server = urlserver.harvestManUrlServer(host, port)
            except socket.error, (errno, errmsg):
                msg = 'Error starting url server => '+errmsg
                sys.exit(msg)
                
            # Register It
            SetObject(server)
            # Start asyncore thread
            async_t = urlserver.AsyncoreThread(timeout=30.0, use_poll=True)
            async_t.setDaemon(True)
            SetObject(async_t)

            extrainfo("Starting url server at port %d..." % self._cfg.urlport)
            async_t.start()
            
            # Test running server by pinging it 
            time.sleep(1.0)
            response = ping_urlserver(host, port)
            if not response:
                msg = """Unable to connect to url server at port %d\nCheck your settings""" % (self._cfg.urlport)
                
                sys.exit(msg)
            else:
                extrainfo("Successfully started url server.")
        
    def register_project_objects(self):
        """ Creates the objects for this project """
        
        pass

    def start_project(self):
        """ Start the current project """

        # crawls through a site using http/ftp/https protocols
        if self._cfg.project:
            info('Starting project',self._cfg.project,'...')
            
            # Write the project file
            if not self._cfg.fromprojfile:
                projector = utils.HarvestManProjectManager()
                projector.write_project()
        
        info('Starting download of url',self._cfg.url,'...')

        # Read the project cache file, if any
        if self._cfg.pagecache:
            GetObject('datamanager').read_project_cache()

        tracker_queue = GetObject('trackerqueue')
        # Configure tracker manager for this project
        if tracker_queue.configure():
            # start the project
            tracker_queue.crawl()

    def clean_up(self):
        """ Clean up actions to do, say after
        an interrupt """

        tq = GetObject('trackerqueue')
        tq.terminate_threads()

    def __prepare(self):
        """ Do the basic things and get ready """

        # Initialize globals module. This initializes
        # the config and logger objects.
        Initialize()

        SetUserAgent(self.USER_AGENT)

        self._cfg = GetObject('config')

    def setdefaultlocale(self):
        """ Set the default locale """

        # The default locale is set to
        # american encoding => en_US.ISO8859-1
        import locale
        
        if sys.platform != 'win32':
            locale.setlocale(locale.LC_ALL, locale.normalize(self._cfg.defaultlocale))
        else:
            # On windoze, the american locale does
            # not seem to be there.
            locale.setlocale(locale.LC_ALL, '')
        
    def set_locale(self):
        """ Set the locale (regional settings)
        for HarvestMan """

        # Import the locale module
        import locale
        
        # Get locale setting
        loc = self._cfg.locale

        # Try locale mappings
        trans_loc = locale.normalize(loc)
        # If we get a new locale which is
        # not american, then set it
        if trans_loc != loc and loc != 'american':
            try:
                extrainfo("Setting locale to",loc,"...")
                locale.setlocale(locale.LC_ALL,trans_loc)
                return True
            except locale.Error, e:
                # Set default locale upon any error
                self.setdefaultlocale()
                debug(str(e))
                
                return False
        else:
            # Set default locale if locale not found
            # in locale module
            self.setdefaultlocale()
            return False
        
    def run_projects(self):
        """ Run the HarvestMan projects specified in the config file """

        # Prepare myself
        self.__prepare()
        
        # Get program options
        self._cfg.get_program_options()

        # Set locale - To fix errors with
        # regular expressions on non-english web
        # sites.
        self.set_locale()

        self.register_common_objects()

        # Welcome messages
        if self._cfg.verbosity:
            self.welcome_message()

        for x in range(len(self._cfg.urls)):
            # Get all project related vars
            url = self._cfg.urls[x]

            if not self._cfg.nocrawl:
                project = self._cfg.projects[x]
                verb = self._cfg.verbosities[x]
                tout = self._cfg.projtimeouts[x]
                basedir = self._cfg.basedirs[x]

                if not url or not project or not basedir:
                    info('Invalid config options found!')
                    if not url: info('Provide a valid url')
                    if not project: info('Provide a valid project name')
                    if not basedir: info('Provide a valid base directory')
                    continue
            
            # Set the current project vars
            self._cfg.url = url
            if not self._cfg.nocrawl:
                self._cfg.project = project
                self._cfg.verbosity = verb
                self._cfg.projtimeout = tout
                self._cfg.basedir = basedir
                
            self.run_project()
            
    def run_project(self):
        """ Run a harvestman project """

        # Set project directory
        # Expand any shell variables used
        # in the base directory.
        self._cfg.basedir = os.path.expandvars(os.path.expanduser(self._cfg.basedir))
        
        if self._cfg.basedir:
            self._cfg.projdir = os.path.join( self._cfg.basedir, self._cfg.project )
            if self._cfg.projdir:
                if not os.path.exists( self._cfg.projdir ):
                    os.makedirs(self._cfg.projdir)

        # Set message log file
        # From 1.4 version message log file is created in the
        # project directory as <projectname>.log
        if self._cfg.projdir and self._cfg.project:
            self._cfg.logfile = os.path.join( self._cfg.projdir, "".join((self._cfg.project,
                                                                          '.log')))

        # Open stream to log file
        SetLogFile()
        
        # Set project objects
        self.register_project_objects()

        try:
            if not self._cfg.testnocrawl:
                self.start_project()
        except (KeyboardInterrupt, EOFError):
            if not self._cfg.ignorekbinterrupt:
                # dont allow to write cache, since it
                # screws up existing cache.
                GetObject('datamanager').conditional_cache_set()
                self.clean_up()

        # Clean up actions    
        self.finish()       
                
    def report_garbage_collection(self):
        """ Diagnosis report on garbage collection """

        # TODO
        pass
        
if __name__=="__main__":
    spider = harvestMan()
    spider.run_projects()

               
        

