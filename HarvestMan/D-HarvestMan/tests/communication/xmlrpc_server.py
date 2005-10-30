#!/usr/bin/env python

# note! if running on linux, change all with 'threading' with 'forking'

from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from SocketServer import ThreadingMixIn


class ManagerInterface:
    def test(self, domain):
        print "inside test function. received: %s" %domain
        return "ok"

class ThreadingServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass

serveraddr = ('', 1234)
server = ThreadingServer(serveraddr, SimpleXMLRPCRequestHandler)
server.register_instance(ManagerInterface())
server.register_introspection_functions()
print "starting server"
server.serve_forever()
