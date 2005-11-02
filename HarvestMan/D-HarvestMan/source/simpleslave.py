import Pyro.core,threading,time
import timeit

class SimpleSlave:
    manager = None
    manager_uri = "PYROLOC://localhost:7766/manager"
    
    def __init__(self):
       self.mproxy = Pyro.core.getProxyForURI(self.manager_uri)
       #pass
        
    def threadCode(self):
        slave = SimpleSlave() 
        for i in range(1,2):        
            domain = slave.mproxy.fetch_url()
            #print "fetched domain: " + domain
            url = "http://www.hia.no/" +str()+threading.currentThread().getName()
            t = timeit.Timer("slave.mproxy.url_found('"+str(url)+"')", "from threadCode import slave")
            res = t.repeat(1,1)
            print res
            
            slave.mproxy.url_found()
            #slave.mproxy.url_found("http://www.ffi.no"
            time.sleep(0.5)
            slave.mproxy.url_found("http://www.hia.no/" +str(i)+threading.currentThread().getName())
            
            #slave.mproxy.heartbeat(domain)
            #slave.mproxy.crawl_failed(domain)
        
        slave.mproxy.crawl_finished(domain)    

def test():
    #slave = SimpleSlave()
    #for i in range(1,2):
    slave.mproxy.url_found("http://www.hia.no/" +str(1)+threading.currentThread().getName())
        #time.sleep(0.5)
        #slave.mproxy.url_found("http://www.hia.no/" +str(i)+threading.currentThread().getName())
        #time.sleep(0.5)

if __name__== '__main__':
    print "Starting SimpleSlave..."
    
    for i in range(0,100):
        slave = SimpleSlave()
        t = threading.Thread(target = slave.threadCode(), name = "child" + str(i))
        t.start()

    #t = timeit.Timer("test()", "from __main__ import test")
    #res = t.repeat(100, 1)
    #for i in res:
    #    print i

    
    