#! /usr/bin/env python
# -- coding: latin-1
""" HarvestMan - Extensible, modular and multithreaded Internet
    spider program using urllib2 and other python modules. This is
    the main module of HarvestMan.
    
    Version      - 1.5 beta 1.

    Author: Anand B Pillai <abpillai at gmail dot com>

    HARVESTMAN is free software. See the file LICENSE.txt for information
    on the terms and conditions of usage, and a DISCLAIMER of ALL WARRANTIES.

 Modification History

    Created: Aug 2003

     Jan 23 2007          Anand      Changes to copy config file to ~/.harvestman/conf
                                     folder on POSIX systems. This file is also looked for
                                     if config.xml not found in curdir.
     Jan 25 2007          Anand      Simulation feature added. Also modified config.py
                                     to allow reading cmd line arguments when passing
                                     a config file using -C option.
     Feb 7 2007          Anand       Finished implementation of plugin feature. Crawl
                                     simulator is now a plugin.
     Feb 8 2007          Anand       Added swish-e integration as a plugin.

   Copyright (C) 2004 Anand B Pillai.     
"""     

__version__ = '1.5 b1'
__author__ = 'Anand B Pillai'

import os, sys
from sgmllib import SGMLParseError
from shutil import copy
import cPickle, pickle

import urlqueue
import connector
import rules
import datamgr
import utils
import time
import threading
import shutil
import glob

import urlserver

from common.common import *

class HarvestMan(object):
    """ Top level application class """

    def __init__(self):
        """ Constructor """

        # project start page (on disk)
        self._projectstartpage = 'file://'
        # error file descriptor
        self.USER_AGENT = "HarvestMan 1.5"
        
    def finish(self):
        """ Actions to take after download is over """

        # Disable tracebacks
        # sys.excepthook = None
        # sys.tracebacklimit = 0
        
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

        # Shutdown logging at the end
        Finish()
        
    def save_current_state(self):
        """ Save state of objects to disk so program
        can be restarted from saved state """

        # If savesession is disabled, return
        if not self._cfg.savesessions:
            extrainfo('Session save feature is disabled.')
            return
        
        # Top-level state dictionary
        state = {}
        # All state objects are dictionaries

        # Get state of queue & tracker threads
        state['trackerqueue'] = GetObject('trackerqueue').get_state()
        # Get state of datamgr
        state['datamanager'] = GetObject('datamanager').get_state()
        # Get state of urlthreads 
        p = GetObject('datamanager')._urlThreadPool
        if p: state['threadpool'] = p.get_state()
        state['ruleschecker'] = GetObject('ruleschecker').get_state()

        # Get common state
        state['common'] = GetState()
        # Get config object
        state['configobj'] = GetObject('config').copy()
        
        # Dump with time-stamp - on POSIX dump this to the
        # user's .harvestman/sessions directory. 
        fname = '.harvestman_saves#' + str(int(time.time()))
        if os.name == 'posix':
            fname = os.path.join(self._cfg.usersessiondir, fname)
            
        moreinfo('Saving run-state to file %s...' % fname)
        try:
            cPickle.dump(state, open(fname, 'wb'), pickle.HIGHEST_PROTOCOL)
            moreinfo('Saved run-state to file %s.' % fname)
        except pickle.PicklingError, e:
            logconsole(e)
        
    def welcome_message(self):
        """ Print a welcome message """
        
        logconsole('Starting %s...' % self._cfg.progname)
        logconsole('Copyright (C) 2004, Anand B Pillai')
        logconsole(' ')

    def register_common_objects(self):
        """ Register common objects required by all projects """

        # Set myself
        SetObject(self)

        # Set verbosity in logger object
        GetObject('logger').verbosity = self._cfg.verbosity
        
        # Data manager object
        dmgr = datamgr.HarvestManDataManager()
        SetObject(dmgr)
        
        # Rules checker object
        ruleschecker = rules.HarvestManRulesChecker()
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

            flag, count, errmsg = 0, 0, ''

            # Try 10 attempts
            while flag == 0 and count<10:
                host, port = self._cfg.urlhost, self._cfg.urlport
                # Initialize server
                try:
                    server = urlserver.harvestManUrlServer(host, port)
                    flag = 1
                    info("Url server bound to port %d" % port)
                    break
                except socket.error, (errno, errmsg):
                    self._cfg.urlport += 1
                    count += 1

            if flag==0:
                sys.exit('Error starting url server => '+errmsg)
                
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
        
    
    def start_project(self):
        """ Start the current project """

        # crawls through a site using http/ftp/https protocols
        if self._cfg.project:
            if not self._cfg.resuming:
                info('Starting project',self._cfg.project,'...')
            else:
                info('Re-starting project',self._cfg.project,'...')                
            
            # Write the project file 
            if not self._cfg.fromprojfile:
                projector = utils.HarvestManProjectManager()
                projector.write_project()

        if not self._cfg.resuming:
            info('Starting download of url',self._cfg.url,'...')
        else:
            pass
            

        # Read the project cache file, if any
        if self._cfg.pagecache:
            GetObject('datamanager').read_project_cache()

        tracker_queue = GetObject('trackerqueue')

        if not self._cfg.resuming:
            # Configure tracker manager for this project
            if tracker_queue.configure():
                # start the project
                tracker_queue.crawl()
        else:
            tracker_queue.restart()

    def clean_up(self):
        """ Clean up actions to do, say after
        an interrupt """

        if self._cfg.fastmode:
            tq = GetObject('trackerqueue')
            tq.terminate_threads()

    def __prepare(self):
        """ Do the basic things and get ready """

        # Init Config Object
        InitConfig()
        # Initialize logger object
        InitLogger()
        
        SetUserAgent(self.USER_AGENT)

        self._cfg = GetObject('config')

        # Create user's .harvestman directory on POSIX
        if os.name == 'posix':
            homedir = os.environ.get('HOME')
            if homedir and os.path.isdir(homedir):
                harvestman_dir = os.path.join(homedir, '.harvestman')
                harvestman_conf_dir = os.path.join(harvestman_dir, 'conf')
                harvestman_sessions_dir = os.path.join(harvestman_dir, 'sessions')
                
                self._cfg.userdir = harvestman_dir
                self._cfg.userconfdir = harvestman_conf_dir
                self._cfg.usersessiondir = harvestman_sessions_dir
                
                if not os.path.isdir(harvestman_dir):
                    try:
                        info('Looks like you are running HarvestMan for the first time in this system')
                        info('Doing initial setup...')
                        info('Creating .harvestman directory in %s...' % homedir)
                        os.makedirs(harvestman_dir)
                        info('Creating "conf" sub-directory in %s...' % harvestman_dir)
                        os.makedirs(harvestman_conf_dir)
                        # Copy config.xml to $HOMEDIR/.harvestman/config folder if found
                        if os.path.isfile('config.xml'):
                            info('Copying current config file to %s...' % harvestman_conf_dir)
                            shutil.copy2('config.xml',harvestman_conf_dir)
                        info('Creating "sessions" sub-directory in %s...' % harvestman_dir)
                        os.makedirs(harvestman_sessions_dir)                        
                        info('Done.')
                            
                    except OSError, e:
                        logconsole(e)



        # Get program options
        if not self._cfg.resuming:
            self._cfg.get_program_options()

        self.register_common_objects()

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

        # Set locale - To fix errors with
        # regular expressions on non-english web
        # sites.
        self.set_locale()

        if self._cfg.verbosity:
            self.welcome_message()

        for x in range(len(self._cfg.urls)):
            # Get all project related vars
            url = self._cfg.urls[x]

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
        
        try:
            if not self._cfg.testnocrawl:
                self.start_project()
        except (KeyboardInterrupt, EOFError, Exception), e:
           logconsole('Exception received=>',str(e))
           if not self._cfg.ignoreinterrupts:
               # dont allow to write cache, since it
               # screws up existing cache.
               GetObject('datamanager').conditional_cache_set()
               self.save_current_state()
               self.clean_up()

        # Clean up actions
        try:
            self.finish()
        except Exception, e:
            # To catch errors at interpreter shutdown
            pass

    def reset_state(self):
        """ Reset state of certain objects/modules """

        # common
        ResetState()
        # Reset self._cfg
        self._cfg = GetObject('config')
        
    def restore_state(self, state_file):
        """ Restore state of some objects from a previous run """

        try:
            state = cPickle.load(open(state_file))
            # This has six keys - configobj, threadpool, ruleschecker,
            # datamanager, common and trackerqueue.

            # First update config object
            cfg = state.get('configobj')
            if cfg:
                for key,val in cfg.items():
                    self._cfg[key] = val
            else:
                # Corrupted object ?
                return -1

            # Open stream to log file
            SetLogFile()

            # Update common
            ret = SetState(state.get('common'))
            if ret == -1:
                moreinfo("Error restoring state in 'common' module - cannot proceed further!")
                return -1
            else:
                moreinfo("Restored state in 'common' module.")
            
            # Now update trackerqueue
            tq = GetObject('trackerqueue')
            ret = tq.set_state(state.get('trackerqueue'))
            if ret == -1:
                moreinfo("Error restoring state in 'urlqueue' module - cannot proceed further!")
                return -1
            else:
                moreinfo("Restored state in urlqueue module.")
            
            # Now update datamgr
            dm = GetObject('datamanager')
            ret = dm.set_state(state.get('datamanager'))
            if ret == -1:
                moreinfo("Error restoring state in 'datamgr' module - cannot proceed further!")
                return -1
            else:
                moreinfo("Restored state in datamgr module.")                
            
            # Update threadpool if any
            pool = None
            if state.has_key('threadpool'):
                pool = dm._urlThreadPool
                ret = pool.set_state(state.get('threadpool'))
                moreinfo('Restored state in urlthread module.')
            
            # Update ruleschecker
            rules = GetObject('ruleschecker')
            ret = rules.set_state(state.get('ruleschecker'))
            moreinfo('Restored state in rules module.')
            
            return 0
        except (pickle.UnpicklingError, AttributeError, IndexError, EOFError), e:
            return -1

    def grab_url(self):
        """ Download URL for the nocrawl option """

        import urlparser
        
        connfact = GetObject('connectorfactory')
        conn = connfact.create_connector(None)
        urlobj = urlparser.HarvestManUrlParser(self._cfg.url)
        print 'Connecting to %s...' % urlobj.get_full_domain()
        ret = conn.url_to_file(urlobj.get_full_url(), urlobj.get_filename())
        
    def run_saved_state(self):

        # If savesession is disabled, return
        if not self._cfg.savesessions:
            extrainfo('Session save feature is disabled, ignoring save files')
            return -1
        
        # Set locale - To fix errors with
        # regular expressions on non-english web
        # sites.
        self.set_locale()
        
        # See if there is a file named .harvestman_saves#...
        if os.name == 'posix':
            sessions_dir = self._cfg.usersessiondir
        elif os.name == 'nt':
            sessions_dir = '.'

        files = glob.glob(os.path.join(sessions_dir, '.harvestman_saves#*'))

        # Get the last dumped file
        if files:
            runfile = max(files)
            res = raw_input('Found HarvestMan save file %s. Do you want to re-run it ? [y/n]' % runfile)
            if res.lower()=='y':
                if self.restore_state(runfile)==0:
                    self._cfg.resuming = True
                    self._cfg.runfile = runfile

                    if self._cfg.verbosity:
                        self.welcome_message()
        
                    try:
                        if not self._cfg.testnocrawl:
                            self.start_project()
                    except (KeyboardInterrupt, EOFError, Exception):
                        if not self._cfg.ignoreinterrupts:
                            # dont allow to write cache, since it
                            # screws up existing cache.
                            GetObject('datamanager').conditional_cache_set()
                            # Disable tracebacks
                            sys.excepthook = None
                            self.save_current_state()
                            self.clean_up()

                    try:
                        self.finish()
                    except Exception, e:
                        # To catch errors at interpreter shutdown
                        pass
                else:
                    logconsole('Could not re-run saved state, defaulting to standard configuration...')
                    self._cfg.resuming = False
                    # Reset state
                    self.reset_state()
                    return -1
            else:
                logconsole('OK, falling back to default configuration...')
                return -1
        else:
            return -1
        pass

    def process_plugins(self):
        """ Load all plugin modules """

        plugin_dir = os.path.abspath(os.path.join(os.path.dirname('__file__'), 'plugins'))
        loaded = []
        
        if os.path.isdir(plugin_dir):
            sys.path.append(plugin_dir)
            for f in os.listdir(plugin_dir):
                if f.endswith('.py') or f.endswith('.pyc'):
                    module = os.path.splitext(f)[0]
                    if module in loaded: continue    
                    
                    # Load plugins
                    try:
                        M = __import__(module)
                        func = getattr(M, 'apply_plugin', None)
                        if not func:
                            logconsole('Invalid plugin module %s, should define function "apply_plugin"!' % f)
                        else:
                            loaded.append(module)
                            try:
                                logconsole('Applying plugin %s...' % f)
                                func()
                            except Exception, e:
                                logconsole('Error while trying to apply plugin %s' % f)
                                logconsole('Error is:',str(e))
                    except ImportError, e:
                        logconsole('Error importing plugin module %s' % f)
                        logconsole('Error is:',str(e))
                        
    def main(self):

        # Prepare myself
        self.__prepare()
        # Load plugins
        self.process_plugins()

        # If this is nocrawl mode, just download the URL
        if self._cfg.nocrawl:
            self.grab_url()
            
        # See if a crash file is there, then try to load it and run
        # program from crashed state.
        elif self.run_saved_state() == -1:
            # No such crashed state or user refused to run
            # from crashed state. So do the usual run.
            self.run_projects()

        
if __name__=="__main__":
    HarvestMan().main()

               
        

