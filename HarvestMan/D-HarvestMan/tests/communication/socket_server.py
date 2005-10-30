#!/usr/bin/env python

# note! if running on linux, change all with 'threading' with 'forking'

import socket
import SocketServer


class ManagerInterface:
    def test(self, domain):
        print "inside test function. received: %s" %domain
        return "ok"


class ThreadingServer(SocketServer.ThreadingTCPServer):
    pass

class SimpleRequestHandler(SocketServer.StreamRequestHandler):

    def handle(self):
        req = self.rfile.readline()
        print 'received: ' + req
        self.wfile.write('ok')
        
def test():
    portnum = 7766
    server = ThreadingServer(('', portnum), SimpleRequestHandler)
    print "starting socket server on port " + str(portnum)
    server.serve_forever()

if __name__ == '__main__':
    test()