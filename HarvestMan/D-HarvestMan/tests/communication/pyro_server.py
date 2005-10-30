import Pyro.core
import Pyro.naming

class ManagerInterface(Pyro.core.ObjBase):
    def __init__(self):
        Pyro.core.ObjBase.__init__(self)
    
    def test(self, domain):
        print "inside test function. received: %s" %domain
        return "ok"

Pyro.core.initServer()
daemon=Pyro.core.Daemon()
uri=daemon.connect(ManagerInterface(),"ManagerInterface")

print "The daemon runs on port:",daemon.port
print "The object's uri is:",uri

daemon.requestLoop()