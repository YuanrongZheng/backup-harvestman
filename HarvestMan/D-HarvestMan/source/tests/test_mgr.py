"""
Simple script for starting the manager's crawling.
This will be called as a process from dharvestman.py
"""

import Pyro.core
from Pyro.errors import PyroError, ProtocolError
import time

def test():
    print 'Resolving without name server (direct connection to Pyro server)...'
    
    uri = 'PYROLOC://127.0.0.1/DHarvestMan'
    proxy = Pyro.core.getProxyForURI(uri)
    print 'URI=>', uri
    proxy.set_flag()

if __name__=="__main__":
    test()
