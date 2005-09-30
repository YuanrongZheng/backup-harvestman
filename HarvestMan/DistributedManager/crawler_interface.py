import Pyro.core
import Pyro.naming
import url_queue

class crawler_interface(Pyro.core.ObjBase):
    def __init__(self):
        Pyro.core.ObjBase.__init__(self)
    
    
    def hello(self,name):
        print "Hello, "+name
     
    def get_domain(self):
        pass
        
    def finished_domain(self,domain):
        pass
        
    def i_am_alive(self,domain):
        pass
        
    def crawl_failed(self,domain):
        pass
        
    def new_domain(self,domain):
        queue = url_queue.url_queue()
        queue.insert("andaas.net")
        
            
        

