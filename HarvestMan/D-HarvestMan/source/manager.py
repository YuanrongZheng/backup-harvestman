import Pyro.core, Pyro.naming

class DomainState:
    # name or address of domain
    domain = None
    
    # possible states for a domain
    URL_FINISHED = 1
    URL_CRAWLING = 2
    URL_NEW = 3
    URL_EXCLUDED = 4
    URL_FAILED = 5
    
    # variable holding the state
    state = URL_NEW
    
    # address of node crawling this domain
    crawler = None
    
    # start time of crawling
    start_time = None
    
    # end time of crawling
    end_time = None
    
    # timestamp of last heardbeat
    heartbeat = None
    
    def __init__(self, urladdress):
        self.domain = urladdress
    

class Manager(Pyro.core.ObjBase):
    domains = {}
    new_domains = []
    
    def __init__(self):
        Pyro.core.ObjBase.__init__(self)
        
        # insert some dummy data
        self.new_domains.append("http://www.google.com")
        self.new_domains.append("http://www.yahoo.com")
        self.new_domains.append("http://www.altavista.com")
        
    def get_current_time(self):
        pass
    
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
        domainaddr = self.new_domains.pop()
        if not domainaddr:
            return None
        
        # register domain status
        new_domain = DomainState(domainaddr)
        new_domain.state = DomainState.URL_CRAWLING
        new_domain.start_time = self.get_current_time()
        new_domain.heartbeat = self.get_current_time()
        # todo
        #new_domain.crawler = get_remote_address()        
        
        # return domain to slave
        return new_domain.domain
    
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
    
    