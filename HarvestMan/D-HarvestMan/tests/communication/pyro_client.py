import Pyro.core
import timeit

# you have to change the URI below to match your own host/port.
manager = Pyro.core.getProxyForURI("PYROLOC://193.217.3.94:7766/ManagerInterface")

def rpc_test():
    manager.test("http://localhost:7766/")

if __name__=='__main__':
    t = timeit.Timer("rpc_test()", "from __main__ import rpc_test")
    res = t.repeat(10, 1)
    for i in res:
        print i
