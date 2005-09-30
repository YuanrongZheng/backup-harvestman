
import time
# howto implement static explained in DiveIntiPython p. 61
class url_queue:

    queue = {}

    def __init__(self):
        pass

    def insert(self,url):
        self.__class__.queue[url] = "testValue"
        print "url_queue: " + self.__class__.queue[url]
        
    def remove(self):
        pass
        
    def is_defined(self,key):
        pass
        
    