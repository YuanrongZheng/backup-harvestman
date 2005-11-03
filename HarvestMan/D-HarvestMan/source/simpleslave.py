import Pyro.core
import threading
import time
import timeit
import random

def setup():
    global mproxy

class SimpleSlave(threading.Thread):
    manager = None
    manager_uri = "PYROLOC://localhost:7766/manager"

    def run(self):
        mproxy = Pyro.core.getProxyForURI(self.manager_uri)
        domain = mproxy.fetch_url()
        print "starting crawling domain: " + domain
        while(1):                    
            url = "http://www.hia.no/" +str(random.randint(1,9999999))+threading.currentThread().getName()
            mproxy.url_found(url)
            time.sleep(0.5)            
        
        mproxy.crawl_finished(domain)    


# this is where the fun starts
if __name__== '__main__':
    print "Starting SimpleSlave..."
    
    # start multiple slave-emulator threads
    for i in range(0,10):
        SimpleSlave().start()        

    #t = timeit.Timer("test()", "from __main__ import test")
    #res = t.repeat(100, 1)
    #for i in res:
    #    print i

    
    