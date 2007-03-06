# -- coding: latin-1
""" urlserver.py - Asynchronous and Synchronous socket servers
    serving urls for HarvestMan. This module is part of the
    HarvestMan program.

    Author : Anand B Pillai (abpillai at gmail dot com).


    Jan 10 2006  Anand  Converted from dos to unix format (removed Ctrl-Ms).
    Mar 02 2007  Anand  Added support for crawler threads. Now enabling
                        url server makes all the flow go through the url
                        server.

   Copyright (C) 2006 Anand B Pillai.

"""

__version__ = '1.5 b1'
__author__ = 'Anand B Pillai'

import select
import asyncore, socket, threading, SocketServer
from urlqueue import PriorityQueue
from Queue import Empty
from common.common import *
import bisect

class AsyncoreThread(threading.Thread):
    """ Asyncore thread class """

    def __init__(self, timeout=30.0, use_poll=0,map=None):
        self.flag=True
        self.timeout=timeout
        self.use_poll=use_poll
        self.map=map
        threading.Thread.__init__(self, None, None, 'asyncore thread')
        
    def run(self):

        self.loop()

    def loop(self):

        if not self.map:
            self.map = asyncore.socket_map

        if self.use_poll:
            if hasattr(select, 'poll'):
                poll_fun = asyncore.poll3
            else:
                poll_fun = asyncore.poll2
        else:
            poll_fun=asyncore.poll

        while self.map and self.flag:
            poll_fun(self.timeout,self.map)

    def stop(self):
        self.flag=False
        self.map=None

class MyTCPServer(SocketServer.ThreadingTCPServer):

    def __init__(self, host, port):
        SocketServer.ThreadingTCPServer.__init__(self, (host, port), harvestManUrlHandler)
        self.host, self.port = self.socket.getsockname()
        # For storing data from crawlers
        self.urls = PriorityQueue(0)
        # For storing data from fetchers
        self.urls2 = PriorityQueue(0)
        self.urlmap = {}
        self.flag = True
        
    def serve_forever(self):
        pass
            
    def get_port(self):
        return self.port

    def seturl(self, url):
        self.urlmap['lasturl'] = url

    def seturllist(self, urllist):
        self.urlmap['lastlist'] = urllist
        
    def geturl(self):
        return self.urlmap['lasturl']

    def geturllist(self):
        return self.urlmap['lastlist']
    
class HarvestManSimpleUrlServer(threading.Thread):
    """ A simple url server based upon SocketServer's
    threading TCP server """

    def __init__(self, host, port):
        threading.Thread.__init__(self, None, None, 'server thread')        
        self.server = MyTCPServer(host, port)
        self.port = self.server.get_port()
        self.flag = True
        
    def run(self):
        while self.flag:
            self.server.handle_request()
        
    def get_port(self):
        return self.port

    def stop(self):
        self.server.socket.close()
        self.flag = False
        raise Exception
    
class harvestManUrlHandler(SocketServer.BaseRequestHandler):
    """ The Request handler class for harvestManSimpleUrlServer """

    urls = []

    def handle(self):

        while True:
            data = self.request.recv(8192)

            if data:
                # Replace any newlines
                data.strip()

                if data in ('ping', 'flush', 'get last url', 'get url','get list','get last list'):
                    if data.lower() == 'ping':
                        self.request.sendall('ping')
                    elif data.lower() == "flush":
                        while True:
                            try:
                                self.server.urls.get_nowait()
                            except Empty:
                                break
                        self.request.sendall("Flushed Repository")
                    elif data.lower() == "get last url":
                        self.request.sendall((self.server.geturl()).strip())
                    elif data.lower() == "get last list":
                        self.request.sendall((self.server.geturllist()).strip())                    
                    elif data.lower() == "get url":
                        try:
                            prior, url=self.server.urls.get_nowait()
                            self.server.seturl(url)
                            self.request.sendall(url.strip())                        
                        except Empty:
                            self.request.sendall("empty")
                    elif data.lower() == 'get list':
                        try:
                            prior, rest = self.server.urls2.get_nowait()
                            self.server.seturllist(rest)
                            self.request.sendall(rest.strip())
                        except Empty:
                            self.request.sendall('empty')
                else:
                    # Split w.r.t '#'
                    pieces = data.split('#')
                    # print 'Pieces=>',pieces
                    if len(pieces)==2:
                        # Sent by crawler, put to urls queue
                        self.server.urls.put_nowait(pieces)
                    else:
                        # Sent by fetcher, put to urls2 queue
                        self.server.urls2.put_nowait((pieces[0], '#'.join(pieces[1:])))

                    self.request.sendall("Recieved")
            else:
                self.request.close()            
                break

    
class HarvestManUrlServer(asyncore.dispatcher_with_send):
    """ An asynchronous url server class for HarvestMan.
    This class can replace the url queue and work as a url
    server multiplexing several url requests simultaneously """

    def __init__(self, host, port, protocol='tcp'):
        # For storing data from crawlers
        self.urls = PriorityQueue(0)
        # For storing data from fetchers
        self.urls2 = PriorityQueue(0)
        self.port = port
        self.host = host
        self.protocol = protocol
        self.urlmap = {}
        self._lock = threading.Condition(threading.RLock())
        
        asyncore.dispatcher_with_send.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.bind((self.host, port))
            self.port = self.getsockname()[1]
        except socket.error:
            raise

        self.listen(20)

    def get_port(self):
        return self.port

    def seturl(self, url):
        self.urlmap['lasturl'] = url

    def seturllist(self, urllist):
        self.urlmap['lastlist'] = urllist
        
    def geturl(self):
        return self.urlmap['lasturl']

    def geturllist(self):
        return self.urlmap['lastlist']
    
    def handle_accept(self):

        try:
            self._lock.acquire()
            newSocket, address = self.accept()
            sec = secondary_url_server(sock=newSocket, addr=address,url_server=self)
        finally:
            self._lock.release()
        

    def handle_close(self):
        pass

    def handle_expt(self):
        pass
    
    def notify(self, handler):
        """ Notify method for secondary socket server
        to add urls. (Not Used) """

        for url in handler.urls:
            self.urls.put(url)

class secondary_url_server(asyncore.dispatcher):
    """ Secondary url server class for asynchronous url
    server. An instance of this class is created every time
    to handle a client connection """

    def __init__(self, sock, addr, url_server):
        asyncore.dispatcher.__init__(self, sock)
        self._urlserver = url_server
        self._client_address = addr

    def handle_write(self):
        pass

    def handle_expt(self):
        pass
    
    def handle_read(self):
        """ Read data from the client and
        send resposnse """

        data = self.recv(8192)

        if data:
            # Replace any newlines
            data.strip()

            if data in ('ping', 'flush', 'get last url', 'get url','get list','get last list'):
                if data.lower() == 'ping':
                    self.sendall('ping')
                elif data.lower() == "flush":
                    while True:
                        try:
                            self._urlserver.urls.get_nowait()
                        except Empty:
                            break
                    self.sendall("Flushed Repository")
                elif data.lower() == "get last url":
                    self.sendall((self._urlserver.geturl()).strip())
                elif data.lower() == "get last list":
                    self.sendall((self._urlserver.geturllist()).strip())                    
                elif data.lower() == "get url":
                    try:
                        prior, url=self._urlserver.urls.get_nowait()
                        self._urlserver.seturl(url)
                        self.sendall(url.strip())                        
                    except Empty:
                        self.sendall("empty")
                elif data.lower() == 'get list':
                    try:
                        prior, rest = self._urlserver.urls2.get_nowait()
                        self._urlserver.seturllist(rest)
                        self.sendall(rest.strip())
                    except Empty:
                        self.sendall('empty')
            else:
                # Split w.r.t '#'
                pieces = data.split('#')
                # print 'Pieces=>',pieces
                if len(pieces)==2:
                    # Sent by crawler, put to urls queue
                    self._urlserver.urls.put_nowait(pieces)
                else:
                    # Sent by fetcher, put to urls2 queue
                    self._urlserver.urls2.put_nowait((pieces[0], '#'.join(pieces[1:])))
                    
                self.sendall("Recieved")
        else:
            self.close()

    def handle_close(self):
        pass

def start():
    """ Start the asynchronous servers/clients
    by entering the asyncore loop """

    asyncore.loop()

if __name__=="__main__":
    # This method is used to create a server 
    # which serves HarvestMan Fetcher threads.
    import sys, time
    host = sys.argv[1]
    port = int(sys.argv[2])

    try:
        HarvestManUrlServer(host, port)
        t=AsyncoreThread()
        t.start()
        print 'Started...'
    except socket.error, (errno, errmsg):
        print 'Error:',errmsg
    except KeyboardInterrupt, e:
        pass




