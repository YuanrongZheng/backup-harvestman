import Pyro.core, Pyro.naming

class Manager(Pyro.core.ObjBase):
    
    
    def __init__(self):
        Pyro.core.ObjBase.__init__(self)
    
    def start_service(self):
        Pyro.core.initServer()
        daemon = Pyro.core.Daemon()
        uri = daemon.connect(Manager(), "manager")
        print "The daemon runs on port:", daemon.port
        print "The object's uri is:", uri
        daemon.requestLoop()
        
    def test(self):
        return "hello from manager"
        
    def fetch_url(self):
        # find a domain to crawl
        
        # register domain status
        
        # return domain to slave
        
        pass
    
    def heartbeat(self):
        pass
        
    def crawl_failed(self):
        pass
        
    def crawl_finished(self):
        pass
        
    def url_found(self):
        pass
    
if __name__=='__main__':
    manager = Manager()
    manager.start_service()
    
    