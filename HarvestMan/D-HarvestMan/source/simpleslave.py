import Pyro.core,threading,time

class SimpleSlave:
    manager = None
    manager_uri = "PYROLOC://localhost:7766/manager"
    
    def __init__(self):
       self.mproxy = Pyro.core.getProxyForURI(self.manager_uri)
       #pass

def threadCode():         
    for i in range(1,10):
        slave = SimpleSlave()
        domain = slave.mproxy.fetch_url()
        #print "fetched domain: " + domain
        slave.mproxy.url_found("http://www.hia.no/" +str(i)+threading.currentThread().getName())
        #slave.mproxy.url_found("http://www.ffi.no"
        slave.mproxy.heartbeat(domain)
        time.sleep(1)
        slave.mproxy.crawl_finished(domain)
        slave.mproxy.crawl_failed(domain)

if __name__=='__main__':
    print "Starting SimpleSlave..."
    slave = SimpleSlave()
    for i in range(0,5):
        t = threading.Thread(target = threadCode, name = "child"+str(i))
        t.start()


    
    