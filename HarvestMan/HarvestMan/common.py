# -- coding: latin-1
""" Global functions for HarvestMan Program.
This file is part of the HarvestMan software.
For licensing information, see file LICENSE.TXT.

Author: Anand B Pillai (anandpillai at letterboxes dot org).

Created: Jun 10 2003

  Jun 14 2004         Anand          1.3.9 release.
  Oct 25 2004         Anand          Added two methods for
                                     testing url server.
                                     ping method checks whether
                                     server is alive & send_url
                                     method sends a url to it.
 Jan 10 2006          Anand          Converted from dos to unix format
                                     (removed Ctrl-Ms).
 Aug 17 2006          Anand          Modifications for the new logging
                                     module.

"""

import weakref
import os, sys
import socket
import binascii
import copy

from config import HarvestManStateObject
from logger import HarvestManLogger

class Registry(object):

    class __registrySingleton(object):

        __slots__ = ('ini',
                     'writeflag',
                     'USER_AGENT',
                     'userdebug',
                     'modfilename',
                     'oldnewmappings',
                     'mappings',
                     'urlmappings',
                     'config',
                     'connector',
                     'datamanager',
                     'ruleschecker',
                     'connectorfactory',
                     'cookiestore',
                     'trackerqueue',
                     'crawler',
                     'urlserver',
                     'asyncorethread',
                     'logger')

        def __init__(self):
            self.ini = 0
            self.writeflag = 1
            self.USER_AGENT = 'HarvestMan 1.5'
            self.userdebug = []
            self.modfilename = ''
            self.urlmappings = {}
            self.oldnewmappings = {}
            self.mappings = { 'HarvestManStateObject' : 'config',
                              'HarvestManNetworkConnector' : 'connector',
                              'HarvestManUrlConnectorFactory' : 'connectorfactory',
                              'harvestManDataManager' : 'datamanager',
                              'harvestManRulesChecker' : 'ruleschecker',
                              'HarvestManCrawlerQueue' : 'trackerqueue',
                              'harvestMan' : 'crawler',
                              'CookieManager' : 'cookiestore',
                              'harvestManUrlServer' : 'urlserver',
                              'AsyncoreThread'      : 'asyncorethread',
                              'HarvestManLogger'    : 'logger',
                              }
            pass
        
        def __str__(self):
            return `self`

        def get_object_key(self, obj):
            """ Return the object key for HarvestMan objects """

            clsname = obj.__class__.__name__
            return self.mappings.get(clsname, '')

        def get_class_key(self, classname):
            """ Return the object key for HarvestMan classes """

            return self.mapping.get(classname)
        
            
    instance = None

    def __new__(cls): # __new__ always a classmethod
        if not Registry.instance:
            Registry.instance = Registry.__registrySingleton()
            
        return Registry.instance

    def __getattr__(self, name):
        try:
            return getattr(self.instance, name)
        except KeyError:
            raise

    def __setattr__(self, name, value):
        setattr(self.instance, name, value)


if sys.version_info[0]==2 and sys.version_info[1]==4:
    import collections

    class MyDeque(collections.deque):

        def index(self, item):
            """ Return the index of an item from the deque """

            return list(self).index(item)
            
        def insert(self, idx, item):
            """ Insert an item to the deque at the given index """
            
            myl = len(self)

            if myl==0:
                self.append(item)
                return
            elif idx==myl:
                self.append(item)
            elif idx>myl:
                raise IndexError, 'Index out of range'

            self.append(self.__getitem__(myl-1))
            for index in reversed(range(idx,myl)):
                self.__setitem__(index+1,self.__getitem__(index))

            self.__setitem__(idx, item)

        def pop(self, idx=None):
            """ Pop an item from the deque from the given index """

            # To be compatible with list
            myl = len(self)
            if idx==None:
                idx = myl - 1
            
            item = self.__getitem__(idx)
            # delete it
            self.__delitem__(idx)
            return item

        def remove(self, item):
            """ Remove an item from the deque """
            
            idx = self.index(item)
            self.__delitem__(idx)
else:
    MyDeque = list

# Single instance of the global lookup object
RegisterObj = Registry()

def GetState():
    """ Return a snapshot of the current state of this
    object and its containing threads for serializing """
        
    d = {}
    d['urlmappings'] = RegisterObj.urlmappings
    return copy.deepcopy(d)

def GetObject(objkey):
    """ Get the registered instance of the HarvestMan program
    object using its key <objkey> by looking up the global
    registry object """

    try:
        obj = eval('RegisterObj.' + str(objkey), globals())
        if type(obj)=='instance':
            return weakref.proxy(obj)
        else:
            return obj
    except (KeyError, AttributeError), e:
        print e

    return None   

def GetUrlObject(key):
    """ Get url object based on its index (key) """

    if type(key) is int:
        obj = RegisterObj.urlmappings.get(key, None)
        return obj
    else:
        return None

def SetState(obj):

    if obj.has_key('urlmappings'):
        global RegisterObj
        RegisterObj.urlmappings = obj.get('urlmappings').copy()
        # print RegisterObj.urlmappings
        return 0
    else:
        return -1

def ResetState():
    
    global RegisterObj
    RegisterObj.urlmappings = {}
    # Reset config object
    cfg = HarvestManStateObject()
    RegisterObj.config = cfg
    # Do not reset logger yet
    
def SetObject(obj):
    """ Set the instance <value> of the HarvestMan program object in
    the global registry object """

    # global RegisterObj
    # Get the object key
    objkey = RegisterObj.get_object_key(obj)

    if objkey:
        s="".join(('RegisterObj', '.', str(objkey),'=', 'obj'))
        exec(compile(s,'','exec'))

def SetUrlObject(obj):
    """ Set url objects based on their index """

    key = obj.index
    urldict = RegisterObj.urlmappings
    if not urldict.has_key(key):
        urldict[key] = obj
    
def SetConfig(configobject):
    """ Set the config object  """

    global RegisterObj
    if RegisterObj.ini==0: Initialize()
    RegisterObj.config = configobject

def SetLogFile():

    global RegisterObj
    logfile = RegisterObj.config.logfile
    # if logfile: RegisterObj.logger.setLogFile(logfile)
    if logfile:
        RegisterObj.logger.setLogSeverity(RegisterObj.config.verbosity)
        # If simulation is turned off, add file-handle
        if not RegisterObj.config.simulate:
            RegisterObj.logger.addLogHandler('FileHandler',logfile)

def SetUserAgent(user_agent):
    """ Set the user agent """

    global RegisterObj
    RegisterObj.USER_AGENT = user_agent

def SetUserDebug(message):
    """ Used to store error messages related
    to user settings in the config file/project file.
    These will be printed at the end of the program """

    global RegisterObj
    if message:
        try:
            RegisterObj.userdebug.index(message)
        except:
            RegisterObj.userdebug.append(message)

def Initialize():
    """ Initialize the globals module. This
    initializes the registry object and a basic
    config object in the regsitry. """

    global RegisterObj
    if RegisterObj.ini==1:
        return -1

    RegisterObj.ini = 1
    cfg = HarvestManStateObject()
    RegisterObj.config = cfg
    RegisterObj.logger = HarvestManLogger()
    
def Finish():
    """ Clean up this module. This function
    can be called at program exit or when
    handling signals to clean up """

    global RegisterObj
    cfg=RegisterObj.config
    # Stop url server if it is running
    if cfg.urlserver:
        info('Stoppping url server at port %d...' % cfg.urlport)
        async_t= RegisterObj.asyncorethread
        if async_t:
            try:
                async_t.end()
                extrainfo("Done.")
            except socket.error, e:
                print e
            except Exception, e:
                print e
                
    
    RegisterObj.ini = 0

    # RegisterObj.logger.close()
    RegisterObj.logger.shutdown()
    
    # Reset url object indices
    RegisterObj.urlmappings.clear()

    # If this was started from a runfile,
    # remove it.
    if cfg.runfile:
        try:
            os.remove(cfg.runfile)
        except OSError, e:
            moreinfo('Error removing runfile %s.' % cfg.runfile)
            
    # inform user of config file errors
    if RegisterObj.userdebug:
        print "Some errors were found in your configuration, please correct them!"
        for x in range(len(RegisterObj.userdebug)):
            print str(x+1),':', RegisterObj.userdebug[x]

    RegisterObj.userdebug = []

def wasOrWere(val):
    """ What it says """

    if val > 1: return 'were'
    else: return 'was'

def plural((s, val)):
    """ What it says """

    if val>1:
        if s[len(s)-1] == 'y':
            return s[:len(s)-1]+'ies'
        else: return s + 's'
    else:
        return s

# file type identification functions
# this is the precursor of a more generic file identificator
# based on the '/etc/magic' file on unices.

signatures = { "gif" : [0, ("GIF87a", "GIF89a")],
               "jpeg" :[6, ("JFIF",)],
               "bmp" : [0, ("BM6",)]
             }
aliases = { "gif" : (),                       # common extension aliases
            "jpeg" : ("jpg", "jpe", "jfif"),
            "bmp" : ("dib",) }

def bin_crypt(data):
    """ Encryption using binascii and obfuscation """

    if data=='':
        return ''

    try:
        return binascii.hexlify(obfuscate(data))
    except TypeError, e:
        debug('Error in encrypting data: <',data,'>', e)
        return data
    except ValueError, e:
        debug('Error in encrypting data: <',data,'>', e)
        return data

def bin_decrypt(data):
    """ Decrypttion using binascii and deobfuscation """

    if data=='':
        return ''

    try:
        return unobfuscate(binascii.unhexlify(data))
    except TypeError, e:
        print 'Error in decrypting data: <',data,'>', e
        return data
    except ValueError, e:
        print'Error in decrypting data: <',data,'>', e
        return data


def obfuscate(data):
    """ Obfuscate a string using repeated xor """

    out = ""
    import operator

    e0=chr(operator.xor(ord(data[0]), ord(data[1])))
    out = "".join((out, e0))

    x=1
    eprev=e0
    for x in range(1, len(data)):
        ax=ord(data[x])
        ex=chr(operator.xor(ax, ord(eprev)))
        out = "".join((out,ex))
        eprev = ex

    return out

def unobfuscate(data):
    """ Unobfuscate a xor obfuscated string """

    out = ""
    x=len(data) - 1

    import operator

    while x>1:
        apos=data[x]
        aprevpos=data[x-1]
        epos=chr(operator.xor(ord(apos), ord(aprevpos)))
        out = "".join((out, epos))
        x -= 1

    out=str(reduce(lambda x, y: y + x, out))
    e2, a2 = data[1], data[0]
    a1=chr(operator.xor(ord(a2), ord(e2)))
    a1 = "".join((a1, out))
    out = a1
    e1,a1=out[0], data[0]
    a0=chr(operator.xor(ord(a1), ord(e1)))
    a0 = "".join((a0, out))
    out = a0

    return out


def filetype(filename):
    """ Return filetype of a file by reading its
    signature """

    fullpath=os.path.abspath(filename)
    if not os.path.exists(fullpath):
        return ''

    try:
        f=open(fullpath, 'rb')
    except IOError, e:
        print e
        return ''
    except OSError, e:
        print e
        return ''

    sigbuffer = ''
    try:
        sigbuffer=f.read(20)
    except IOError, e:
        print e
        return ''

    ftype=''
    for key in signatures.keys():
        sigs = (signatures[key])[1]
        # look for the sigs in the sigbuffer
        for sig in sigs:
            index = sigbuffer.find(sig)
            if index == -1: continue
            if index == (signatures[key])[0]:
                ftype = key
                break

    return ftype

def rename(filename):
    """ Rename a file by looking at its signature """

    ftype=filetype(filename)

    if ftype:
        fullpath = os.path.abspath(filename)
        # get extension
        extn = (((os.path.splitext(fullpath))[1])[1:]).lower()
        if extn==ftype: return ''
        try:
            a=aliases[ftype]
            if extn in a: return ''
        except KeyError:
            return ''

        # rename the file
        newname = (os.path.splitext(fullpath))[0] + '.' + ftype
        try:
            os.rename(fullpath, newname)
            # set the global variable to new name
            global RegisterObj
            # build up a dictionary of oldfilename => newfilename
            # mappings, this will be useful later
            RegisterObj.oldnewmappings[fullpath]=newname
            RegisterObj.modfilename = newname
            # return the new name
            return newname
        except OSError, e:
            print e
            return ''
    return ''

def send_url(data, host, port):
    
    cfg = RegisterObj.config
    if cfg.urlserver_protocol == 'tcp':
        return send_url_tcp(data, host, port)
    elif cfg.urlserver_protocol == 'udp':
        return send_url_udp(data, host, port)
    
def send_url_tcp(data, host, port):
    """ Send url to url server """

    # Return's server response if connection
    # succeeded and null string if failed.
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host,port))
        sock.sendall(data)
        response = sock.recv(8192)
        sock.close()
        return response
    except socket.error:
        pass

    return ''

def send_url_udp(data, host, port):
    """ Send url to url server """

    # Return's server response if connection
    # succeeded and null string if failed.
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(data,0,(host, port))
        response, addr = sock.recvfrom(8192, 0)
        sock.close()
        return response
    except socket.error:
        pass

    return ''

def ping_urlserver(host, port):
    
    cfg = RegisterObj.config
    
    if cfg.urlserver_protocol == 'tcp':
        return ping_urlserver_tcp(host, port)
    elif cfg.urlserver_protocol == 'udp':
        return ping_urlserver_udp(host, port)
        
def ping_urlserver_tcp(host, port):
    """ Ping url server to see if it is alive """

    # Returns server's response if server is
    # alive & null string if server is not alive.
    try:
        debug('Pinging server at (%s:%d)' % (host, port))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host,port))
        # Send a small packet
        sock.sendall("ping")
        response = sock.recv(8192)
        if response:
            debug('Url server is alive')
        sock.close()
        return response
    except socket.error:
        debug('Could not connect to (%s:%d)' % (host, port))
        return ''

def ping_urlserver_udp(host, port):
    """ Ping url server to see if it is alive """

    # Returns server's response if server is
    # alive & null string if server is not alive.
    try:
        debug('Pinging server at (%s:%d)' % (host, port))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Send a small packet
        sock.sendto("ping", 0, (host,port))
        response, addr = sock.recvfrom(8192,0)
        if response:
            debug('Url server is alive')
        sock.close()
        return response
    except socket.error:
        debug('Could not connect to (%s:%d)' % (host, port))
        return ''    
        
# Modified to use the logger object
def info(arg, *args):
    """ Print basic information, will print if verbosity is >=1 """

    # Setting verbosity to 1 will print the basic
    # messages like project info and final download stats.
    RegisterObj.logger.info(arg, *args)

def moreinfo(arg, *args):
    """ Print more information, will print if verbosity is >=2 """

    # Setting verbosity to 2 will print the basic info
    # as well as detailed information regarding each downloaded link.
    RegisterObj.logger.moreinfo(arg, *args)    

def extrainfo(arg, *args):
    """ Print extra information, will print if verbosity is >=3 """

    # Setting verbosity to 3 will print more information on each link
    # as well as information of each thread downloading the link, as
    # well as some more extra information.
    RegisterObj.logger.extrainfo(arg, *args)    

def debug(arg, *args):
    """ Print debug information, will print if verbosity is >=4 """

    # Setting verbosity to 4 will print maximum information
    # plus extra debugging information.
    RegisterObj.logger.debug(arg, *args)    

def moredebug(arg, *args):
    """ Print more debug information, will print if verbosity is >=5 """

    # Setting verbosity to 5 will print maximum information
    # plus maximum debugging information.
    RegisterObj.logger.moredebug(arg, *args)        

if __name__=="__main__":
    Initialize()
    cfg = GetObject('config')
    print type(cfg)
    
