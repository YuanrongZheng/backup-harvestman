# -- coding: latin-1
import xml.parsers.expat

class ConfigParser(object):

    def __init__(self, stream):
        self._node = ''
    self._stream = stream
       
    def close(self):
    try:
        self._stream.close()
    except Exception, e:
        print e
 
    def start_element(self, name, attrs):
       
        if attrs:
            # If the element has attributes
            # it does not have CDATA. So set
            # curr elem to null.
            self._node = ''
            
            for key, value in attrs.iteritems():
                # Form key name in xml map
                xmlkey = "".join((name, "_", key))
        else:
            # If element has no attributes, the
            # value will be in CDATA. Store the
            # element name so that we can use it
            # in cdata callback.
            self._node = name
        
    def char_data(self, data):
        # This will be called after the
        # start element is called. If the
        # element is of interest, set it's
        # option.
        # data = data.strip()
        
        if self._node and data:
            # print 'Setting option for %s %s ' % (self._node, data)
            if self._node=='link':
        print data
                self._stream.write(data)

if __name__=="__main__":
    p = xml.parsers.expat.ParserCreate()
    c = ConfigParser(open('links.txt','w'))
    
    p.StartElementHandler = c.start_element
    p.CharacterDataHandler = c.char_data

    try:
        p.Parse(open('cnet-rss.xml').read())
        c.close()
    except xml.parsers.expat.ExpatError, e:
        print e
        
