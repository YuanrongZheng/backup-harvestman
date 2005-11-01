import Pyro.core

class SimpleSlave:
    manager = None
    manager_uri = "PYROLOC://localhost:7766/manager"
    
    def __init__(self):
        self.mproxy = Pyro.core.getProxyForURI(self.manager_uri)

if __name__=='__main__':
    print "Starting SimpleSlave..."
    slave = SimpleSlave()
    domain = slave.mproxy.fetch_url()
    print "fetched domain: " + domain
    slave.mproxy.url_found("http://www.hia.no")
    slave.mproxy.url_found("http://www.ffi.no")
    slave.mproxy.heartbeat(domain)
    slave.mproxy.crawl_finished(domain)
    slave.mproxy.crawl_failed(domain)
    
    