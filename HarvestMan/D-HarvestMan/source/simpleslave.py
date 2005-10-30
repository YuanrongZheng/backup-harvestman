import Pyro.core

class SimpleSlave:
    manager = None
    manager_uri = "PYROLOC://localhost:7766/manager"
    
    def __init__(self):
        self.manager = Pyro.core.getProxyForURI(self.manager_uri)
        
    def test(self):
        return self.manager.fetch_url()

if __name__=='__main__':
    print "Starting SimpleSlave..."
    slave = SimpleSlave()
    print slave.test()
    