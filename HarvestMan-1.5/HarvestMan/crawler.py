# -- coding: latin-1
""" crawler.py - Module which does crawling and downloading
    of urls from the web. This module is part of HarvestMan program.

    Author: Anand B Pillai (abpillai at gmail dot com).

    For licensing information see the file LICENSE.txt that
    is included in this distribution.

    Modification history (Trimmed on Dec 14 2004)

    Aug 22 2006  Anand    Changes for fixing single-thread mode.
    Nov 9 2006   Anand    Added support to download imported stylesheets.

    Jan 2007     Anand    Support for META robot tags.
    Feb 17 2007  Anand    Modified return type of process_url in
                          HarvestManUrlFetcher class to return the data.
                          This is required for the modified swish-e
                          plugin.
    Feb 26 2007 Anand     Figured out the problem with 'disappearing' URLs.
                          The error is in the crawl_url method which was
                          checking whether a source URL was crawled. This
                          happens when a page redefines its base URL as
                          something else and when that URL is already crawled.
                          We need to modify our logic of applying base URLs.

 Copyright (C) 2004 Anand B Pillai.
   
"""

__version__ = '1.5 b1'
__author__ = 'Anand B Pillai'

import os, sys
import socket
import time
import math
import threading
import random
import exceptions
import sha

from sgmllib import SGMLParseError

from common.common import *
from common.methodwrapper import MethodWrapperMetaClass

import urlparser
import pageparser

from datamgr import harvestManController

# Defining pluggable functions
# Plugin name is the key and value is <class>:<function>

__plugins__ = { 'fetcher_process_url_hook': 'HarvestManUrlFetcher:process_url',
                'crawler_crawl_url_hook': 'HarvestManUrlCrawler:crawl_url' }

# Defining functions with pre & post callbacks
# Callback name is the key and value is <class>:<function>
__callbacks__ = { 'fetcher_process_url_callback' : 'HarvestManUrlFetcher:process_url',
                  'crawler_crawl_url_callback' : 'HarvestManUrlCrawler:crawl_url',
                  'fetcher_push_buffer_callback' : 'HarvestManUrlFetcher:push_buffer',
                  'crawler_push_buffer_callback' : 'HarvestManUrlCrawler:push_buffer',
                  'fetcher_terminate_callback' : 'HarvestManUrlFetcher:terminate',
                  'crawler_terminate_callback' : 'HarvestManUrlCrawler:terminate' }
              
class HarvestManUrlCrawlerException(Exception):

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return str(self.value)

class HarvestManBaseUrlCrawler( threading.Thread ):
    """ Base class to do the crawling and fetching of internet/intranet urls.
    This is the base class with no actual code apart from the threading or
    termination functions. """

    __metaclass__ = MethodWrapperMetaClass
    
    def __init__(self, index, url_obj = None, isThread = True):
        # Index of the crawler
        self._index = index
        # Initialize my variables
        self._initialize()
        # Am i a thread
        self._isThread = isThread
        
        if isThread:
            threading.Thread.__init__(self, None, None, self.get_role() + str(self._index))

    def _initialize(self):
        """ Initialise my state after construction """

        # End flag
        self._endflag = False
        # Status of thread (This is different from the
        # thread alive status. This is a harvestman
        # crawler status )
        # 0 => Idle
        # 1 => Working
        # 2 => Deadlocked
        self._status = 0
        # Download flag
        self._download = True
        # My url
        self._url = ''
        # The url object
        self._urlobject = None
        # Number of loops
        self._loops = 0
        # Role string
        self._role = "undefined"
        # Harvestman config object
        self._configobj = GetObject('config')
        # Crawler queue object
        self._crawlerqueue = GetObject('trackerqueue')
        # Local Buffer for Objects
        # to be put in q.
        self.buffer = MyDeque()
        # Flag for pushing to buffer
        self._pushflag = self._configobj.fastmode and (not self._configobj.blocking)
        # Resume flag - for resuming from a saved state
        self._resuming = False
        
    def __str__(self):
        return self.getName()

    def get_role(self):
        return self._role
        
    def set_role(self, role):
        self._role = role
        
    def get_url(self):
        """ Return my url """

        return self._url

    def set_url(self, url):
        """ Set my url """

        self._url = url
        
    def set_download_flag(self, val = True):
        """ Set the download flag """
        self._download = val

    def set_url_object(self, obj):
        """ Set the url object of this crawler """

        self._urlobject = obj
        self._url = self._urlobject.get_full_url()
        return True

    def set_index(self, index):
        self._index = index

    def get_index(self):
        return self._index
    
    def get_url_object(self):
        """ Return the url object of this crawler """

        return self._urlobject

    def get_current_url(self):
        """ Return the current url """

        return self._urlobject.get_full_url()
    
    def action(self):
        """ The action method, to be overridden by
        sub classes to provide action """

        pass
        
    def run(self):
        """ The overloaded run method of threading.Thread class """

        try:
            self.action()
        except Exception, e:
           if e.__class__ == HarvestManUrlCrawlerException:
               raise
           else:
               # Now I am dead - so I need to tell the queue
               # object to migrate my data and produce a new
               # thread.
               self._crawlerqueue._cond.acquire()
               self._crawlerqueue.dead_thread_callback(self)
               self._crawlerqueue._cond.release()                
        
               extrainfo('Tracker thread %s has died due to error: %s' % (str(self), str(e)))

    def terminate(self):
        """ Kill this crawler thread """

        self.stop()
        msg = self.getName() + ' Killed'
        raise HarvestManUrlCrawlerException, msg

    def stop(self):
        """ Stop this crawler thread """

        self._status = 0
        self._endflag = True
        self.set_download_flag(False)
        
    def get_status(self):
        """ Return the running status of this crawler """
        
        return self._status

    def get_status_string(self):
        """ Return the running status of this crawler as a string """
        
        if self._status == 0:
            return "idle"
        elif self._status == 1:
            return "busy"
        elif self._status == 2:
            return "locked"
        
    def has_work(self):
        """ Let others know whether I am working
        or idling """

        # Fix: Check length of local buffer also
        # before returning.
        if self._status != 0 or len(self.buffer):
            return True

        return False

    def is_locked(self):
        """ Return whether I am locked or not """

        if self._status == 2:
            return True

        return False

    def crawl_url(self):
        """ Crawl a web page, recursively downloading its links """

        pass

    def process_url(self):
        """ Download the data for a web page or a link and
        manage its data """

        pass

    def append_to_buffer(self, url_obj):
        """ Add an item to the buffer """

        self.buffer.append(url_obj)
        
    def push_buffer(self):
        """ Try to push items in local buffer to queue """

        self._status = 1

        # Try to push the last item
        stuff = self.buffer[-1]

        if self._crawlerqueue.push(stuff, self._role):
            # Remove item
            self.buffer.remove(stuff)

        self._status = 0

class HarvestManUrlCrawler(HarvestManBaseUrlCrawler):
    """ The crawler class which crawls urls and fetches their links.
    These links are posted to the url queue """

    def __init__(self, index, url_obj = None, isThread=True):
        HarvestManBaseUrlCrawler.__init__(self, index, url_obj, isThread)

    def _initialize(self):
        HarvestManBaseUrlCrawler._initialize(self)
        self._role = "crawler"
        self.links = []

    def set_url_object(self, obj):

        # Reset
        self.links = []
        
        if not obj:
            return False

        prior, (indx, links) = obj
        url_obj = GetUrlObject(indx)
        if not url_obj:
            return False
        
        self.links = links
        return HarvestManBaseUrlCrawler.set_url_object(self, url_obj)
        
    def action(self):
        
        if self._isThread:
            
            if not self._resuming:
                self._loops = 0

            while not self._endflag:

                if not self._resuming:
                    if self.buffer and self._pushflag:
                        self.push_buffer()
                    
                    obj = self._crawlerqueue.get_url_data( "crawler" )

                    if not obj:
                        if self._endflag: break
                        
                        if self.buffer and self._pushflag:
                            self.push_buffer()

                        continue
                
                    self.set_url_object(obj)
                    if not self._urlobject:
                        continue
                    
                    # Set status to one to denote busy state
                    self._status = 1

                    # Inserting a random sleep
                    time.sleep(random.random()*0.3)
                
                # Do a crawl to generate new objects
                # only after trying to push buffer
                # objects.
                self.crawl_url()

                self._loops += 1

                del self._urlobject
                self._urlobject = None
                
                # Sleep for some time
                time.sleep(random.random()*0.3)
                # Set status to zero to denote idle state                
                self._status = 0
                # If I had resumed from a saved state, set resuming flag
                # to false
                self._resuming = False
        else:
            self.process_url()
            self.crawl_url()


    def apply_url_priority(self, url_obj):
        """ Apply priority to url objects """

        cfg = GetObject('config')

        # Set initial priority to previous url's generation
        url_obj.priority = self._urlobject.generation

        # Get priority
        curr_priority = url_obj.priority

        # html files (webpages) get higher priority
        if url_obj.is_webpage():
            curr_priority -= 1

        # Apply any priorities specified based on file extensions in
        # the config file.
        pr_dict1, pr_dict2 = cfg.urlprioritydict, cfg.serverprioritydict
        # Get file extension
        extn = ((os.path.splitext(url_obj.get_filename()))[1]).lower()
        # Skip the '.'
        extn = extn[1:]

        # Get domain (server)
        domain = url_obj.get_domain()

        # Apply url priority
        if extn in pr_dict1:
            curr_priority -= int(pr_dict1[extn])

        # Apply server priority, this allows a a partial
        # key match 
        for key in pr_dict2:
            # Apply the first match
            if domain.find(key) != -1:
                curr_priority -= int(pr_dict2[domain])
                break
            
        # Set priority again
        url_obj.priority = curr_priority
        
        return 1

    def crawl_url(self):
        """ Crawl a web page, recursively downloading its links """

        # Nov 9 2006
        
        # Commented this out to add support for imported
        # stylesheets - we have to process the original stylesheet
        # in crawl_url, so this check cannot be there since stylesheet
        # is not a web-page. If this is found to cause problems later,
        # uncomment the following three lines and add a check for
        # is_stylesheet.
        
        #if not self._urlobject.is_webpage():
        #    moreinfo('Not a webpage =>',self._urlobject.get_full_url())
        #    return None

        if not self._download: return None
        
        # Rules checker object
        ruleschecker = GetObject('ruleschecker')
        # Data manager object
        mgr = GetObject('datamanager')
        
        # Check whether I was crawled
        #if ruleschecker.add_source_link(self._url):
        #    print 'I was crawled before!',self._url
        #    return None
        
        ruleschecker.add_link(self._url)

        # Configuration object
        moreinfo('Fetching links for url', self._url)
 
        priority_indx = 0

        # MOD: Need to localise <base href="..." links if any
        # so add a NULL entry. (Nov 30 2004 - Refer header)
        mgr.update_links(self._urlobject.get_full_filename(), [])
        urlobjlist = []
        
        for typ,link in self.links:

            # Check for status flag to end loop
            if self._endflag: break
            if not link: continue

            is_cgi, is_php = False, False
            if link.find('php?') != -1: is_php = True
            if typ == 'form' or is_php: is_cgi = True

            try:
                child_urlobj = urlparser.HarvestManUrlParser(link,
                                                             typ,
                                                             is_cgi,
                                                             self._urlobject)

            except urlparser.HarvestManUrlParserError, e:
                print 'Error:',e, link
                continue
                
            if not child_urlobj: continue

            if ruleschecker.is_duplicate_link( child_urlobj.get_full_url()):
                continue
            else:
                debug('Not duplicate link->',child_urlobj.get_full_url())
                pass

            child_urlobj.set_index()
            SetUrlObject(child_urlobj)
            
            # print 'URL=> %s, index=> %d' % (child_urlobj.get_full_url(), child_urlobj.index)
            urlobjlist.append(child_urlobj)
            
            child_urlobj.generation = self._urlobject.generation + 1
            typ = child_urlobj.get_type()
            
            if typ == 'javascript':
                if not self._configobj.javascript:
                    continue
            elif typ == 'javaapplet':
                if not self._configobj.javaapplet:
                    continue

            # Check for basic rules of download
            if child_urlobj.violates_rules():
                continue

            # Thread is going to push data, set status to locked...
            self._status = 2
            
            priority_indx += 1
            self.apply_url_priority( child_urlobj )
            
            # If not using url server, push data to
            # queue, otherwise send data to url server.
            # - New in 1.4 alpha2
            if not self._configobj.urlserver:
                # Fix for hanging threads - Use a local buffer
                # to store url objects, if they could not be
                # adde to queue.
                if not self._crawlerqueue.push( child_urlobj, "crawler" ):
                    if self._pushflag:
                        self.buffer.append(child_urlobj)
            else:
                # Serialize url object
                try:
                    send_url(str(child_urlobj.index),
                             self._configobj.urlhost,
                             self._configobj.urlport)
                except:
                    pass
            # Thread was able to push data, set status to busy...
            self._status = 1

        # Update links called here
        mgr.update_links(self._urlobject.get_full_filename(), urlobjlist)
            

class HarvestManUrlFetcher(HarvestManBaseUrlCrawler):
    """ This is the fetcher class, which downloads data for a url
    and writes its files. It also posts the data for web pages
    to a data queue """

    def __init__(self, index, url_obj = None, isThread=True):
        HarvestManBaseUrlCrawler.__init__(self, index, url_obj, isThread)

    def _initialize(self):
        HarvestManBaseUrlCrawler._initialize(self)
        self._role = "fetcher"
        self.wp = pageparser.HarvestManSimpleParser()
        # For increasing ref count of url
        # objects so that they don't get
        # dereferenced!
        self._tempobj = None

    def set_url_object(self, obj):

        if not obj: return False
        
        try:
            prior, indx = obj
            url_obj = GetUrlObject(indx)
        except TypeError:
            url_obj = obj

        return HarvestManBaseUrlCrawler.set_url_object(self, url_obj)

    def receive_url(self):
        """ Receive urls from the asynchronous url server. """

        try:
            err = False

            res = 0
            try:
                num_tries = 0
                while True: # and num_tries<5: (should this be enabled?)
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((self._configobj.urlhost, self._configobj.urlport))
                    
                    if err:
                        # There was error in network data, so request
                        # url data again.
                        sock.sendall("get last url")
                        num_tries += 1                        
                    else:
                        sock.sendall("get url")
                        num_tries += 1
                    response = sock.recv(8192)
                    if response=='empty':
                        break
                    try:
                        key=int(response)
                        obj = GetUrlObject(key)
                        HarvestManBaseUrlCrawler.set_url_object(self, obj)
                        res = 1
                        break
                    except Exception, e:
                        err = True

                    sock.close()    
            except socket.error, e:
                logconsole(e)

            return res
        finally:
            sock.close()
            
    def action(self):
        
        if self._isThread:

            if not self._resuming:
                self._loops = 0            

            while not self._endflag:
                    
                if not self._resuming:
                    if self.buffer and self._pushflag:
                        self.push_buffer()

                    # If url server is disabled, get data
                    # from Queue, else query url server for
                    # new urls.
                    if not self._configobj.urlserver:
                        obj = self._crawlerqueue.get_url_data("fetcher" )

                        if not obj:
                            if self._endflag: break
                            
                            if self.buffer and self._pushflag:
                                self.push_buffer()
                            continue

                        if not self.set_url_object(obj):
                            if self._endflag: break                            
                            continue

                    else:
                        if self.receive_url() != 1:
                            # Time gap helps to reduce
                            # network errors.
                            time.sleep(0.3)
                            continue

                    # Set status to busy 
                    self._status = 1

                    # Inserting a random sleep
                    time.sleep(random.random()*0.3)
                
                # Process to generate new objects
                # only after trying to push buffer
                # objects.                    
                self.process_url()
                self._loops += 1

                del self._urlobject
                self._urlobject = None

                # Sleep for some random time
                time.sleep(random.random()*0.3)                
                self._status = 0
                # Set resuming flag to False
                self._resuming = False
        else:
            self.process_url()
            self.crawl_url()

    def process_url(self):
        """ This function downloads the data for a url and writes its files.
        It also posts the data for web pages to a data queue """

        mgr = GetObject('datamanager')
        ruleschecker = GetObject('ruleschecker')
        
        # Mod - Anand Jan 10 06 - moved duplicate download check here.
        if mgr.check_duplicate_download(self._urlobject):
            debug('Detected duplicate URL in process_url... %s' % self._url)
            return -1
        
        moreinfo('Downloading file for url', self._url)
        data = mgr.download_url(self, self._urlobject)

        # Rules checker object
        ruleschecker = GetObject('ruleschecker')

        # Add webpage links in datamgr, if we managed to
        # download the url
        url_obj = self._urlobject

        if self._urlobject.typ in ('webpage','base') and data:

            urlobjlist = []
            
            # Check if this page was already crawled
            url = self._urlobject.get_full_url()
            sh = sha.new()
            sh.update(data)
            
            if ruleschecker.check_duplicate_content(self._urlobject, sh.hexdigest()):
                extrainfo('Skipped URL %s => duplicate content' % url)
                return ''
            
            self._status = 2
            
            extrainfo("Parsing web page", self._url)

            try:
                self.wp.reset()
                self.wp.feed(data)
                # Bug Fix: If the <base href="..."> tag was defined in the
                # web page, relative urls must be constructed against
                # the url provided in <base href="...">
                
                if self.wp.base_url_defined():
                    url = self.wp.get_base_url()
                    if not self._urlobject.is_equal(url):
                        extrainfo("Base url defined, replacing",self._url)
                        # Construct a url object
                        url_obj = urlparser.HarvestManUrlParser(url,
                                                                'base',
                                                                0,
                                                                self._urlobject,
                                                                self._configobj.projdir)
                        url_obj.set_index()
                        SetUrlObject(url_obj)

                        # Save a reference otherwise
                        # proxy might be deleted
                        self._tempobj = url_obj

                self.wp.close()
            except (SGMLParseError, IOError), e:
                extrainfo('SGML parse error:',str(e))
                extrainfo('Error in parsing web-page %s' % self._url)

            # Check for NOINDEX flag...do this only after checking robots flag
            if self._configobj.robots:
                # Check for NOFOLLOW tag
                if not self.wp.can_follow:
                    extrainfo('URL %s defines META Robots NOFOLLOW flag, not following its children...' % self._url)
                    return data
                
            links = self.wp.links
            # Put images first!
            if self._configobj.images:
                links += self.wp.images

            # Fix for hanging threads - Append objects
            # to local buffer if queue was full.

            # Rules checker object
            ruleschecker = GetObject('ruleschecker')

            if not self._crawlerqueue.push((url_obj, links), 'fetcher'):
                if self._pushflag:
                    print 'Appending to buffer for URL %s' % self._url
                    self.buffer.append((url_obj, links))

            return data
        
        elif self._urlobject.is_stylesheet() and data:

            # To download stylesheets imported in other stylesheets
            url_obj = self._urlobject.get_base_urlobject()
            
            # Parse stylesheet to find @import links
            imported_sheets = mgr.parse_style_sheet(data)
            if imported_sheets:
                imported_sheets = [('stylesheet', url) for url in imported_sheets]

                if not self._crawlerqueue.push((self._urlobject, imported_sheets), 'fetcher'):
                    if self._pushflag:                
                        self.buffer.append((self._urlobject, imported_sheets))

            # Successful return returns data
            return data
        else:
            # Dont do anything
            return None


class HarvestManUrlDownloader(HarvestManUrlFetcher, HarvestManUrlCrawler):
    """ This is a mixin class which does both the jobs of crawling webpages
    and download urls """

    # Created: 23 Sep 2004 for 1.4 version 
    def __init__(self, index, url_obj = None, isThread=True):
        HarvestManUrlFetcher.__init__(self, index, url_obj, isThread)
        self.set_url_object(url_obj)
        
    def _initialize(self):
        HarvestManUrlFetcher._initialize(self)
        HarvestManUrlCrawler._initialize(self)        
        self._role = 'downloader'

    def set_url_object(self, obj):
        HarvestManUrlFetcher.set_url_object(self, obj)

    def set_url_object2(self, obj):
        HarvestManUrlCrawler.set_url_object(self, obj)        

    def exit_condition(self, caller):

        # Exit condition for single thread case
        if caller=='crawler':
            return (self._crawlerqueue.data_q.qsize()==0)
        elif caller=='fetcher':
            return (self._crawlerqueue.url_q.qsize()==0)

        return False

    def is_exit_condition(self):

        return (self.exit_condition('crawler') and self.exit_condition('fetcher'))
    
    def action(self):

        if self._isThread:
            self._loops = 0

            while not self._endflag:
                obj = self._crawlerqueue.get_url_data("downloader")
                if not obj: continue
                
                self.set_url_object(obj)

                # Set status to one to denote busy state
                self._status = 1

                self.process_url()
                self.crawl_url()

                self._loops += 1
                time.sleep(0.5)
                # Set status to zero to denote idle state                
                self._status = 0
        else:
            while True:
                self.process_url()

                obj = self._crawlerqueue.get_url_data( "crawler" )
                if obj: self.set_url_object2(obj)

                if self._urlobject.is_webpage():
                    self.crawl_url()

                # If url server is disabled, get data
                # from Queue, else query url server for
                # new urls.
                if not self._configobj.urlserver:
                    obj = self._crawlerqueue.get_url_data("fetcher" )
                    self.set_url_object(obj)
                    
                else:
                    if self.receive_url() != 1:
                        # Time gap helps to reduce
                        # network errors.
                        time.sleep(0.3)
                        continue

                if self.is_exit_condition(): break

    def process_url(self):

        # First process urls using fetcher's algorithm
        HarvestManUrlFetcher.process_url(self)

    def crawl_url(self):
        HarvestManUrlCrawler.crawl_url(self)
        
    def receive_url(self):
        HarvestManUrlFetcher.receive_url(self)


