"""
Simple script for starting the manager's crawling.
This will be called as a process from dharvestman.py
"""

import Pyro.core
from Pyro.errors import PyroError, ProtocolError
import time

def bootstrap(name):
    print 'Resolving without name server (direct connection to Pyro server)...'
    
    uri = 'PYROLOC://127.0.0.1/' + name
    proxy = Pyro.core.getProxyForURI(uri)
    print 'URI=>', uri
    while True:
        try:
            print 'Okay...'
            proxy.run_projects()
            break
        except ProtocolError, e:
            print e
            time.sleep(1.0)
            
def main():
    import sys
    bootstrap(sys.argv[1])

if __name__=="__main__":
    main()
