import xmlrpclib, code
import timeit

serveraddr = "http://localhost:1234/"
s = xmlrpclib.ServerProxy(serveraddr)

def rpc_test():
    s.test('http://localhost')

if __name__=='__main__':
    t = timeit.Timer("rpc_test()", "from __main__ import rpc_test")
    res = t.repeat(10, 100)
    for i in res:
        print i
