# -- coding: iso8859-1
""" test_client - Client classes to test the url server.
This module consists of a simple client & an asynchronous
url client based on asyncore.

(This module is not used in HarvestMan program right now.)

Author : Anand B Pillai ( anandpillai at letterboxes dot org).
Date: 25/10/2004.
"""

import socket, asyncore, threading

class test_client:

    def __init__(self, port):
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
    def connect(self):
        self.sock.connect(('localhost', self.port))
        print "Connected to server at port",self.port

    def send(self):

        datal = [ "flush",
                  "This is client connecting",
                  "This is first piece of data",
                  "This is second piece of data",
                  "This is third piece of data"]

        for s in datal:
            self.sock.sendall(s + "\n")
            print "Sent: ",s
            response = self.sock.recv(8192)
            print "Recieved:",response

        self.sock.close()

class async_url_client(asyncore.dispatcher_with_send):
    """ Asynchronous url client """
    
    def __init__(self, host, port, data):
        self.port = port
        self.host = host
        self.data = data
        self.flag = False
        self.evt = threading.Event()
        self.evt.clear()
        asyncore.dispatcher_with_send.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((self.host, self.port))
        
    def send_data(self, data):
        self.data = data
        print 'Sending data',data
        self.send(self.data)

    def connect_to_server(self):
        self.connect((self.host, self.port))        
        pass

    def handle_connect(self):
        pass
    
    def handle_expt(self):
        print 'Connection failed'
        self.close()
        
    def handle_read(self):

        data = self.recv(8192)
        print "Recieved:", data
        
    def handle_close(self):
        self.flag=True
        self.evt.set()
        self.close()
    
if __name__=="__main__":
    data_list = ["Python",
                 "Perl",
                 "Ruby",
                 "Pascal",
                 "C",
                 "C++"]

    client = test_client(port=8882)
    client.connect()
    client.send()
    #asyncore.loop()
    
    #for d in data_list:
    #    client.send_data(d)
        

