# -- coding: iso8859-1
""" HarvestManUrlTracker.py - Module to track and download urls
    from the internet using urllib2. This software is part
    of the HarvestMan program.

    Author: Anand B Pillai (anandpillai at letterboxes dot org).

    For licensing information see the file LICENSE.txt that
    is included in this distribution.

    Dependency
    ==========
    1. HarvestManHTMLParser.py
    2. HarvestManRobotParser.py
    3. HarvestManUrlPathParser.py
    4. HarvestManUrlThread.py
    5. HarvestManPageParser.py
    6. HarvestManUrlConnector.py

    Modification history (Trimmed on Dec 14 2004)

  Nov 18 2004           Anand         Fixed bugs in the above algorithm.
                                      o Urls in the local buffer were not processed,
                                      leading to partial downloads. Added a push_buffer
                                      method to process urls/links in local buffer.
                                      o Modified get_url_data method also to non-blocking
                                      so that local buffer objects can be processed, when
                                      we reach the end of a download.
                                      o Added a check to see if a file is already downloaded
                                      in set_url_object method of Fetcher class.
                                      o Increased sleep times to reduce CPU usage.
                                      o Modified is_busy method to has_work, which returns
                                      False (not busy) only if local buffer is empty.

                                      Removed check of whether queues are locked
                                      or not. Not needed in current architecture.

  Nov 26 2004           Anand         Fixed a bug. If <base href='...'> link is defined
                                      in a web page, urls need to be constructed using it
                                      as the parent url.

  Nov 30 2004           Anand         Added an update_links method in fetcher's
                                      process_url method to add the current url. This
                                      makes sure that the file is parsed for localizing
                                      even if it does not have any links (for replacing
                                      <base href='...'> links if any.
"""

import os, sys
import socket
import time
import math
import threading
import bisect

from Queue import Queue, Full, Empty
from sgmllib import SGMLParseError

from common import *
import urlparser
import htmlparser
import pageparser

from datamgr import harvestManController

class HarvestManUrlCrawlerException(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class HarvestManBaseUrlCrawler( threading.Thread ):
    """ Base class to do the crawling and fetching of internet/intranet urls.
    This is the base class with no actual code apart from the threading or
    termination functions. """

    def __init__(self, index, url_obj = None, isThread = True):
        # Index of the crawler
        self._index = index
        # Initialize my variables
        self._initialize()
        # Set url object
        self.set_url_object(url_obj)
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
        self.buffer = []
        
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
    
    def action(self):
        """ The action method, to be overridden by
        sub classes to provide action """

        pass
        
    def run(self):
        """ The overloaded run method of threading.Thread class """

        self.action()

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

    def __init___(self, index, url_obj = None, isThread=True):
        HarvestManBaseUrlCrawler.__init__(self, index, url_obj, isThread)

    def _initialize(self):
        HarvestManBaseUrlCrawler._initialize(self)
        self._role = "crawler"
        self.links = []

    def set_url_object(self, obj):

        if obj is None: return None

        prior, (indx, links) = obj
        url_obj = GetUrlObject(indx)
        if url_obj is None:
            return False
        
        self.links = links
        HarvestManBaseUrlCrawler.set_url_object(self, url_obj)

    def action(self):
        
        if self._isThread:

            self._loops = 0

            while not self._endflag:
                if self.buffer:
                    self.push_buffer()
                    
                obj = self._crawlerqueue.get_url_data( "crawler" )
                if obj is None:
                    if self.buffer and not self._configobj.blocking:
                        self.push_buffer()
                    else:
                        continue
                
                self.set_url_object(obj)

                # Set status to one to denote busy state
                self._status = 1

                # Do a crawl to generate new objects
                # only after trying to push buffer
                # objects.
                self.crawl_url()

                self._loops += 1
                # Sleep for some time
                time.sleep(0.3)
                # Set status to zero to denote idle state                
                self._status = 0
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
        if extn in pr_dict1.keys():
            curr_priority -= int(pr_dict1[extn])

        # Apply server priority, this allows a a partial
        # key match 
        for key in pr_dict2.keys():
            # Apply the first match
            if domain.find(key) != -1:
                curr_priority -= int(pr_dict2[domain])
                break
            
        # Set priority again
        url_obj.priority = curr_priority
        
        return 1

    def crawl_url(self):
        """ Crawl a web page, recursively downloading its links """

        if not self._urlobject.is_webpage(): return None
        if not self._download: return None
        
        # Rules checker object
        ruleschecker = GetObject('ruleschecker')
        # Check whether I was crawled
        if ruleschecker.add_source_link(self._url):
            return None
        
        ruleschecker.add_link(self._url)

        # Data manager object
        dmgr = GetObject('datamanager')

        # Configuration object
        moreinfo('\nFetching links for url', self._url)
 
        priority_indx = 0
        
        base_url = self._urlobject.get_full_url()

        # print 'My Links =>',base_url
        for typ, childurl in self.links:

            # print typ,childurl
            # Check for status flag to end loop
            if self._endflag: break

            is_cgi, is_php = False, False

            if childurl.find('php?') != -1: is_php = True
            if type == 'form' or is_php: is_cgi = True
            
            try:
                url_obj = urlparser.HarvestManUrlParser(childurl,
                                                        typ,
                                                        is_cgi,
                                                        self._urlobject)
                
                url_obj.generation = self._urlobject.generation + 1
            except urlparser.HarvestManUrlParserError, e:
                debug(str(e), childurl)
                continue

            if ruleschecker.is_duplicate_link( url_obj.get_full_url() ):
                continue

            dmgr.update_links(self._urlobject.get_full_filename(), url_obj)

            # New in 1.2 (rc3) - get javascript links (.js)
            if typ == 'javascript':
                # moreinfo(" I found a javascript tag!")
                if not self._configobj.javascript:
                    continue
            elif typ == 'javaapplet':
                # moreinfo("I found a java applet class")
                if not self._configobj.javaapplet:
                    continue

            # Check for basic rules of download
            if url_obj.violates_rules():
                continue

            if self._configobj.fastmode:
                # Thread is going to push data, set status to locked...
                self._status = 2
            
                priority_indx += 1
                self.apply_url_priority( url_obj )

                url_obj.set_index()
                SetUrlObject(url_obj)
                
                # If not using url server, push data to
                # queue, otherwise send data to url server.
                # - New in 1.4 alpha2
                if not self._configobj.urlserver:
                    # Fix for hanging threads - Use a local buffer
                    # to store url objects, if they could not be
                    # adde to queue.
                    if not self._crawlerqueue.push( url_obj, "crawler" ):
                        if not self._configobj.blocking:
                            self.buffer.append(url_obj)
                        
                else:
                    # Serialize url object
                    try:
                        send_url(str(url_obj.index),
                                 self._configobj.urlhost,
                                 self._configobj.urlport)
                    except socket.error, e:
                        pass
                    except Exception, e:
                        pass
                # Thread was able to push data, set status to busy...
                self._status = 1
            else:
                t=HarvestManUrlDownloader(self._index+1, url_obj, False)
                t.action()


class HarvestManUrlFetcher(HarvestManBaseUrlCrawler):
    """ This is the fetcher class, which downloads data for a url
    and writes its files. It also posts the data for web pages
    to a data queue """

    def __init___(self, index, url_obj = None, isThread=True):
        HarvestManBaseUrlCrawler.__init__(self, index, url_obj, isThread)

    def _initialize(self):
        HarvestManBaseUrlCrawler._initialize(self)
        self._role = "fetcher"
        self.wp = pageparser.harvestManSimpleParser()
        # For increasing ref count of url
        # objects so that they don't get
        # dereferenced!
        self._tempobj = None

    def set_url_object(self, obj):

        if obj is None: return False
        
        try:
            prior, indx = obj
            url_obj = GetUrlObject(indx)
        except TypeError:
            url_obj = obj

        # Check if this is already downloaded
        if GetObject('datamanager').is_file_downloaded(url_obj.get_full_filename()):
            return False
        
        return HarvestManBaseUrlCrawler.set_url_object(self, url_obj)

    def receive_url(self):
        """ Receive urls from the asynchronous url server. """

        # New method in 1.4 alpha2
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
                print e

            return res
        finally:
            sock.close()
            
    def action(self):
        
        if self._isThread:
            self._loops = 0

            while not self._endflag:
                if self.buffer:
                    self.push_buffer()
                    
                # If url server is disabled, get data
                # from Queue, else query url server for
                # new urls.
                if not self._configobj.urlserver:
                    obj = self._crawlerqueue.get_url_data("fetcher" )
                    if obj is None:
                        if not self._configobj.blocking and self.buffer:
                            self.push_buffer()
                        else:
                            continue
                        
                    if not self.set_url_object(obj):
                        continue
                    
                else:
                    if self.receive_url() != 1:
                        # Time gap helps to reduce
                        # network errors.
                        time.sleep(0.3)
                        continue
                
                # Set status to busy 
                self._status = 1

                # Process to generate new objects
                # only after trying to push buffer
                # objects.                    
                self.process_url()
                self._loops += 1
                # Sleep for some time
                time.sleep(0.3)
                self._status = 0
        else:
            self.process_url()
            self.crawl_url()

    def process_url(self):
        """ This function downloads the data for a url and writes its files.
        It also posts the data for web pages to a data queue """

        filename = self._urlobject.get_full_filename()

        mgr = GetObject('datamanager')            
        moreinfo('Downloading file for url ', self._url)
        data = mgr.download_url(self._urlobject)

        # Add webpage links in datamgr, if we managed to
        # download the url
        base_url_obj = self._urlobject.get_base_urlobject()

        if self._urlobject.is_webpage() and data:
            # MOD: Need to localise <base href="..." links if any
            # so add a NULL entry. (Nov 30 2004 - Refer header)
            mgr.update_links(self._urlobject.get_full_filename(), None)
            url_obj = self._urlobject
            
            self._status = 2
            
            extrainfo("Parsing web page ", self._url)
            try:
                # use tidylib to clean up html data
                if self._configobj.tidyhtml:
                    import tidy
                    
                    options=dict(output_xhtml=1,indent=1, tidy_mark=1, fix_uri=1)
                    data = str(tidy.parseString( data, **options ))
                    # Sometimes tidy finds lots of errors in the
                    # page, that it returns an empty string.
                    if not data:
                        return None
                    
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
            except (htmlparser.HTMLParseError,SGMLParseError, IOError),e:
                debug(e)
                
            links = self.wp.links
            if self._configobj.images:
                links += self.wp.images

            # Fix for hanging threads - Append objects
            # to local buffer if queue was full.
            if not self._crawlerqueue.push((url_obj, links), 'fetcher'):
                if not self._configobj.blocking:                
                    self.buffer.append((url_obj, links))

class HarvestManUrlDownloader(HarvestManUrlFetcher, HarvestManUrlCrawler):
    """ This is a mixin class which does both the jobs of crawling webpages
    and download urls """

    # Created: 23 Sep 2004 for 1.4 version 
    def __init__(self, index, url_obj = None, isThread=True):
        HarvestManUrlFetcher.__init__(self, index, url_obj, isThread)

    def _initialize(self):
        HarvestManUrlFetcher._initialize(self)
        self._role = 'downloader'

    def set_url_object(self, obj):
        HarvestManUrlFetcher.set_url_object(self, obj)

    def action(self):

        if self._isThread:
            self._loops = 0

            while not self._endflag:
                obj = self._crawlerqueue.get_url_data( "downloader" )
                if obj is None: continue
                
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
            self.process_url()
            self.crawl_url()

    def process_url(self):

        # First process urls using fetcher's algorithm
        HarvestManUrlFetcher.process_url(self, False)
        # Then process using crawler's algorithm
        HarvestManUrlCrawler.process_url(self)

    def crawl_url(self):
        HarvestManUrlCrawler.crawl_url(self)
        

class PriorityQueue(Queue):
    """ Priority queue based on bisect module (courtesy: Effbot) """

    def __init__(self, maxsize=0):
        Queue.__init__(self, maxsize)
        
    def _put(self, item):
        bisect.insort(self.queue, item)
        
class HarvestManCrawlerQueue(object):
    """ This class functions as the thread safe queue
    for storing url data for tracker threads """

    def __init__(self):
        self._basetracker = None
        self._controller = None # New in 1.4
        self._flag = 0
        self._pushes = 0
        self._lockedinst = 0
        self._lasttimestamp = time.time()
        self._trackers  = []
        self._requests = 0
        self._trackerindex = 0
        self._lastblockedtime = 0
        self._numfetchers = 0
        self._numcrawlers = 0
        self.__qsize = 0
        self._baseUrlObj = None
        # Time to wait for a data operation on the queue
        # before stopping the project with a timeout.
        self._waittime = GetObject('config').projtimeout
        self._configobj = GetObject('config')
        self.url_q = PriorityQueue(4*self._configobj.maxtrackers)
        self.data_q = PriorityQueue(4*self._configobj.maxtrackers)
        
    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            return None

    def __setattr__(self, name, value):
        self.__dict__[name] = value

    def increment_lock_instance(self, val=1):
        self._lockedinst += val

    def get_locked_instances(self):
        return self._lockedinst
    
    def configure(self):
        """ Configure this class with this config object """

        try:
            self._baseUrlObj = urlparser.HarvestManUrlParser(self._configobj.url, 'normal',
                                                             0, self._configobj.url,
                                                             self._configobj.projdir)
            SetUrlObject(self._baseUrlObj)
        except urlparser.HarvestManUrlParserError, e:
            return -1

        self._baseUrlObj.is_starting_url = True
        
        if self._configobj.fastmode:
            self._basetracker = HarvestManUrlFetcher( 0, self._baseUrlObj, True )
        else:
            self._basetracker = HarvestManUrlDownloader( 0, self._baseUrlObj, False )
            
        self._trackers.append(self._basetracker)

    def crawl(self):
        """ Starts crawling for this project """

        if os.name=='nt':
            t1=time.clock()
        else:
            t1=time.time()

        # Set start time on config object
        self._configobj.starttime = t1

        if not self._configobj.urlserver:
            self.push(self._baseUrlObj, 'crawler')
        else:
            try:
                # Flush url server of any previous urls by
                # sending a flush command.
                send_url("flush", self._configobj.urlhost, self._configobj.urlport)
                send_url(str(self._baseUrlObj.index),
                         self._configobj.urlhost,
                         self._configobj.urlport)
            except socket.error, e:
                pass
            except Exception,e:
                pass

        # Start harvestman controller thread
        # (New in 1.4)
        self._controller = harvestManController()
        self._controller.start()

        if self._configobj.fastmode:
            # Create the number of threads in the config file
            # Pre-launch the number of threads specified
            # in the config file.

            # Initialize thread dictionary
            self._basetracker.setDaemon(True)
            self._basetracker.start()

            while self._basetracker.get_status() != 0:
                time.sleep(0.1)

            for x in range(1, self._configobj.maxtrackers):
                
                # Back to equality among threads
                if x % 2==0:
                    t = HarvestManUrlFetcher(x, None)
                else:
                    t = HarvestManUrlCrawler(x, None)
                    
                self.add_tracker(t)
                t.setDaemon(True)
                t.start()

            for t in self._trackers:
                
                if t.get_role() == 'fetcher':
                    self._numfetchers += 1
                elif t.get_role() == 'crawler':
                    self._numcrawlers += 1

            # bug: give the threads some time to start,
            # otherwise we exit immediately sometimes.
            time.sleep(2.0)
            
            while 1:
                time.sleep(2.0)
                if self.is_exit_condition(): break
                
            # Set flag to 1 to denote that downloading is finished.
            self._flag = 1

            self.stop_threads(noexit = True)
        else:
            self._basetracker.action()

    def get_base_tracker(self):
        """ Get the base tracker object """

        return self._basetracker

    def get_base_urlobject(self):

        return self._baseUrlObj
    
    def get_url_data(self, role):
        """ Pop url data from the queue """

        if self._flag: return None

        obj = None

        blk = self._configobj.blocking
        
        if role == 'crawler':
            try:
                if blk:
                    obj=self.data_q.get()
                else:
                    obj=self.data_q.get_nowait()
            except Empty:
                return None
                
        elif role == 'fetcher' or role=='tracker':
            try:
                if blk:
                    obj = self.url_q.get()
                else:
                    obj = self.url_q.get_nowait()
            except Empty:
                return None
            
        self._lasttimestamp = time.time()        

        self._requests += 1
        return obj

    def __get_num_blocked_threads(self):

        blocked = 0
        for t in self._trackers:
            if not t.has_work(): blocked += 1

        return blocked

    def get_num_alive_threads(self):

        live = 0
        for t in self._trackers:
            if t.isAlive(): live += 1

        return live
        
    def __get_num_locked_crawler_threads(self):

        locked = 0
        for t in self._trackers:
            if t.get_role() == 'crawler':
                if t.is_locked(): locked += 1

        return locked

    def __get_num_locked_fetcher_threads(self):
        
        locked = 0
        for t in self._trackers:
            if t.get_role() == 'fetcher':
                if t.is_locked(): locked += 1

        return locked
    
    def add_tracker(self, tracker):
        self._trackers.append( tracker )
        self._trackerindex += 1

    def remove_tracker(self, tracker):
        self._trackers.remove(tracker)
        
    def get_last_tracker_index(self):
        return self._trackerindex
    
    def print_busy_tracker_info(self):
        
        for t in self._trackers:
            if t.has_work():
                print t,' =>', t.getUrl()

            
    def is_locked_up(self, role):
         """ The queue is considered locked up if all threads
         are waiting to push data, but none can since queue
         is already full, and no thread is popping data. This
         is a deadlock condition as the program cannot go any
         forward without creating new threads that will pop out
         some of the data (We need to take care of it by spawning
         new threads which can pop data) """

         locked = 0
         
         if role == 'fetcher':
             locked = self.__get_num_locked_fetcher_threads()
             if locked == self._numfetchers - 1:
                 return True
         elif role == 'crawler':
             locked = self.__get_num_locked_crawler_threads()
             if locked == self._numcrawlers - 1:
                 return True             

         return False
     
    def is_exit_condition(self):
        """ Exit condition is when there are no download
        sub-threads running and all the tracker threads
        are blocked or if the project times out """

        dmgr = GetObject('datamanager')
            
        currtime = time.time()
        last_thread_time = dmgr.last_download_thread_report_time()

        if last_thread_time > self._lasttimestamp:
            self._lasttimestamp = last_thread_time
            
        timediff = currtime - self._lasttimestamp

        is_blocked = self.is_blocked()
        if is_blocked:
            self._lastblockedtime = time.time()
            
        has_running_threads = dmgr.has_download_threads()
        timed_out = False

        # If the trackers are blocked, but waiting for sub-threads
        # to finish, kill the sub-threads.
        if is_blocked and has_running_threads:
            # Find out time difference between when trackers
            # got blocked and curr time. If greater than 1 minute
            # Kill hanging threads
            timediff2 = currtime - self._lastblockedtime
            if timediff2 > 60.0:
                moreinfo("Killing download threads ...")
                dmgr.kill_download_threads()
            
        if is_blocked and not has_running_threads:
            return True
        
        if timediff > self._waittime:
            timed_out = True
        
        if timed_out:
            moreinfo("Project", self._configobj.project, "timed out.")
            moreinfo('(Time since last data operation was', timediff, 'seconds)')
            return True

        return False
        
    def is_blocked(self):
        """ The queue is considered blocked if all threads
        are waiting for data, and no data is coming """

        blocked = self.__get_num_blocked_threads()
        
        if blocked == len(self._trackers):
            return True
        else:
            return False

    def is_fetcher_queue_full(self):
        """ Check whether the fetcher queue is full """

        if self.__get_num_locked_fetcher_threads() == self._numfetchers - 1:
            return True
        
        return False

    def is_crawler_queue_full(self):
        """ Check whether the crawler queue is full """

        if self.__get_num_locked_crawler_threads() == self._numcrawlers - 1:
            return True
        
        return False        
        
    def push(self, obj, role):
        """ Push trackers to the queue """

        if self._flag: return

        # 1.4 alpha 3 - Big fix for hanging threads.
        # Instead of perpetually waiting at queues
        # (blocking put), the threads now do a mix
        # of unblocking put plus local buffers.

        # Each thread tries to put data to buffer
        # for maximum five attempts, each separated
        # by a 0.5 second gap.
        ntries, status = 0, 0

        if role == 'crawler' or role=='tracker' or role =='downloader':
            while ntries < 5:
                try:
                    ntries += 1
                    self.url_q.put_nowait((obj.get_priority(), obj.index))
                    status = 1
                    break
                except Full:
                    time.sleep(0.5)
                    
                    
        elif role == 'fetcher':
            stuff = (obj[0].get_priority(), (obj[0].index, obj[1]))
            while ntries < 5:
                try:
                    ntries += 1
                    self.data_q.put_nowait(stuff)
                    status = 1
                    break
                except Full:
                    time.sleep(0.5)
                    
        self._pushes += 1
        self._lasttimestamp = time.time()

        return status
    
    def stop_threads(self, noexit=False):
        """ Stop all running threads and clean
        up the program. This function is called
        for a normal exit of HravestMan """

        moreinfo("Ending Project", self._configobj.project,'...')
        for t in self._trackers:
            t.stop()

        # Stop controller
        self._controller.stop()
        
        # Exit the system
        if not noexit:
            sys.exit(2)

    def terminate_threads(self):
        """ Kill all current running threads and
        stop the program. This function is called
        for an abnormal exit of HarvestMan """

        # Created: 23 Nov 2004
        # Kill the individual download threads
        mgr = GetObject('datamanager')
        mgr.kill_download_threads()

        # Stop controller thread
        self._controller.stop()
 
        # If not fastmode, then there are no
        # further threads!
        if not self._configobj.fastmode:
            self._basetracker.stop()
            return -1

        # Kill tracker threads
        self.__kill_tracker_threads()
    
    def __kill_tracker_threads(self):
        """ This function kills running tracker threads """

        moreinfo('Terminating project ',self._configobj.project,'...')
        self._flag=1

        count =0

        debug('Current running threads => ', threading.activeCount())
        debug('Current tracker count => ', len(self._trackers))
        extrainfo('Waiting for threads to clean up ')

        for tracker in self._trackers:
            count += 1
            sys.stdout.write('...')

            if count % 10 == 0: sys.stdout.write('\n')

            try:
                tracker.terminate()
                tracker.join()
                del tracker
            except HarvestManUrlCrawlerException, e:
                pass
            except AssertionError, e:
                print e, '=> ', tracker
            except ValueError, e:
                print e, '=> ', tracker

