import Pyro.core, Pyro.naming
import time

class DomainState:
    """ This class holds the state of a domain
    that is either being crawled or is finished.
    This class could be inserted in some kind of
    hash-array as the value, with key being
    the domain name being crawled.
    """
    
    def __init__(self, urladdress):
        self.domain = urladdress
    
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

class Manager(Pyro.core.ObjBase):
    """ This class implements the D-Harvestman
    Manager functionality """
    
    domains = {}
    new_domains = []
    
    def __init__(self):
        Pyro.core.ObjBase.__init__(self)
        
        # insert some dummy data
        self.new_domains.append("http://www.google.com")
        self.new_domains.append("http://www.yahoo.com")
        self.new_domains.append("http://www.altavista.com")
        
    def get_current_time(self):
        return time.time()
    
    def start_service(self):
        Pyro.core.initServer()
        daemon = Pyro.core.Daemon()
        uri = daemon.connect(Manager(), "manager")
        print "The daemon runs on port: ", daemon.port
        print "The object's uri is: ", uri
        daemon.requestLoop()
        
    def test(self):
        return "hello from manager"
        
    def fetch_url(self):
        # find a domain to crawl
        try:
            domainaddr = self.new_domains.pop()
            if not domainaddr:
                return None
        except:
            return None
        
        # register domain status
        new_domain = DomainState(domainaddr)
        new_domain.state = DomainState.URL_CRAWLING
        new_domain.start_time = self.get_current_time()
        new_domain.heartbeat = self.get_current_time()
        # todo
        #new_domain.crawler = get_remote_address()
        
        # add to global hash array
        self.domains[new_domain.domain] = new_domain
        
        # return domain to slave
        return new_domain.domain
    
    def heartbeat(self, domain):
        # update heardbeat timestamp for this domain
        if self.domains.has_key(domain):
            print "updating heartbeat for domain " + domain
            domain_state = self.domains[domain]
            domain_state.heartbeat = self.get_current_time()
        
    def crawl_failed(self, domain):
        # update state for this domain
        if self.domains.has_key(domain):
            print "crawl failed for domain " + domain
            domain_state = self.domains[domain]
            domain_state.state = DomainState.URL_FAILED
        
    def crawl_finished(self, domain):
        # update state for this domain
        if self.domains.has_key(domain):
            print "crawl finished for domain " + domain
            domain_state = self.domains[domain]
            domain_state.state = DomainState.URL_FINISHED
        
    def url_found(self, new_url):
        # register new url in queue
        print "adding new domain: " + new_url
        self.new_domains.append(new_url)
        pass
    
# this is where the fun starts
if __name__=='__main__':
    manager = Manager()
    manager.start_service()
    
    