# -- coding: iso8859-1

##  HARVESTMAN - Multithreaded internet spider program
##     using urllib2 and other python modules.
    
##     Version      - 1.4 (final)

##    Author: Anand B Pillai(anandpillai at letterboxes dot org).

##  HARVESTMAN is totally free software. See the file LICENSE.txt for
##  information on the terms and conditions of usage, and a DISCLAIMER
##  of ALL WARRANTIES. The same license agreement applies to all other
##  python software modules used in this program.

##  Modification History
##  ====================

##   Oct 10 2003         Anand          1.3 a1 release.
##   Jan 2 2004          Anand          1.3.1 bug fix version.
##   Feb 24 2004         Anand          1.3.3 version release.
##   Apr 20 2004         Anand          1.3.4 version release.
##   Jun 14 2004         Anand          1.3.9 release.
##   Sep 20 2004         Anand          1.4 development. Added methods
##                                      to set locales. Patch release
##                                      P001391 to fix bug #B1095681194.6 .
##   Oct 20 2004         Anand          Fix for setting locales on Win32.
##   Oct 25 2004         Anand          Changes for url server support.
##                                      Added an exit handler.
##   Nov 3  2004         Anand          1.4 alpha 3 release.
##                                      * Url server run in a separate
##                                      thread.
##                                      * Changes in urltracker module
##                                      in storing url objects.
##                                      * Url server mode set as default.
##                                      * Error handling fixes.
##      Dec 17 2004                     1.4 final release.


import os, sys
from sgmllib import SGMLParseError
from shutil import copy

# Our modules

# Tracker modules
import urltracker
# Connector module
import connector
# Rules module
import rules
# Data manager module
import datamgr
# Cookie module
import cookiemgr
# Utils module
import utils
import time
# Url server
import urlserver
import socket

# Globals/lookup module
from common import *

class harvestMan(object):
    """ Top level application class """

    def __init__(self):
        """ Constructor """

        # project start page (on disk)
        self._projectstartpage='file://'
        # error file descriptor
        self.USER_AGENT="HarvestMan 1.4"
        # Error stream
        self.ew = None
        
    def set_error_log(self, errorfile):
        """ Function to call to set this class
        as sys.stderr """

        # error log file
        errorlogpath = os.path.join(self._cfg.projdir, errorfile)
        
        if os.path.exists(errorlogpath):
            try:
                os.remove(errorlogpath)
            except OSError, e:
                print e
                
        self.ew = open(errorlogpath, 'w')

    def finish(self):
        """ Actions to take after download is over """

        # Close the cookie session so that
        # cookies are saved.
        cookie_manager = GetObject('cookiestore')
        cookie_manager.close_session()
        
        # Localise file links
        # This code sits in the data manager class
        dmgr = GetObject('datamanager')
        dmgr.post_download_setup()

        if not self._cfg.testing:
            if self._cfg.browsepage:
                browser = utils.HarvestManBrowser()
                browser.make_project_browse_page()

        # FIXME: Better way to signal global module that
        # we are done.
        Finish()
            
    def write(self, msg):
        """ Overloaded function when this class behaves
        as sys.stderr """
        
        try:
            self.ew.write(msg)
            self.ew.flush()
        except Exception, e:
            # dont recursively crash on errors
            pass

    def welcome_message(self):
        """ Print a welcome message """
        
        info('Starting HarvestMan version', self._cfg.version)
        info('Copyright (C) 2004-2005, Anand B Pillai')
        info('WWW: http://harvestman.freezope.org')
        info(' ')

    def register_objects(self):
        """ Creates the objects for harvestman """
        
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
        
        # Cookie manager object
        # We are saving the cookies in each projects project directory
        if self._cfg.cookies:
            cookie_file = os.path.join(self._cfg.projdir, 'cookies.dat')
            hcookiestore = cookiemgr.DBMCookieStore(cookie_file)
        
            cmgr = cookiemgr.CookieManager(hcookiestore)
            SetObject(cmgr )

        # Start url server if requested
        if self._cfg.urlserver:
            host, port = self._cfg.urlhost, self._cfg.urlport
            # Initialize server
            try:
                server=urlserver.harvestManUrlServer(host,port)
            except socket.error, (errno, errmsg):
                msg='Error starting url server => '+errmsg
                sys.exit(msg)
            # Register It
            SetObject(server)
            # Start asyncore thread
            async_t = urlserver.AsyncoreThread(timeout=30.0,use_poll=True)
            SetObject(async_t)
            async_t.start()
            
            # Test running server by pinging it 
            time.sleep(1.0)
            response=ping_urlserver(host,port)
            if not response:
                msg = """Unable to connect to url server at port %d\nCheck your settings""" % (self._cfg.urlport)
                
                sys.exit(msg)

            # self.usethreads = 0

        # create tracker monitor
        tracker_queue = urltracker.HarvestManCrawlerQueue()
        SetObject(tracker_queue)

        tracker_queue.configure()

        # Set myself
        SetObject(self)

        # Set system exit handler function
        sys.exitfunc = self.exit_handler

    def start_project(self):
        """ Start the current project """

        # Welcome messages
        self.welcome_message()

        # crawls through a site using http/ftp/https protocols
        info('Starting project ', self._cfg.project ,'...')

        # Write the project file
        projector = utils.HarvestManProjectManager()
        projector.write_project()
        
        info('Starting download of url ', self._cfg.url, '...')

        # Read the project cache file, if any
        if self._cfg.pagecache:
            GetObject('datamanager').read_project_cache()

        tracker_queue=GetObject('trackerqueue')
        # start the project
        tracker_queue.crawl()

    def exit_handler(self):
        """ System exit handler """

        # print 'Exit handler called!'
        if self.ew:
            try:
                self.ew.flush()
                self.ew.close()
            except Exception, e:
                print e

    def clean_up(self):
        """ Clean up actions to do, say after
        an interrupt """

        tq = GetObject('trackerqueue')
        tq.terminate_threads()

        # Close the cookie session so that
        # cookies are saved.
        cookie_manager = GetObject('cookiestore')
        cookie_manager.close_session()
        
    def __prepare(self):
        """ Do the basic things and get ready """

        # Initialize globals module. This initializes
        # the config and connector objects.
        Initialize()

	SetUserAgent(self.USER_AGENT)

        self._cfg = GetObject('config')
        # set program name on config object
        self._cfg.progname = 'HarvestMan ' + self._cfg.version

    def setdefaultlocale(self):
        """ Set the default locale """

        # The default locale is set to
        # american encoding => en_US.ISO8859-1
        import locale
        
        if sys.platform != 'win32':
            locale.setlocale(locale.LC_ALL, locale.normalize('american'))
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
                return 0
            except locale.Error, e:
                # Set default locale upon any error
                self.setdefaultlocale()
                print e
                return -1
        else:
            # Set default locale if locale not found
            # in locale module
            self.setdefaultlocale()
            return -1
        
        
    def set_project(self):
        """ Set the variables and initialize
        this object and other harvestman objects """

        # Prepare myself
        self.__prepare()
        
        # Get program options
        res=self._cfg.get_program_options()

        # Set locale - To fix errors with
        # regular expressions on non-english web
        # sites.
        self.set_locale()

        sys.setcheckinterval(1000)
        # Populate the url, project and basedir variables
        url=self._cfg.url
        project=self._cfg.project
        basedir=self._cfg.basedir
        
        if not url or not project or not basedir:
            print 'Invalid config options'
            print 'Enter a valid url, project and base directory in the config file'
            sys.exit(1)

        # Set project directory
        # Expand any shell variables used
        # in the base directory.
        self._cfg.basedir = os.path.expandvars(os.path.expanduser(self._cfg.basedir))
        self._cfg.projdir = os.path.join( self._cfg.basedir, self._cfg.project )

        if not os.path.exists( self._cfg.projdir ):
            os.makedirs(self._cfg.projdir)

        # Set message log file
        # From 1.4 version message log file is created in the
        # project directory as <projectname>.log
        self._cfg.logfile = os.path.join( self._cfg.projdir, "".join((self._cfg.project,
                                                                      '.log')))
        # Open stream to log file
        SetLogFile()
        
        self.register_objects()
            
        # Set error log file
        if self._cfg.errorfile:
            if not self._cfg.testing:
                #sys.stderr = self
                #self.set_error_log(self._cfg.errorfile)
                pass

    def run_project(self):
        """ Run a harvestman project """
        
        try:
            self.start_project()
        except (KeyboardInterrupt, EOFError):
            if not self._cfg.ignorekbinterrupt:
                # dont allow to write cache, since it
                # screws up existing cache.
                GetObject('datamanager').conditional_cache_set()
                try:
                    self.clean_up()
                except SystemExit, e:
                    pass
   
        # Clean up actions    
        self.finish()       

    def report_garbage_collection(self):
        """ Diagnosis report on garbage collection """

        # TODO
        pass
        
if __name__=="__main__":
    spider = harvestMan()
    spider.set_project()
    spider.run_project()
        

