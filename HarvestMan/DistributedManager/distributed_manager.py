import Pyro.core
import Pyro.naming
import crawler_interface

Pyro.core.initServer()
daemon=Pyro.core.Daemon()
uri=daemon.connect(crawler_interface.crawler_interface(),"crawler_interface")

print "The daemon runs on port:",daemon.port
print "The object's uri is:",uri

daemon.requestLoop()