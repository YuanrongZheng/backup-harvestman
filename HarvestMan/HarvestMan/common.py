# -- coding: iso8859-1
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

"""

import weakref
import os, sys
import binascii
import socket

__all__ = [ "varprint", "info", "moreinfo", "extrainfo", "debug", "moredebug",
           "wasOrWere", "plural", "filetype", "rename", "obfuscate", "unobfuscate",
            "bin_crypt", "bin_decrypt", "Initialize", "Finish", "SetUserAgent",
            "GetObject", "GetRegistryObject", "send_url", "ping_urlserver",
            "SetObject", "SetUserDebug", "GetUrlObject", "SetUrlObject", "SetLogFile",
            "HARVESTMAN_SIG", "HARVESTMAN_PROJECTINFO",
            "HARVESTMAN_BOAST", "HARVESTMAN_KEYWORDS", "HARVESTMAN_CREDITS", "HARVESTMAN_BROWSER_CSS",
            "HARVESTMAN_BROWSER_TABLE1", "HARVESTMAN_BROWSER_HEADER", "HARVESTMAN_BROWSER_TABLE2",
            "HARVESTMAN_BROWSER_TABLE3", "HARVESTMAN_CACHE_README"]

#============================== Start Browser page macro strings ================================================ #
HARVESTMAN_SIG="Daddy Long Legs"

HARVESTMAN_PROJECTINFO="""\
<TR align=center>
    <TD>
    %(PROJECTNAME)s
    </TD>
    <TD>&middot;
    <!-- PROJECTPAGE --><A HREF=\"%(PROJECTSTARTPAGE)s\"><!-- END -->
    <!-- PROJECTURL -->%(PROJECTURL)s<!-- END -->
        </A>
    </TD>
</TR>"""

HARVESTMAN_BOAST="""HarvestMan is an easy-to-use website copying utility. It allows you to download a website in the World Wide Web from the Internet to a local directory. It retrieves html, images, and other files from the remote server to your computer. It builds the local directory structures recursively, and rebuilds links relatively so that you can browse the local site without again connecting to the internet. The robot allows you to customize it in a variety of ways, filtering files based on file extensions/websites/keywords. The robot is customizable by using a configuration file. The program is completely written in Python."""

HARVESTMAN_KEYWORDS="""HarvestMan, HARVESTMAN, HARVESTMan, offline browser, robot, web-spider, website mirror utility, aspirateur web, surf offline, web capture, www mirror utility, browse offline, local  site builder, website mirroring, aspirateur www, internet grabber, capture de site web, internet tool, hors connexion, windows, windows 95, windows 98, windows nt, windows 2000, python apps, python tools, python spider"""

HARVESTMAN_CREDITS="""\
&copy; 2004-2005, Anand B Pillai. """


HARVESTMAN_BROWSER_CSS="""\
body {
    margin: 0;
    padding: 1;
    margin-bottom: 15px;
    margin-top: 15px;
    background: #678;
}
body, td {
    font: 14px Arial, Times, sans-serif;
    }

#subTitle {
    background: #345;  color: #fff;  padding: 4px;  font-weight: bold;
    }

#siteNavigation a, #siteNavigation .current {
    font-weight: bold;  color: #448;
    }
#siteNavigation a:link    { text-decoration: none; }
#siteNavigation a:visited { text-decoration: none; }

#siteNavigation .current { background-color: #ccd; }

#siteNavigation a:hover   { text-decoration: none;  background-color: #fff;  color: #000; }
#siteNavigation a:active  { text-decoration: none;  background-color: #ccc; }


a:link    { text-decoration: underline;  color: #00f; }
a:visited { text-decoration: underline;  color: #000; }
a:hover   { text-decoration: underline;  color: #c00; }
a:active  { text-decoration: underline; }

#pageContent {
    clear: both;
    border-bottom: 6px solid #000;
    padding: 10px;  padding-top: 20px;
    line-height: 1.65em;
    background-image: url(backblue.gif);
    background-repeat: no-repeat;
    background-position: top right;
    }

#pageContent, #siteNavigation {
    background-color: #ccd;
    }


.imgLeft  { float: left;   margin-right: 10px;  margin-bottom: 10px; }
.imgRight { float: right;  margin-left: 10px;   margin-bottom: 10px; }

hr { height: 1px;  color: #000;  background-color: #000;  margin-bottom: 15px; }

h1 { margin: 0;  font: 14px \"Monotype Corsiva\", Times, Arial;
font-weight: bold;  font-size: 2em; }
h2 { margin: 0;  font-weight: bold;  font-size: 1.6em; }
h3 { margin: 0;  font-weight: bold;  font-size: 1.3em; }
h4 { margin: 0;  font-weight: bold;  font-size: 1.18em; }

.blak { background-color: #000; }
.hide { display: none; }
.tableWidth { min-width: 400px; }

.tblRegular       { border-collapse: collapse; }
.tblRegular td    { padding: 6px;  background-image: url(fade.gif);  border: 2px solid #99c; }
.tblHeaderColor, .tblHeaderColor td { background: #99c; }
.tblNoBorder td   { border: 0; }"""

HARVESTMAN_BROWSER_TABLE1="""\
<table width=\"76%\" border=\"0\" align=\"center\" cellspacing=\"0\" cellpadding=\"3\" class=\"tableWidth\">
    <tr>
    <td id=\"subTitle\">HARVESTMan Internet Spider - Website Copier</td>
    </tr>
</table>"""

HARVESTMAN_BROWSER_HEADER="Index of Downloaded Sites:"

HARVESTMAN_BROWSER_TABLE2= """\
<table width=\"76%(PER)s\" border=\"0\" align=\"center\" cellspacing=\"0\" cellpadding=\"0\" class=\"tableWidth\">
<tr class=\"blak\">
<td>
    <table width=\"100%(PER)s\" border=\"0\" align=\"center\" cellspacing=\"1\" cellpadding=\"0\">
    <tr>
    <td colspan=\"6\">
        <table width=\"100%(PER)s\" border=\"0\" align=\"center\" cellspacing=\"0\" cellpadding=\"10\">
        <tr>
        <td id=\"pageContent\">
<!-- ==================== End prologue ==================== -->

    <meta name=\"generator\" content=\"HARVESTMAN Internet Spider Version %(VERSION)s \">
    <TITLE>Local index - HarvestMan</TITLE>
</HEAD>
<h1 ALIGN=left><u>%(HEADER)s</i></h1>
    <TABLE BORDER=\"0\" WIDTH=\"100%(PER)s\" CELLSPACING=\"1\" CELLPADDING=\"0\">
    <BR>
        <TR align=center>
            <TD>
            %(PROJECTNAME)s
            </TD>
            <TD>&middot;
                <!-- PROJECTPAGE --><A HREF=\"%(PROJECTSTARTPAGE)s\"><!-- END -->
                    <!-- PROJECTURL -->%(PROJECTURL)s<!-- END -->
                </A>
            </TD>
        </TR>
    </TABLE>
    <BR>
    <BR>
    <BR>
    <H6 ALIGN=\"RIGHT\">
    <I>Mirror and index made by HARVESTMan Internet Spider [ABP &amp; NK 2003]</I>
    </H6>
<!-- ==================== Start epilogue ==================== -->
    </td>
    </tr>
    </table>
    </td>
    </tr>
    </table>
</td>
</tr>
</table>"""

HARVESTMAN_BROWSER_TABLE3="""\
<table width=\"76%(PER)s\" border=\"0\" align=\"center\" valign=\"bottom\" cellspacing=\"0\" cellpadding=\"0\">
    <tr>
    <td id=\"footer\"><small>%(CREDITS)s </small></td>
    </tr>
</table>"""

HARVESTMAN_CACHE_README="""\
This directory contains important cache information for HarvestMan.
This information is used by HarvestMan to update the project files.
If you delete this directory or its contents, the project update/caching
mechanism wont work.

"""

#=================================== End Browser page macro strings ===========================================
class Registry(object):

    class __registrySingleton(object):

        __slots__ = ('ini',
                     'ofs',
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
                     'asyncorethread')

        def __init__(self):
            self.ini = 0
            self.ofs = 0
            self.writeflag = 1
            self.USER_AGENT = 'HarvestMan 1.4'
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
                              'AsyncoreThread'      : 'asyncorethread'
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
            return None

    def __setattr__(self, name):
        return setattr(self.instance, name)

# Single instance of the global lookup object
RegisterObj = Registry()

def GetRegistryObject():
    """ Return the registry object """
    
    return RegisterObj

def GetObject(objkey):
    """ Get the registered instance of the HarvestMan program
    object using its key <objkey> by looking up the global
    registry object """

    try:
        obj = eval('RegisterObj.' + str(objkey), globals())
        if type(obj) is 'instance':
            return weakref.proxy(obj)
        else:
            return obj
    except (KeyError, AttributeError), e:
        print e
        return None

def GetUrlObject(key):
    """ Get url object based on its index (key) """

    if type(key) is int:
        wref = RegisterObj.urlmappings.get(key, None)
        return wref()
    else:
        return None
    
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
        urldict[key] = weakref.ref(obj)
    
def SetConfig(configobject):
    """ Set the config object  """

    global RegisterObj
    if RegisterObj.ini==0: Initialize()
    RegisterObj.config = configobject

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

def varprint(arg, *args):
    """ Our custom printing function """

    op=str(arg)
    for a in args:
        op = "".join((op, ' ',str(a)))

    print op
    global RegisterObj

    if RegisterObj.writeflag:
        try:
            RegisterObj.ofs.write("".join((op,'\n')))
            # RegisterObj.ofs.flush()
        except IOError, e:
            print e

def Initialize():
    """ Initialize the globals module. This
    initializes the registry object and a basic
    config object in the regsitry """

    global RegisterObj
    if RegisterObj.ini==1:
        return -1

    RegisterObj.ini = 1

    from config import HarvestManStateObject

    cfg = HarvestManStateObject()
    RegisterObj.config = cfg

def SetLogFile():
    
    logfile = RegisterObj.config.logfile
    try:
        RegisterObj.ofs = open(logfile, 'w')
        writeflag=1
    except OSError, e:
        print e

def Finish():
    """ Clean up this module. This function
    can be called at program exit or when
    handling signals to clean up """

    cfg=GetObject('config')
    # Stop url server if it is running
    if cfg.urlserver:
        # info('Stoppping url server...')
        async_t=GetObject('asyncorethread')
        if async_t:
            try:
                async_t.end()
            except socket.error, e:
                print e
            except Exception, e:
                print e
                
    global RegisterObj
    try:
        RegisterObj.ofs.flush()
        RegisterObj.ofs.close()
    except Exception, e:
        pass
    
    RegisterObj.writeflag = 0
    RegisterObj.ini = 0

    # inform user of config file errors
    if RegisterObj.userdebug:
        print "Some errors were found in your configuration, please correct them!"
        for x in range(0, len(RegisterObj.userdebug)):
            print str(x+1),':', RegisterObj.userdebug[x]

    RegisterObj.userdebug = []

def info(arg, *args):
    """ Print basic information, will print if verbosity is >=1 """

    # Setting verbosity to 1 will print the basic
    # messages like project info and final download stats.
    ConfigObj = GetObject('config')
    if ConfigObj.verbosity==0:
        return
    elif ConfigObj.verbosity>=1:
        varprint(arg, *args)

def moreinfo(arg, *args):
    """ Print more information, will print if verbosity is >=2 """

    # Setting verbosity to 2 will print the basic info
    # as well as detailed information regarding each downloaded link.
    ConfigObj = GetObject('config')
    if ConfigObj.verbosity==0:
        return
    elif ConfigObj.verbosity>=2:
        varprint(arg, *args)

def extrainfo(arg, *args):
    """ Print extra information, will print if verbosity is >=3 """

    # Setting verbosity to 3 will print more information on each link
    # as well as information of each thread downloading the link, as
    # well as some more extra information.
    ConfigObj = GetObject('config')
    if ConfigObj.verbosity==0:
        return
    elif ConfigObj.verbosity>=3:
        varprint(arg, *args)

def debug(arg, *args):
    """ Print debug information, will print if verbosity is >=4 """

    # Setting verbosity to 4 will print maximum information
    # plus extra debugging information.
    ConfigObj = GetObject('config')
    if ConfigObj.verbosity==0:
        return
    elif ConfigObj.verbosity>=4:
        varprint(arg, *args)

def moredebug(arg, *args):
    """ Print more debug information, will print if verbosity is >=5 """

    # Setting verbosity to 5 will print maximum information
    # plus maximum debugging information.
    ConfigObj = GetObject('config')
    if ConfigObj.verbosity==0:
        return
    elif ConfigObj.verbosity>=5:
        varprint(arg, *args)


def wasOrWere(val):
    """ What it says """

    if val > 1: return 'were'
    else: return 'was'

def plural((str, val)):
    """ What it says """

    if val>1:
        if str[len(str)-1] == 'y':
            return str[:len(str)-1]+'ies'
        else: return str+'s'
    else:
        return str

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


def filetype(filename, usemagicfile=False):
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
    
    cfg=GetObject('config')
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
    except socket.error, e:
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
        # print 'Response',response
        sock.close()
        return response
    except socket.error, e:
        pass

    return ''

def ping_urlserver(host, port):
    
    cfg=GetObject('config')
    if cfg.urlserver_protocol == 'tcp':
        return ping_urlserver_tcp(host, port)
    elif cfg.urlserver_protocol == 'udp':
        return ping_urlserver_udp(host, port)
        
def ping_urlserver_tcp(host, port):
    """ Ping url server to see if it is alive """

    # Returns server's response if server is
    # alive & null string if server is not alive.
    try:
        print 'Pinging server at (%s:%d)' % (host, port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host,port))
        # Send a small packet
        sock.sendall("ping")
        response = sock.recv(8192)
        if response:
            print 'Url server is alive'
        sock.close()
        return response
    except socket.error, e:
        print 'Could not connect to (%s:%d)' % (host, port)
        return ''

def ping_urlserver_udp(host, port):
    """ Ping url server to see if it is alive """

    # Returns server's response if server is
    # alive & null string if server is not alive.
    try:
        print 'Pinging server at (%s:%d)' % (host, port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Send a small packet
        bytes = sock.sendto("ping", 0, (host,port))
        response, addr = sock.recvfrom(8192,0)
        if response:
            print 'Url server is alive'
        sock.close()
        return response
    except socket.error, e:
        print 'Could not connect to (%s:%d)' % (host, port)
        return ''    
        


