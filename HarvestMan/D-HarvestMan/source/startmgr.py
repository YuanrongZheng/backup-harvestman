"""
Simple script for starting the manager's crawling.
This will be called as a process from dharvestman.py
"""

import Pyro.core
from Pyro.errors import PyroError, ProtocolError
import time
import sys

def bootstrap(name):
    print 'Resolving without name server (direct connection to Pyro server)...'
    
    uri = 'PYROLOC://192.168.4.71/' + name
    proxy = Pyro.core.getProxyForURI(uri)
    print 'URI=>', uri
    while True:
        try:
            print 'Okay...'
            print 'PROXY=>',proxy
            proxy.run_projects()
            break
        except ProtocolError, e:
            time.sleep(1.0)
        except KeyboardInterrupt, e:
            sys.exit(1)
            
def main():
    bootstrap(sys.argv[1])

if __name__=="__main__":
    main()
