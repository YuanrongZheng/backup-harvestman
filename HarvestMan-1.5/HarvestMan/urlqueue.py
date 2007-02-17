# -- coding: latin-1
""" urlqueue.py - Module which controls queueing of urls
    created by crawler threads. This is part of the HarvestMan
    program.

    Author: Anand B Pillai <abpillai at gmail dot com>
    
    Modification History

     Anand Jan 12 2005 -   Created this module, by splitting urltracker.py
     Aug 11 2006  Anand    Checked in changes for reducing CPU utilization.

     Aug 22 2006  Anand    Changes for fixing single-thread mode.

   Copyright (C) 2005 Anand B Pillai.     

"""

__version__ = '1.5 b1'
__author__ = 'Anand B Pillai'

import bisect
import Queue
import crawler
import time
import threading
import sys, os
import copy

from common.common import *

class PriorityQueue(Queue.Queue):
    """ Priority queue based on bisect module (courtesy: Effbot) """

    def __init__(self, maxsize=0):
        Queue.Queue.__init__(self, maxsize)

    def _init(self, maxsize):
        self.maxsize = maxsize
        self.queue = MyDeque()
        
    def _put(self, item):
        bisect.insort(self.queue, item)

    def _qsize(self):
        return len(self.queue)

    def _empty(self):
        return not self.queue

    def _full(self):
        return self.maxsize>0 and len(self.queue) == self.maxsize

    def _get(self):
        return self.queue.pop(0)    
    
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
        self._baseUrlObj = None
        # Time to wait for a data operation on the queue
        # before stopping the project with a timeout.
        self._waittime = GetObject('config').projtimeout
        self._configobj = GetObject('config')
        if self._configobj.fastmode:
            self.url_q = PriorityQueue(4*self._configobj.maxtrackers)
            self.data_q = PriorityQueue(4*self._configobj.maxtrackers)
        else:
            self.url_q = PriorityQueue(0)
            self.data_q = PriorityQueue(0)
            
        # Local buffer - new in 1.4.5
        self.buffer = []
        # Condition object for exit condition checking
        # loop - to halt exit condition check, acquire this lock
        self._cond = threading.Condition(threading.Lock())

    def get_state(self):

        # Return state of this object,
        # it's queues and the threads it contain
        d = {}
        d['_pushes'] = self._pushes
        d['_lockedinst'] = self._lockedinst
        d['_lasttimestamp'] = self._lasttimestamp
        d['_requests'] = self._requests
        d['_lastblockedtime'] = self._lastblockedtime
        d['buffer'] = self.buffer
        d['_baseUrlObj'] = self._baseUrlObj
        
        # For the queues, get their contents
        q1 = self.url_q.queue
        # This is an index of priorities and url indices
        d['url_q'] = copy.deepcopy(q1)
        q2 = self.data_q.queue
        d['data_q'] = copy.deepcopy(q2)

        # Thread dictionary
        tdict = {}
        
        # For threads get their information
        for t in self._trackers:
            d2 = {}
            d2['_status'] = t._status
            d2['_loops'] = t._loops          
            
            d2['_url'] = t._url
            d2['_urlobject'] = t._urlobject
            d2['buffer'] = t.buffer
            d2['role'] = t.get_role()
            if t.get_role() == 'crawler':
                d2['links'] = t.links
            elif t.get_role() == 'fetcher':
                pass

            tdict[t._index] = d2
            
        d['threadinfo'] = tdict
        
        return copy.deepcopy(d)

    def set_state(self, state):
        """ Set state to a previous saved state """

        # Get base url object
        self._baseUrlObj = state.get('_baseUrlObj')
        # If base url object is None, we cannot proceed
        # so return -1
        if self._baseUrlObj is None:
            return -1
        
        # Set state for simple data-members
        self._pushes = state.get('_pushes',0)
        self._lockedinst = state.get('_lockedinst', 0)
        self._lasttimestamp = state.get('_lasttimestamp', time.time())
        self._requests = state.get('_requests', 0)
        self._lastblockedtime = state.get('_lastblockedtime', 0)
        self.buffer = state.get('buffer', [])

        # Set state for queues
        self.url_q.queue = state.get('url_q', MyDeque())
        
        self.data_q.queue = state.get('data_q', MyDeque())

        # If both queues are empty, we don't have anything to do
        if len(self.url_q.queue)==0 and len(self.data_q.queue)==0:
            moreinfo('Size of data/url queues are zero, nothing to re-run')
            return -1
        
        cfg = GetObject('config')
        self._configobj = cfg
        
        if cfg.fastmode:
            # Create threads and set their state
            for idx,tdict in state.get('threadinfo').items():
                role = tdict.get('role')
                t = None
                
                if role == 'fetcher':
                    t = crawler.HarvestManUrlFetcher(idx, None)
                    self._numfetchers += 1
                elif role == 'crawler':
                    t = crawler.HarvestManUrlCrawler(idx, None)
                    t.links = tdict.get('links')
                    self._numcrawlers += 1

                if t:
                    t._status = tdict.get('_status')
                    t._loops = tdict.get('_loops')
                    t._url = tdict.get('_url')
                    t._urlobject = tdict.get('_urlobject')
                    t.buffer = tdict.get('buffer')
                    if t._urlobject: t._resuming = True
                    
                    self.add_tracker(t)
                    t.setDaemon(True)

            # Set base tracker
            self._basetracker = self._trackers[0]

    def increment_lock_instance(self, val=1):
        self._lockedinst += val

    def get_locked_instances(self):
        return self._lockedinst

    def get_controller(self):
        """ Return the controller thread object """

        return self._controller
        
    def configure(self):
        """ Configure this class with this config object """

        try:
            import urlparser
            
            # urlparser.HarvestManUrlParser.reset_IDX()
            
            self._baseUrlObj = urlparser.HarvestManUrlParser(self._configobj.url, 'normal',
                                                             0, self._configobj.url,
                                                             self._configobj.projdir)
            SetUrlObject(self._baseUrlObj)
        except urlparser.HarvestManUrlParserError:
            return False

        self._baseUrlObj.starturl = True
        
        if self._configobj.fastmode:
            self._basetracker = crawler.HarvestManUrlFetcher( 0, self._baseUrlObj, True )
        else:
            # Disable usethreads
            self._configobj.usethreads = False
            # Disable blocking
            self._configobj.blocking = False
            self._basetracker = crawler.HarvestManUrlDownloader( 0, self._baseUrlObj, False )
            
        self._trackers.append(self._basetracker)
        return True

    def mainloop(self):
        """ The loop where this object spends
        most of its time. However it is not
        an idle loop """

        # New in 1.4.5, moving code from
        # the crawl method.
        count=0

        numstops = 3
        
        while 1:
            if self.is_exit_condition():
                count += 1
            
            if count==numstops:
                break

            time.sleep(1.0)

    def restart(self):
        """ Alternate method to start from a previous restored state """

        # Start harvestman controller thread
        import datamgr
        
        self._controller = datamgr.harvestManController()
        self._controller.start()

        # Start base tracker
        self._basetracker.start()
        time.sleep(2.0)
        
        for t in self._trackers[1:]:
            try:
                t.start()
            except AssertionError, e:
                logconsole(e)
                pass

        time.sleep(2.0)
        self.mainloop()        
        # Set flag to 1 to denote that downloading is finished.
        self._flag = 1
            
        self.stop_threads(noexit = True)
        
    def crawl(self):
        """ Starts crawling for this project """

        # Reset flag
        self._flag = 0

        # Clear the event flag
        # self.exitobj.clear()
        
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
            except:
                pass

        if self._configobj.fastmode:

            # Start harvestman controller thread
            import datamgr
            
            self._controller = datamgr.harvestManController()
            self._controller.start()
            
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
                    t = crawler.HarvestManUrlFetcher(x, None)
                else:
                    t = crawler.HarvestManUrlCrawler(x, None)

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

            self.mainloop()
            
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
            if blk:
                obj=self.data_q.get()
            else:
                for i in xrange(5):
                    try:
                        obj=self.data_q.get_nowait()
                        break
                    except Queue.Empty:
                        time.sleep(0.3)
                        continue
                
        elif role == 'fetcher' or role=='tracker':
            if blk:
                obj = self.url_q.get()
            else:
                for i in xrange(5):
                    try:
                        obj = self.url_q.get_nowait()
                        break
                    except Queue.Empty:
                        time.sleep(0.3)
                        continue
            
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

        need_to_exit = False
        
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
            need_to_exit = True
        
        if timediff > self._waittime:
            timed_out = True
        
        if timed_out:
            moreinfo("Project", self._configobj.project, "timed out.")
            moreinfo('(Time since last data operation was', timediff, 'seconds)')
            need_to_exit = True


        return need_to_exit
        
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

    def dead_thread_callback(self, t):
        """ Call back function called by a thread if it
        dies with an exception. This class then creates
        a fresh thread, migrates the data of the dead
        thread to it """

        # First find out the type
        role = t.get_role()
        new_t = None
        
        if role == 'fetcher':
            new_t = crawler.HarvestManUrlFetcher(t.get_index(), None)
        elif role == 'crawler':
            new_t = crawler.HarvestManUrlCrawler(t.get_index(), None)

        # Migrate data and start thread
        if new_t:
            new_t._status = t._status
            new_t._url = t._url
            new_t._urlobject = t._urlobject
            new_t._loops = t._loops
            new_t.buffer = copy.deepcopy(t.buffer)
            # If this is a crawler get links also
            if role == 'crawler':
                new_t.links = t.links[:]

            # Replace dead thread in the list
            idx = self._trackers.index(t)
            self._trackers[idx] = new_t
            new_t._resuming = True
            new_t.start()
            time.sleep(2.0)
        else:
            # Could not make new thread, so decrement
            # count of threads.
            if role == 'fetcher':
                self._numfetchers -= 1
            elif role == 'crawler':
                self._numcrawlers -= 1
                
                
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
                    self.url_q.put_nowait((obj.priority, obj.index))
                    status = 1
                    break
                except Queue.Full:
                    time.sleep(0.5)
                    
        elif role == 'fetcher':
            stuff = (obj[0].priority, (obj[0].index, obj[1]))
            while ntries < 5:
                try:
                    ntries += 1
                    self.data_q.put_nowait(stuff)
                    status = 1
                    break
                except Queue.Full:
                    time.sleep(0.5)
                    
        self._pushes += 1
        self._lasttimestamp = time.time()

        return status
    
    def stop_threads(self, noexit=False):
        """ Stop all running threads and clean
        up the program. This function is called
        for a normal exit of HravestMan """

        if self._configobj.project:
            moreinfo("Ending Project", self._configobj.project,'...')
        for t in self._trackers:
            try:
                t.terminate()
                t.join()
            except crawler.HarvestManUrlCrawlerException, e:
                pass
            except Exception, e:
                pass

        # Stop controller
        self._controller.stop()

        # Reset the thread list
        self.empty_list()
        
        # Exit the system
        if not noexit:
            try:
                sys.exit(0)
            except Exception, e:
                pass

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
 
        # Kill tracker threads
        self.__kill_tracker_threads()
    
    def __kill_tracker_threads(self):
        """ This function kills running tracker threads """

        moreinfo('Terminating project ',self._configobj.project,'...')
        self._flag=1

        count =0

        debug('Waiting for threads to clean up ')

        for tracker in self._trackers:
            count += 1
            sys.stdout.write('...')

            if count % 10 == 0: sys.stdout.write('\n')

            try:
                tracker.terminate()
                tracker.join()
            except crawler.HarvestManUrlCrawlerException, e:
                pass
            except AssertionError, e:
                logconsole(str(e))
            except ValueError, e:
                logconsole(str(e))

            del tracker
            
        # Reset the thread list
        self.empty_list()
        
    def empty_list(self):
        """ Remove thread objects from the thread list """

        self._trackers = []
        self._basetracker = None

