import Pyro.core,threading,time
import timeit

class SimpleSlave:
    manager = None
    manager_uri = "PYROLOC://193.217.3.94:7766/manager"
    
    def __init__(self):
       self.mproxy = Pyro.core.getProxyForURI(self.manager_uri)
       #pass

def threadCode():
    slave = SimpleSlave() 
    for i in range(1,61):        
        domain = slave.mproxy.fetch_url()
        #print "fetched domain: " + domain
        url = "http://www.hia.no/" +str(i)+threading.currentThread().getName()
        t = timeit.Timer("test("+str(url)+")", "")
        res = t.repeat(1,1)
        print res
        
        slave.mproxy.url_found()
        #slave.mproxy.url_found("http://www.ffi.no"
        time.sleep(0.5)
        slave.mproxy.url_found("http://www.hia.no/" +str(i)+threading.currentThread().getName())
        
        #slave.mproxy.heartbeat(domain)
        #slave.mproxy.crawl_failed(domain)
    
    slave.mproxy.crawl_finished(domain)    

if __name__== '__main__':
    print "Starting SimpleSlave..."
    slave = SimpleSlave()
    for i in range(0,100):
        t = threading.Thread(target = threadCode, name = "child" + str(i))
        t.start()


    
    