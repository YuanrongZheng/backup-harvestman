import xml.parsers.expat

class ConfigParser(object):

    def __init__(self, config):
        self.cfg = config
        self._node = ''
        
    def start_element(self, name, attrs):
        
        if attrs:
            # If the element has attributes
            # it does not have CDATA. So set
            # curr elem to null.
            self._node = ''
            
            for key, value in attrs.items():
                # Form key name in xml map
                xmlkey = "".join((name, "_", key))
                # Set value
                if self.cfg:
                    self.cfg.set_option_xml(xmlkey, value)
                else:
                   print key, value
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
        data = data.strip()
        
        if self._node and data:
            # print 'Setting option for %s %s ' % (self._node, data)
            if self.cfg:
                self.cfg.set_option_xml(self._node, data)
            else:
                print data
                
            pass

def parse_xml_config_file(configobj, configfile):
    """ Parse xml config file """

    # Create config parser
    c = ConfigParser(configobj)
    p = xml.parsers.expat.ParserCreate()

    p.StartElementHandler = c.start_element
    p.CharacterDataHandler = c.char_data

    try:
        p.Parse(open(configfile).read())
        return 1
    except (IOError, OSError, xml.parsers.expat.ExpatError), e:
        print e
        return 0
    
if __name__=="__main__":
    p = xml.parsers.expat.ParserCreate()
    c = ConfigParser(None)
    
    p.StartElementHandler = c.start_element
    p.CharacterDataHandler = c.char_data

    try:
        p.Parse(open('config.xml').read())
    except xml.parsers.expat.ExpatError, e:
        print e
        
