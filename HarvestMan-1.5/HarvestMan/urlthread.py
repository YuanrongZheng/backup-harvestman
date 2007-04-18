# -- coding: latin-1
""" urlthread.py - Url thread downloader module.
    Has two classes, one for downloading of urls and another
    for managing the url threads.

    This module is part of the HarvestMan program.

    Author: Anand B Pillai (abpillai at gmail dot com).
    
    Modification History

    Jan 10 2006  Anand  Converted from dos to unix format (removed Ctrl-Ms).
    Jan 20 2006  Anand  Small change in printing debug info in download
                        method.

    Mar 05 2007  Anand  Implemented http 304 handling in notify(...).

    Apr 09 2007  Anand  Added check to make sure that threads are not
                        re-started for the same recurring problem.
    
    Copyright (C) 2004 Anand B Pillai.

"""

__version__ = '1.5 b1'
__author__ = 'Anand B Pillai'

import os, sys
import math
import time
import threading
import copy

from collections import deque
from Queue import Queue, Full, Empty
from common.common import *

class HarvestManUrlThreadInterrupt(Exception):
    """ Interrupt raised to kill a harvestManUrlThread class's object """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class HarvestManUrlThread(threading.Thread):
    """ Class to download a url in a separate thread """

    # The last error which caused a thread instance to die
    _lasterror = None
    
    def __init__(self, name, timeout, threadpool):
        """ Constructor, the constructor takes a url, a filename
        , a timeout value, and the thread pool object pooling this
        thread """

        # url Object (This is an instance of urlPathParser class)
        self.__urlobject = None
        # thread queue object pooling this thread
        self.__pool = threadpool
        # max lifetime for the thread
        self.__timeout = timeout
        # start time of thread
        self.__starttime = 0
        # sleep time
        self.__sleepTime = 1.0
        # error dictionary
        self.__error = {}
        # download status flag
        self.__downloadstatus = 0
        # busy flag
        self.__busyflag = False
        # end flag
        self.__endflag = False
        # Url data, only used for mode 1
        self.__data = ''
        # initialize threading
        threading.Thread.__init__(self, None, None, name)
        
    def get_error(self):
        """ Get error value of this thread """

        return self.__error

    def get_status(self):
        """ Get the download status of this thread """

        return self.__downloadstatus

    def get_data(self):
        """ Return the data of this thread """

        return self.__data
    
    def set_status(self, status):
        """ Set the download status of this thread """

        self.__downloadstatus = status

    def is_busy(self):
        """ Get busy status for this thread """

        return self.__busyflag

    def set_busy_flag(self, flag):
        """ Set busy status for this thread """

        self.__busyflag = flag

    def join(self):
        """ The thread's join method to be called
        by other threads """

        threading.Thread.join(self, self.__timeout)

    def terminate(self):
        """ Kill this thread """

        self.stop()
        msg = 'Download thread, ' + self.getName() + ' killed!'
        raise HarvestManUrlThreadInterrupt, msg

    def stop(self):
        """ Stop this thread """

        # If download was not completed, push-back object
        # to the pool.
        if self.__downloadstatus==0 and self.__urlobject:
            self.__pool.push(self.__urlobject)
            
        self.__endflag = True

    def download(self, url_obj):
        """ Download this url """

        # Set download status
        self.__downloadstatus = 0
        
        url = url_obj.get_full_url()
        server = url_obj.get_domain()

        if not url_obj.trymultipart:
            if url_obj.is_image():
                info('Downloading image ...', url)
            else:
                info('Downloading url ...', url)
        else:
            startrange = url_obj.range[0]
            endrange = url_obj.range[-1]            
            info('Downloading url %s, byte range(%d - %d)' % (url,startrange,endrange))
            
        server = url_obj.get_domain()

        conn_factory = GetObject('connectorfactory')
        # This call will block if we exceed the number of connections
        # moreinfo("Creating connector for url ", urlobj.get_full_url())
        conn = conn_factory.create_connector( server )

        if not url_obj.trymultipart:
            res = conn.save_url(url_obj)
        else:
            res = conn.wrapper_connect(url_obj)
            # This has a different return value.
            # 0 indicates data was downloaded fine.
            if res==0: res=1
            self.__data = conn.get_data()

        # Remove the connector from the factory
        conn_factory.remove_connector(server)

        # Set this as download status
        self.__downloadstatus = res
        
        # get error flag from connector
        self.__error = conn.get_error()

        del conn
        
        # Notify thread pool
        self.__pool.notify(self)

        if res != 0:
            if not url_obj.trymultipart:            
                extrainfo('Finished download of ', url)
            else:
                startrange = url_obj.range[0]
                endrange = url_obj.range[-1]                            
                extrainfo('Finished download of byte range(%d - %d) of %s' % (startrange,endrange, url))
        else:
            extrainfo('Failed to download URL',url)

    def run(self):
        """ Run this thread """

        while not self.__endflag:
            try:
                if os.name=='nt' or sys.platform == 'win32':
                  self.__starttime=time.clock()
                else:
                    self.__starttime=time.time()

                url_obj = self.__pool.get_next_urltask()

                if self.__pool.check_duplicates(url_obj):
                    continue

                if not url_obj:
                    time.sleep(0.1)
                    continue

                # set busy flag to 1
                self.__busyflag = True

                # Save reference
                self.__urlobject = url_obj

                filename, url = url_obj.get_full_filename(), url_obj.get_full_url()
                if not filename and not url:
                    return

                # Perf fix: Check end flag
                # in case the program was terminated
                # between start of loop and now!
                if not self.__endflag: self.download(url_obj)
                # reset busyflag
                self.__busyflag = False
            except Exception, e:
                # Now I am dead - so I need to tell the pool
                # object to migrate my data and produce a new thread.
                
                # See class for last error. If it is same as
                # this error, don't do anything since this could
                # be a programming error and will send us into
                # a loop...
                if str(self.__class__._lasterror) == str(e):
                    debug('Looks like a repeating error, not trying to restart worker thread %s' % (str(self)))
                else:
                    self.__class__._lasterror = e
                    self.__pool.dead_thread_callback(self)
                    extrainfo('Worker thread %s has died due to error: %s' % (str(self), str(e)))


    def get_url(self):

        if self.__urlobject:
            return self.__urlobject.get_full_url()

        return ""

    def get_filename(self):

        if self.__urlobject:
            return self.__urlobject.get_full_filename()

        return ""

    def get_urlobject(self):
        """ Return this thread's url object """

        return self.__urlobject

    def set_urlobject(self, urlobject):
            
        self.__urlobject = urlobject
        
    def get_start_time(self):
        """ Return the start time of current download """

        return self.__starttime

    def set_start_time(self, starttime):
        """ Return the start time of current download """

        self.__starttime = starttime
    
    def get_elapsed_time(self):
        """ Get the time taken for this thread """

        now=0.0

        if os.name=='nt' or sys.platform=='win32':
            now=time.clock()
        else:
            now=time.time()

        fetchtime=float(math.ceil((now-self.__starttime)*100)/100)
        return fetchtime

    def long_running(self):
        """ Find out if this thread is running for a long time
        (more than given timeout) """

        # if any thread is running for more than <timeout>
        # time, return TRUE
        return (self.get_elapsed_time() > self.__timeout)

    def set_timeout(self, value):
        """ Set the timeout value for this thread """

        self.__timeout = value

        
class HarvestManUrlThreadPool(Queue):
    """ Thread group/pool class to manage download threads """

    def __init__(self):
        """ Initialize this class """

        # list of spawned threads
        self.__threads = []
        # list of url tasks
        self.__tasks = []

        cfg = GetObject('config')
        # Maximum number of threads spawned
        self.__numthreads = cfg.threadpoolsize
        self.__timeout = cfg.timeout
        
        # Last thread report time
        self._ltrt = 0.0
        # Local buffer
        self.buffer = []
        # Data dictionary for multi-part downloads
        # Keys are URLs and value is the data
        self.__multipartdata = {}
        # Status of URLs being downloaded in
        # multipart. Keys are URLs
        self.__multipartstatus = {}
        # Number of parts
        self.__parts = GetObject('config').numparts
        # Condition object
        self._cond = threading.Condition(threading.Lock())        
        Queue.__init__(self, self.__numthreads + 5)
        
    def get_state(self):
        """ Return a snapshot of the current state of this
        object and its containing threads for serializing """
        
        d = {}
        d['buffer'] = self.buffer
        d['queue'] = self.queue
        
        tdict = {}
        
        for t in self.__threads:
            d2 = {}
            d2['__urlobject'] = t.get_urlobject()
            d2['__busyflag'] = t.is_busy()
            d2['__downloadstatus'] = t.get_status()
            d2['__starttime'] = t.get_start_time()

            tdict[t.getName()]  = d2

        d['threadinfo'] = tdict
        
        return copy.deepcopy(d)

    def set_state(self, state):
        """ Set state to a previous saved state """

        cfg = GetObject('config')
        # Maximum number of threads spawned
        self.__numthreads = cfg.threadpoolsize
        self.__timeout = cfg.timeout
        self.__parts = cfg.numparts
        
        self.buffer = state.get('buffer',[])
        self.queue = state.get('queue', deque([]))
        
        for name,tdict in state.get('threadinfo').items():
            fetcher = HarvestManUrlThread(name, self.__timeout, self)
            fetcher.set_urlobject(tdict.get('__urlobject'))
            fetcher.set_busy_flag(tdict.get('__busyflag', False))
            fetcher.set_status(tdict.get('__downloadstatus', 0))
            fetcher.set_start_time(tdict.get('__starttime', 0))            
            
            fetcher.setDaemon(True)
            self.__threads.append(fetcher)
            
    def start_threads(self):
        """ Start threads if they are not running """

        for t in self.__threads:
            try:
                t.start()
            except AssertionError, e:
                pass
            
    def spawn_threads(self):
        """ Start the download threads """

        for x in range(self.__numthreads):
            name = 'Worker-'+ str(x+1)
            fetcher = HarvestManUrlThread(name, self.__timeout, self)
            fetcher.setDaemon(True)
            # Append this thread to the list of threads
            self.__threads.append(fetcher)
            fetcher.start()

    def download_urls(self, listofurlobjects):
        """ Method to download a list of urls.
        Each member is an instance of a urlPathParser class """

        for urlinfo in listofurlobjects:
            self.push(urlinfo)

    def __get_num_blocked_threads(self):

        blocked = 0
        for t in self.__threads:
            if not t.is_busy(): blocked += 1

        return blocked

    def is_blocked(self):
        """ The queue is considered blocked if all threads
        are waiting for data, and no data is coming """

        blocked = self.__get_num_blocked_threads()

        if blocked == len(self.__threads):
            return True
        else:
            return False

    def push(self, urlObj):
        """ Push the url object and start downloading the url """

        # unpack the tuple
        try:
            filename, url = urlObj.get_full_filename(), urlObj.get_full_url()
        except:
            return

        # Wait till we have a thread slot free, and push the
        # current url's info when we get one
        try:
            self.put( urlObj )
            # If this URL was multipart, mark it as such
            self.__multipartstatus[url] = False
        except Full:
            self.buffer.append(urlObj)
        
    def get_next_urltask(self):

        try:
            if len(self.buffer):
                # Get last item from buffer
                return buffer.pop()
            else:
                return self.get()
        except Empty:
            return None

    def notify(self, thread):
        """ Method called by threads to notify that they
        have finished """

        try:
            self._cond.acquire()
            # Mark the time stamp (last thread report time)
            self._ltrt = time.time()

            urlObj = thread.get_urlobject()

            # See if this was a multi-part download
            if urlObj.trymultipart:
                # print 'Thread %s reported with data range (%d-%d)!' % (thread, urlObj.range[0], urlObj.range[-1])
                # Get data
                data = thread.get_data()

                url = urlObj.get_full_url()

                if url in self.__multipartdata:
                    datalist = self.__multipartdata[url]
                    datalist.append((urlObj.range[0],data))
                else:
                    datalist = []
                    datalist.append((urlObj.range[0],data))
                    self.__multipartdata[url] = datalist

                #print 'Length of data list is',len(datalist)
                if len(datalist)==self.__parts:
                    # Sort the data list  according to byte-range
                    datalist.sort()
                    # Download of this URL is complete...
                    # print 'Download of %s is complete...' % urlObj.get_full_url()
                    data = ''.join([item[1] for item in datalist])
                    self.__multipartdata['data:' + url] = data
                    self.__multipartstatus[url] = True

            # if the thread failed, update failure stats on the data manager
            dmgr = GetObject('datamanager')

            err = thread.get_error()

            tstatus = thread.get_status()

            # Either file was fetched or file was uptodate
            if err.get('number',0) in (0, 304):
                # thread succeeded, increment file count stats on the data manager
                dmgr.update_file_stats( urlObj, tstatus)
            else:
                dmgr.update_failed_files( urlObj )
        finally:
            self._cond.release()
            

    def has_busy_threads(self):
        """ Return whether I have any busy threads """

        val=0
        for thread in self.__threads:
            if thread.is_busy():
                val += 1

        return val

    def locate_thread(self, url):
        """ Find a thread which downloaded a certain url """

        for x in self.__threads:
            if not x.is_busy():
                if x.get_url() == url:
                    return x

        return None

    def locate_busy_threads(self, url):
        """ Find all threads which are downloading a certain url """

        threads=[]
        for x in self.__threads:
            if x.is_busy():
                if x.get_url() == url:
                    threads.append(x)

        return threads

    def check_duplicates(self, urlobj):
        """ Avoid downloading same url file twice.
        It can happen that same url is linked from
        different web pages. We query any thread which
        has downloaded this url, and copy the file to
        the file location of the new download request """

        filename = urlobj.get_full_filename()
        url = urlobj.get_full_url()

        # First check if any thread is in the process
        # of downloading this url.
        if self.locate_thread(url):
            debug('Another thread is downloading %s' % url)
            return True
        
        # Get data manager object
        dmgr = GetObject('datamanager')

        if dmgr.is_file_downloaded(filename):
            return True

        return False

    def end_hanging_threads(self):
        """ If any download thread is running for too long,
        kill it, and remove it from the thread pool """

        pool=[]
        for thread in self.__threads:
            if thread.long_running(): pool.append(thread)

        for thread in pool:
            extrainfo('Killing hanging thread ', thread)
            # remove this thread from the thread list
            self.__threads.remove(thread)
            # kill it
            try:
                thread.terminate()
            except HarvestManUrlThreadInterrupt:
                pass

            del thread

    def end_all_threads(self):
        """ Kill all running threads """

        for t in self.__threads:
            try:
                t.terminate()
                del t
            except HarvestManUrlThreadInterrupt, e:
                extrainfo(str(e))
                pass

    def remove_finished_threads(self):
        """ Clean up all threads that have completed """

        for thread in self.__threads:
            if not thread.is_busy():
                self.__threads.remove(thread)
                del thread

    def last_thread_report_time(self):
        """ Return the last thread reported time """

        return self._ltrt

    def get_download_status(self, url):
        """ Get status of multipart downloads """

        return self.__multipartstatus.get(url, False)

    def get_url_data(self, url):
        """ Return data for multipart downloads """

        return self.__multipartdata.get('data:'+url, '')

    def dead_thread_callback(self, t):
        """ Call back function called by a thread if it
        dies with an exception. This class then creates
        a fresh thread, migrates the data of the dead
        thread to it """

        try:
            self._cond.acquire()
            new_t = HarvestManUrlThread(t.getName(), self.__timeout, self)
            # Migrate data and start thread
            if new_t:
                new_t.set_urlobject(t.get_urlobject())
                # Replace dead thread in the list
                idx = self.__threads.index(t)
                self.__threads[idx] = new_t
                new_t.start()
            else:
                # Could not make new thread, remove
                # current thread anyway
                self.__threads.remove(t)
        finally:
            self._cond.release()                
                    
