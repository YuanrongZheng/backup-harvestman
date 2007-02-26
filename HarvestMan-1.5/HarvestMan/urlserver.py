# -- coding: latin-1
""" urlserver.py - Asynchronous and Synchronous socket servers
    serving urls for HarvestMan. This module is part of the
    HarvestMan program.

    Author : Anand B Pillai (abpillai at gmail dot com).


    Jan 10 2006  Anand  Converted from dos to unix format (removed Ctrl-Ms).

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

    def end(self):
        self.flag=False
        self.map=None

class HarvestManSimpleUrlServer(object):
    """ A simple url server based upon SocketServer's
    threading TCP server """

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server = SocketServer.ThreadingTCPServer((self.host, self.port), 
                                          harvestManUrlHandler)
        self.server.serve_forever()

class harvestManUrlHandler(SocketServer.BaseRequestHandler):
    """ The Request handler class for harvestManSimpleUrlServer """

    urls = []

    def __init__(self, req, caddr, server):
        SocketServer.BaseRequestHandler.__init__(self, req, caddr, server)

    def handle(self):

        while True:
            data = self.request.recv(8192)
            if not data:break

            if data.lower() == "get url":
                if len(self.urls)==0:
                    self.request.sendall('empty')
                else:
                    url = self.urls.pop()
                    self.request.sendall(url.strip())
            else:
                self.urls.append(data)
                self.request.sendall("Recieved")
        self.request.close()

class HarvestManUrlServer(asyncore.dispatcher_with_send):
    """ An asynchronous url server class for HarvestMan.
    This class can replace the url queue and work as a url
    server multiplexing several url requests simultaneously """

    def __init__(self, host, port, protocol='tcp'):
        self.urls = PriorityQueue(0)
        self.port = port
        self.host = host
        self.protocol = protocol
        self.urlmap = {}
        asyncore.dispatcher_with_send.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.bind((self.host, port))
        except socket.error:
            raise

        self.listen(5)

    def get_port(self):
        return self.port

    def seturl(self, url):
        self.urlmap['last'] = url

    def geturl(self):
        return self.urlmap['last']

    def handle_accept(self):
        newSocket, address = self.accept()
        secondary_url_server(sock=newSocket, addr=address,
                             url_server=self)

    def handle_close(self):
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
    
    def handle_read(self):
        """ Read data from the client and
        send resposnse """

        data = self.recv(8192)

        if data:
            # Replace any newlines
            data.strip()
            urls = self._urlserver.urls
            if data in ('ping', 'flush', 'get last url', 'get url'):
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
                elif data.lower() == "get url":
                    try:
                        url=urls.get_nowait()
                        self._urlserver.seturl(url)
                        self.sendall(url.strip())                        
                    except Empty:
                        self.sendall("empty")
            else:
                urls.put_nowait(data)
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




