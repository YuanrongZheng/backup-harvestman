# -- coding: latin-1
""" connector.py - Module to manage and retrieve data
    from an internet connection using urllib2. This module is
    part of the HarvestMan program.

    Author: Anand B Pillai (abpillai at gmail dot com).

    For licensing information see the file LICENSE.txt that
    is included in this distribution.

    Modification History
    ====================

    Aug 16 06         Restarted dev cycle. Fixed 2 bugs with 404
                      errors, one with setting directory URLs
                      and another with re-resolving URLs.
    Feb 8 2007        Added hooks support.

    Mar 5 2007        Modified cache check logic slightly to add
                      support for HTTP 304 errors. HarvestMan will
                      now use HTTP 304 if caching is enabled and
                      we have data cache for the URL being checked.
                      This adds true server-side cache check.
                      Older caching logic retained as fallback.

   Mar 7 2007         Added HTTP compression (gzip) support.
   Mar 8 2007         Added connect2 method for grabbing URLs.
                      Added interactive progress bar for connect2 method.
                      Improved interactive progress bar to resize
                      with changing size of terminal.

   Mar 9 2007         Made progress bar use Progress class borrowed
                      from SMART package manager (Thanks to Vaibhav
                      for pointing this out!)

   Mar 14 2007        Completed implementation of multipart with
                      range checks and all.

   Mar 26 2007        Finished implementation of multipart, integrating
                      with the crawler pieces. Resuming of URLs and
                      caching changes are pending.

   April 20 2007  Anand Added force-splitting option for hget.
   
   Copyright (C) 2004 Anand B Pillai.    
                              
"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

import sys
import socket
import time
import threading as tg

import urllib2 
import urlparse
import gzip
import cStringIO
import os

from common.common import *
from common.methodwrapper import MethodWrapperMetaClass

from urlparser import HarvestManUrlParser, HarvestManUrlParserError

# Defining pluggable functions
__plugins__ = { 'save_url_plugin': 'HarvestManUrlConnector:save_url' }

# Defining functions with callbacks
__callbacks__ = { 'connect_callback' : 'HarvestManUrlConnector:connect' }

__protocols__=["http", "ftp"]

class DataReader(tg.Thread):
    """ Data reader thread class which is used by
    the HarvestMan hget interface """
    
    def __init__(self, request, urltofetch, clength):
        self._request = request
        self._data = ''
        self._clength = int(clength)
        self._url = urltofetch
        self._bs = 1024*8
        self._start = 0.0
        self._flag = False
        tg.Thread.__init__(self, None, None, 'data reader')

    def initialize(self):
        self._start = time.time()
        
    def run(self):
        self.initialize()

        while not self._flag:
            block = self._request.read(self._bs)
            if block=='':
                self._flag = True
                break
            else:
                self._data += block
        
    def readNext(self):

        block = self._request.read(self._bs)
        if block=='':
            self._flag = True
            return False
        else:
            self._data += block

    def get_info(self):
        """ Return percentage, data downloaded, bandwidth, estimated time to
        complete as a tuple """

        if self._clength:
            per = float(100.0*len(self._data))/float(self._clength)
        else:
            per = -1
            
        l = len(self._data)
        bandwidth = float(l)/float(time.time() - self._start)
        if bandwidth and self._clength:
            eta = int((self._clength - l)/float(bandwidth))
            # Convert to hr:min:sec
            hh = eta/3600
            if hh:
                eta = (hh % 3600)
            
            mm = eta/60

            if mm:
                ss = (eta % 60)
            else:
                ss = eta

            if hh<10:
                hh = '0'+str(hh)
            if mm<10:
                mm = '0'+str(mm)
            if ss<10:
                ss = '0'+str(ss)
                
            eta = ':'.join((str(hh),str(mm),str(ss)))
        else:
            eta = 'NaN'
        
        return (per, l, bandwidth, eta)

    def get_data(self):
        return self._data

    def stop(self):
        self._flag = True
        
class MyRedirectHandler(urllib2.HTTPRedirectHandler):
    # maximum number of redirections to any single URL
    # this is needed because of the state that cookies introduce
    max_repeats = 4
    # maximum total number of redirections (regardless of URL) before
    # assuming we're in a loop
    max_redirections = 20

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        """Return a Request or None in response to a redirect.

        This is called by the http_error_30x methods when a
        redirection response is received.  If a redirection should
        take place, return a new Request to allow http_error_30x to
        perform the redirect.  Otherwise, raise HTTPError if no-one
        else should try to handle this url.  Return None if you can't
        but another Handler might.
        """

        m = req.get_method()
        
        if (code in (301, 302, 303, 307) and m in ("GET", "HEAD")
            or code in (301, 302, 303) and m == "POST"):

            # Strictly (according to RFC 2616), 301 or 302 in response
            # to a POST MUST NOT cause a redirection without confirmation
            # from the user (of urllib2, in this case).  In practice,
            # essentially all clients do redirect in this case, so we
            # do the same.
            newreq = urllib2.Request(newurl,
                                     headers=req.headers,
                                     origin_req_host=req.get_origin_req_host(),
                                     unverifiable=True)

            # Fix for url cookie headers
            # This makes sure that the redirection
            # will not fail if cookies are required
            # Works for any version of Python.
            # Jul 19 2005 - Anand
            for key in headers.keys():
                if key.lower().find('set-cookie') != -1:
                    cookie = headers[key]
                    newreq.add_header('Cookie',  cookie)
                    break

            return newreq
        
        else:
            raise urllib2.HTTPError(req.get_full_url(), code, msg, headers, fp)

    # Implementation note: To avoid the server sending us into an
    # infinite loop, the request object needs to track what URLs we
    # have already seen.  Do this by adding a handler-specific
    # attribute to the Request object.
    def http_error_302(self, req, fp, code, msg, headers):
        # Some servers (incorrectly) return multiple Location headers
        # (so probably same goes for URI).  Use first header.

        if 'location' in headers:
            newurl = headers.getheaders('location')[0]
        elif 'uri' in headers:
            newurl = headers.getheaders('uri')[0]
        else:
            return

        newurl = urlparse.urljoin(req.get_full_url(), newurl)

        # XXX Probably want to forget about the state of the current
        # request, although that might interact poorly with other
        # handlers that also use handler-specific request attributes
        new_req = self.redirect_request(req, fp, code, msg, headers, newurl)
        if not new_req:
            return

        # loop detection
        # .redirect_dict has a key url if url was previously visited.
        if hasattr(req, 'redirect_dict'):
            visited = new_req.redirect_dict = req.redirect_dict

            if (visited.get(newurl, 0) >= self.max_repeats or
                len(visited) >= self.max_redirections):
                
                raise urllib2.HTTPError(req.get_full_url(), code,
                                        self.inf_msg + msg, headers, fp)
        else:
            visited = new_req.redirect_dict = req.redirect_dict = {}
        visited[newurl] = visited.get(newurl, 0) + 1

        # Don't close the fp until we are sure that we won't use it
        # with HTTPError.
        fp.read()
        fp.close()

        return self.parent.open(new_req)

    http_error_301 = http_error_303 = http_error_307 = http_error_302

    inf_msg = "The HTTP server returned a redirect error that would " \
              "lead to an infinite loop.\n" \
              "The last 30x error message was:\n"

class HarvestManNetworkConnector(object):
    """ This class keeps the internet settings and configures
    the network. """
    
    def __init__(self):
        # use proxies flag
        self.__useproxy=0
        # check for ssl support in python
        self.__initssl=False
        # Number of socket errors
        self.__sockerrs = 0
        # Config object
        self.__cfg = GetObject('config')
        
        if hasattr(socket, 'ssl'):
            self.__initssl=True
            __protocols__.append("https")

        # dictionary of protocol:proxy values
        self.__proxydict = {}
        # dictionary of protocol:proxy auth values
        self.__proxyauth = {}
        self.__configure()
        
    def set_useproxy(self, val=True):
        """ Set the value of use-proxy flag. Also
        set proxy dictionaries to default values """

        self.__useproxy=val

        if val:
            proxystring = 'proxy:80'
            
            # proxy variables
            self.__proxydict["http"] =  proxystring
            self.__proxydict["https"] = proxystring
            self.__proxydict["ftp"] = proxystring
            # set default for proxy authentication
            # tokens.
            self.__proxyauth["http"] = ""
            self.__proxyauth["https"] = ""
            self.__proxyauth["ftp"] = ""            

    def set_ftp_proxy(self, proxyserver, proxyport, authinfo=(), encrypted=True):
        """ Set ftp proxy """

        if encrypted:
            self.__proxydict["ftp"] = "".join((bin_decrypt(proxyserver),  ':', str(proxyport)))
        else:
            self.__proxydict["ftp"] = "".join((proxyserver, ':', str(proxyport)))

        if authinfo:
            try:
                username, passwd = authinfo
            except ValueError:
                username, passwd = '', ''

            if encrypted:
                passwdstring= "".join((bin_decrypt(username), ':', bin_decrypt(passwd)))
            else:
                passwdstring = "".join((username, ':', passwd))

            self.__proxyauth["ftp"] = passwdstring

    def set_https_proxy(self, proxyserver, proxyport, authinfo=(), encrypted=True):
        """ Set https(ssl) proxy  """

        if encrypted:
            self.__proxydict["https"] = "".join((bin_decrypt(proxyserver), ':', str(proxyport)))
        else:
            self.__proxydict["https"] = "".join((proxyserver, ':', str(proxyport)))

        if authinfo:
            try:
                username, passwd = authinfo
            except ValueError:
                username, passwd = '', ''

            if encrypted:
                passwdstring= "".join((bin_decrypt(username), ':', bin_decrypt(passwd)))
            else:
                passwdstring = "".join((username, ':', passwd))

            self.__proxyauth["https"] = passwdstring

    def set_http_proxy(self, proxyserver, proxyport, authinfo=(), encrypted=True):
        """ Set http proxy """

        if encrypted:
            self.__proxydict["http"] = "".join((bin_decrypt(proxyserver), ':', str(proxyport)))
        else:
            self.__proxydict["http"] = "".join((proxyserver, ':', str(proxyport)))

        if authinfo:
            try:
                username, passwd = authinfo
            except ValueError:
                username, passwd = '', ''

            if encrypted:
                passwdstring= "".join((bin_decrypt(username), ':', bin_decrypt(passwd)))
            else:
                passwdstring= "".join((username, ':', passwd))

            self.__proxyauth["http"] = passwdstring

    def set_proxy(self, server, port, authinfo=(), encrypted=True):
        """ Set generic (all protocols) proxy values.
        For most users, only this method will be called,
        rather than the specific method for each protocol,
        as proxies are normally shared for all tcp/ip protocols """

        for p in __protocols__:
            # eval helps to do this dynamically
            s='self.set_' + p + '_proxy'
            func=eval(s, locals())
            
            func(server, port, authinfo, encrypted)

    def set_authinfo(self, username, passwd, encrypted=True):
        """ Set authentication information for proxy.
        Note: If this function is used all protocol specific
        authentication will be replaced by this authentication. """

        if encrypted:
            passwdstring = "".join((bin_decrypt(username), ':', bin_decrypt(passwd)))
        else:
            passwdstring = "".join((username, ':', passwd))

        self.__proxyauth = {"http" : passwdstring,
                            "https" : passwdstring,
                            "ftp" : passwdstring }

    def configure_protocols(self):
        """ Just a wrapper """
        
        self.__configure_protocols()

    def configure_network(self):
        """ Just a wrapper """

        self.__configure_network()

    def __configure(self):
        """ Wrapping up wrappers """
        
        self.__configure_network()
        self.__configure_protocols()
        
    def __configure_network(self):
        """ Initialise network for the user """

        # First: Configuration of network (proxies/intranet etc)
        
        # Check for proxies in the config object
        if self.__cfg.proxy:
            self.set_useproxy(True)
            proxy = self.__cfg.proxy
            
            index = proxy.rfind(':')
            if index != -1:
                port = proxy[(index+1):].strip()
                server = proxy[:index]
                # strip of any 'http://' from server
                index = server.find('http://')
                if index != -1:
                    server = server[(index+7):]

                self.set_proxy(server, int(port), (), self.__cfg.proxyenc)

            else:
                port = self.__cfg.proxyport
                server = self.__cfg.proxy
                self.set_proxy(server, int(port), (), self.__cfg.proxyenc)

            # Set proxy username and password, if specified
            puser, ppasswd = self.__cfg.puser, self.__cfg.ppasswd
            if puser and ppasswd: self.set_authinfo(puser, ppasswd, self.__cfg.proxyenc)


    def __configure_protocols(self):
        """ Configure protocol handlers """
        
        # Second: Configuration of protocol handlers.

        # TODO: Verify gopher protocol
        authhandler = urllib2.HTTPBasicAuthHandler()
        cookiehandler = None
        
        # set timeout for sockets to thread timeout, for Python 2.3
        # and greater. 
        minor_version = sys.version_info[1]
        if minor_version>=3:
            socket.setdefaulttimeout( self.__cfg.timeout )
            # For Python 2.4, use cookielib support
            # To fix HTTP cookie errors such as those
            # produced by http://www.eidsvoll.kommune.no/
            if minor_version>=4:
                import cookielib
                cj = cookielib.MozillaCookieJar()
                cookiehandler = urllib2.HTTPCookieProcessor(cj)
                pass
            
        # If we are behing proxies/firewalls
        if self.__useproxy:
            if self.__proxyauth['http']:
                httpproxystring = "".join(('http://',
                                           self.__proxyauth['http'],
                                           '@',
                                           self.__proxydict['http']))
            else:
                httpproxystring = "".join(('http://', self.__proxydict['http']))

            if self.__proxyauth['ftp']:
                ftpproxystring = "".join(('http://',
                                          self.__proxyauth['ftp'],
                                          '@',
                                          self.__proxydict['ftp']))
            else:
                ftpproxystring = "".join(('http://', self.__proxydict['ftp']))

            if self.__proxyauth['https']:
                httpsproxystring = "".join(('http://',
                                            self.__proxyauth['https'],
                                            '@',
                                            self.__proxydict['https']))
            else:
                httpsproxystring = "".join(('http://', self.__proxydict['https']))

            # Set this as the new entry in the proxy dictionary
            self.__proxydict['http'] = httpproxystring
            self.__proxydict['ftp'] = ftpproxystring
            self.__proxydict['https'] = httpsproxystring

            
            proxy_support = urllib2.ProxyHandler(self.__proxydict)
            
            # build opener and install it
            if self.__initssl:
                opener = urllib2.build_opener(authhandler,
                                              MyRedirectHandler,
                                              proxy_support,
                                              urllib2.HTTPHandler,
                                              urllib2.HTTPDefaultErrorHandler,
                                              urllib2.CacheFTPHandler,
                                              urllib2.GopherHandler,
                                              urllib2.HTTPSHandler,
                                              urllib2.FileHandler,
                                              cookiehandler)
            else:
                opener = urllib2.build_opener(authhandler,
                                              MyRedirectHandler,
                                              proxy_support,
                                              urllib2.HTTPHandler,
                                              urllib2.HTTPDefaultErrorHandler,
                                              urllib2.CacheFTPHandler,
                                              urllib2.GopherHandler,
                                              urllib2.FileHandler,
                                              cookiehandler)

        else:
            # Direct connection to internet
            if self.__initssl:
                opener = urllib2.build_opener(authhandler,
                                              MyRedirectHandler,
                                              urllib2.HTTPHandler,
                                              urllib2.CacheFTPHandler,
                                              urllib2.HTTPSHandler,
                                              urllib2.GopherHandler,
                                              urllib2.FileHandler,
                                              urllib2.HTTPDefaultErrorHandler,
                                              cookiehandler)
            else:
                opener = urllib2.build_opener( authhandler,
                                               MyRedirectHandler,
                                               urllib2.HTTPHandler,
                                               urllib2.CacheFTPHandler,
                                               urllib2.GopherHandler,
                                               urllib2.FileHandler,
                                               urllib2.HTTPDefaultErrorHandler,
                                               cookiehandler)

        opener.addheaders = [ ('User-agent', GetObject('USER_AGENT')) ]
        urllib2.install_opener(opener)

        return 0

    # Get methods
    def get_useproxy(self):
        """ Find out if we are using proxies """

        return self.__useproxy
    
    def get_proxy_info(self):
        return (self.__proxydict, self.__proxyauth)

    def increment_socket_errors(self, val=1):
        self.__sockerrs += val

    def decrement_socket_errors(self, val=1):
        self.__sockerrs -= val
        
    def get_socket_errors(self):
        return self.__sockerrs
        
class HarvestManUrlConnector(object):
    """ Class which helps to connect to the internet """

    __metaclass__ = MethodWrapperMetaClass
    
    def __str__(self):
        return `self` 
        
    def __init__(self):
        """ Constructor for this class """

        # file like object returned by
        # urllib2.urlopen(...)
        self.__freq = urllib2.Request('file://')
        # data downloaded
        self.__data = ''
        # error dictionary
        self.__error={ 'msg' : '',
                       'number': 0,
                       'fatal' : False
                       }
        # time to wait before reconnect
        # in case of failed connections
        self.__sleeptime = 0.5
        # global network configurator
        self.network_conn = GetObject('connector')
        # Config object
        self._cfg = GetObject('config')        
        # Http header for current connection
        self._headers = CaselessDict()
        # Data reader object - used by hget
        self._reader = None
        # Elasped time for reading data
        self._elasped = 0.0
        
    def __del__(self):
        del self.__data
        self.__data = None
        del self.__freq
        self.__freq = None
        del self.__error
        self.__error = None
        del self.network_conn
        self.network_conn = None
        del self._cfg
        self._cfg = None
        
    def __proxy_query(self, queryauth=1, queryserver=0):
        """ Query the user for proxy related information """

        self.network_conn.set_useproxy(True)
        
        if queryserver or queryauth:
            # There is an error in the config file/project file/user input
            SetUserDebug("Error in proxy server settings (Regenerate the config/project file)")

        # Get proxy info from user
        try:
            if queryserver:
                server=bin_crypt(raw_input('Enter the name/ip of your proxy server: '))
                port=int(raw_input('Enter the proxy port: '))         
                self.network_conn.set_proxy(server, port)

            if queryauth:
                user=bin_crypt(raw_input('Enter username for your proxy server: '))
                # Ask for password only if a valid user is given.
                if user:
                    import getpass
                    passwd=bin_crypt(getpass.getpass('Enter password for your proxy server: '))
                    # Set it on myself and re-configure
                    self.network_conn.set_authinfo(user,passwd)
        except EOFError, e:
            debug(str(e))

        moreinfo('Re-configuring protocol handlers...')
        self.network_conn.configure_protocols()
        
        moreinfo('Done.')

    def urlopen(self, url):
        """ Open the url and return the url file stream """

        self.connect(url, None, True, self._cfg.retryfailed )
        # return the file like object
        if self.__error['fatal']:
            return None
        else:
            return self.__freq

    def robot_urlopen(self, url):
        """ Open a robots.txt url """

        self.connect(url, None, False, 0)
        # return the file like object
        if self.__error['fatal']:
            return None
        else:
            return self.__freq
    
    def connect(self, urltofetch, url_obj = None, fetchdata=True, retries=1, lastmodified=-1):
        """ Connect to the Internet fetch the data of the passed url """

        # This routine has four possible return values
        #
        # -1 => Could not connect to URL and download data due
        #       to some error.
        # 0 => Downloaded URL and got data without error.
        # 1 => Server returned a 304 error because our local
        #      cache was uptodate.
        # 2 => There was a rules violation, so we dont bother
        #      to download this URL.
        
        data = '' 

        dmgr = GetObject('datamanager')
        rulesmgr = GetObject('ruleschecker')

        if url_obj:
            hu = url_obj
        else:
            try:
                hu = HarvestManUrlParser(urltofetch)
            except HarvestManUrlParserError, e:
                debug(str(e))

        
        numtries = 0
        three_oh_four = False

        # Reset the http headers
        self._headers.clear()
        
        while numtries <= retries and not self.__error['fatal']:

            errnum = 0
            try:
                # Reset error
                self.__error = { 'number' : 0,
                                 'msg' : '',
                                 'fatal' : False }

                numtries += 1

                # create a request object
                request = urllib2.Request(urltofetch)
                    
                if lastmodified != -1:
                    ts = time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                       time.localtime(lastmodified))
                    request.add_header('If-Modified-Since', ts)


                # Check for urlobject which is trying to do
                # multipart download.
                byterange = hu.range
                if byterange:
                    range1 = byterange[0]
                    range2 = byterange[-1]
                    request.add_header('Range','bytes=%d-%d' % (range1, range2))

                # If we accept http-compression, add the required header.
                if self._cfg.httpcompress:
                    request.add_header('Accept-Encoding', 'gzip')
                    
                self.__freq = urllib2.urlopen(request)
                # Set http headers
                self.set_http_headers()

                clength = int(self.get_content_length())

                trynormal = False
                # Check constraint on file size, dont do this on
                # objects which are already downloading pieces of
                # a multipart download.
                if not byterange and not self.check_content_length():
                    maxsz = self._cfg.maxfilesize
                    extrainfo("Url",urltofetch,"does not match size constraints, trying multi-part download...")
                    supports_multipart = dmgr.supports_range_requests(hu)
                    # print 'supports multipart=>',supports_multipart
                    
                    # Dont do range checking on FTP servers since they
                    # typically support it by default.
                    if hu.protocol != 'ftp' and supports_multipart==0:
                        # See if the server supports 'Range' header
                        # by requesting half the length
                        self._headers.clear()
                        request.add_header('Range','bytes=%d-%d' % (0,clength/2))
                        self.__freq = urllib2.urlopen(request)
                        # Set http headers
                        self.set_http_headers()
                        range_result = self._headers.get('accept-ranges')

                        if range_result.lower()=='bytes':
                            supports_multipart = 1
                        else:
                            extrainfo('Server %s does not support multipart downloads' % hu.domain)
                            extrainfo('Aborting download of  URL %s.' % urltofetch)
                            return 2

                    if supports_multipart==1:
                        extrainfo('Server %s supports multipart downloads' % hu.domain)
                        # hu.trymultipart = True
                        dmgr.download_multipart_url(hu, clength)
                        return 3
                    
                # The actual url information is used to
                # differentiate between directory like urls
                # and file like urls.
                actual_url = self.__freq.geturl()
                # print 'ACTUAL URL=>',actual_url
                
                # Replace the urltofetch in actual_url with null
                if actual_url:
                    no_change = (actual_url == urltofetch)
                    
                    if not no_change:
                        
                        replacedurl = actual_url.replace(urltofetch, '')
                        # If the difference is only as a directory url
                        if replacedurl=='/':
                            no_change = True
                            
                        # Sometimes, there could be HTTP re-directions which
                        # means the actual url may not be same as original one.

                        if actual_url[-1] == '/' and urltofetch[-1] != '/':
                            extrainfo('Setting directory url=>',urltofetch)
                            hu.set_directory_url()

                        if not no_change:
                            # There is considerable change in the URL.
                            # So we need to re-resolve it, since otherwise
                            # some child URLs which derive from this could
                            # be otherwise invalid and will result in 404
                            # errors.
                            
                            hu.url = actual_url
                            hu.wrapper_resolveurl()
                            
                    
                # Find the actual type... if type was assumed
                # as wrong, correct it.
                content_type = self.get_content_type()
                hu.manage_content_type(content_type)
                        
                # update byte count
                # if this is the not the first attempt, print a success msg
                if numtries>1:
                    moreinfo("Reconnect succeeded => ", urltofetch)

                # Update content info on urlobject
                self.set_content_info(hu)

                if fetchdata:
                    try:
                        # If gzip-encoded, need to deflate data
                        encoding = self.get_content_encoding()

                        t1 = time.time()
                        data = self.__freq.read()

                        self._elapsed = time.time() - t1
                        
                        # Save a reference
                        data0 = data
                        self.__freq.close()                        
                        dmgr.update_bytes(len(data))
                        
                        if encoding.strip().find('gzip') != -1:
                            try:
                                gzfile = gzip.GzipFile(fileobj=cStringIO.StringIO(data))
                                data = gzfile.read()
                                gzfile.close()
                            except (IOError, EOFError), e:
                                data = data0
                                #extrainfo('Error deflating HTTP compressed data:',str(e))
                                pass
                            
                    except MemoryError, e:
                        # Catch memory error for sockets
                        debug('Error:',str(e))
                break
            except urllib2.HTTPError, e:

                try:
                    errbasic, errdescn = (str(e)).split(':',1)
                    parts = errbasic.strip().split()
                    self.__error['number'] = int(parts[-1])
                    self.__error['msg'] = errdescn.strip()
                except:
                    pass

                if self.__error['msg']:
                    extrainfo(self.__error['msg'], '=> ',urltofetch)
                else:
                    extrainfo('HTTPError:',urltofetch)

                try:
                    errnum = int(self.__error['number'])
                except:
                    pass

                if errnum==304:
                    # Page not modified
                    three_oh_four = True
                    self.__error['fatal'] = False
                    # Need to do this to ensure that the crawler
                    # proceeds further!
                    content_type = self.get_content_type()
                    hu.manage_content_type(content_type)                    
                    break
                if errnum == 407: # Proxy authentication required
                    self.__proxy_query(1, 1)
                elif errnum == 503: # Service unavailable
                    rulesmgr.add_to_filter(urltofetch)
                    self.__error['fatal']=True                        
                elif errnum == 504: # Gateway timeout
                    rulesmgr.add_to_filter(urltofetch)
                    self.__error['fatal']=True                        
                elif errnum in range(500, 505): # Server error
                    self.__error['fatal']=True
                elif errnum == 404:
                    # Link not found, this might
                    # be a file wrongly fetched as directory
                    # Add to filter
                    rulesmgr.add_to_filter(urltofetch)
                    self.__error['fatal']=True
                elif errnum == 401: # Site authentication required
                    self.__error['fatal']=True
                    break

            except urllib2.URLError, e:
                # print 'Error=>',e
                errdescn = ''
                
                try:
                    errbasic, errdescn = (str(e)).split(':',1)
                    parts = errbasic.split()                            
                except:
                    try:
                        errbasic, errdescn = (str(e)).split(',')
                        parts = errbasic.split('(')
                        errdescn = (errdescn.split("'"))[1]
                    except:
                        pass

                try:
                    self.__error['number'] = int(parts[-1])
                except:
                    pass
                
                if errdescn:
                    self.__error['msg'] = errdescn
                else:
                    print 'errdescn is null!'

                if self.__error['msg']:
                    extrainfo(self.__error['msg'], '=> ',urltofetch)
                else:
                    extrainfo('URLError:',urltofetch)

                errnum = self.__error['number']
                if errnum == 10049 or errnum == 10061: # Proxy server error
                    self.__proxy_query(1, 1)
                elif errnum == 10055:
                    # no buffer space available
                    self.network_conn.increment_socket_errors()
                    # If the number of socket errors is >= 4
                    # we decrease max connections by 1
                    sockerrs = self.network_conn.get_socket_errors()
                    if sockerrs>=4:
                        self._cfg.connections -= 1
                        self.network_conn.decrement_socket_errors(4)

            except IOError, e:
                self.__error['number'] = 31
                self.__error['fatal']=True
                self.__error['msg'] = str(e)                    
                # Generated by invalid ftp hosts and
                # other reasons,
                # bug(url: http://www.gnu.org/software/emacs/emacs-paper.html)
                extrainfo(e ,'=> ',urltofetch)

            except ValueError, e:
                self.__error['number'] = 41
                self.__error['msg'] = str(e)                    
                extrainfo(e, '=> ',urltofetch)

            except AssertionError, e:
                self.__error['number'] = 51
                self.__error['msg'] = str(e)
                extrainfo(e ,'=> ',urltofetch)

            except socket.error, e:
                self.__error['msg'] = str(e)
                errmsg = self.__error['msg']

                extrainfo('Socket Error: ', errmsg,'=> ',urltofetch)

                if errmsg.lower().find('connection reset by peer') != -1:
                    # Connection reset by peer (socket error)
                    self.network_conn.increment_socket_errors()
                    # If the number of socket errors is >= 4
                    # we decrease max connections by 1
                    sockerrs = self.network_conn.get_socket_errors()

                    if sockerrs>=4:
                        self._cfg.connections -= 1
                        self.network_conn.decrement_socket_errors(4)
            except Exception, e:
                self.__error['msg'] = str(e)
                errmsg = self.__error['msg']

                extrainfo('General Error: ', errmsg,'=> ',urltofetch)
                
            # attempt reconnect after some time
            time.sleep(self.__sleeptime)

        
        if data: self.__data = data

        if url_obj:
            url_obj.status = self.__error['number']
            url_obj.fatal = self.__error['fatal']

        # If three_oh_four, return ok
        if three_oh_four:
            return 1
            
        if data:
            return 0
        else:
            return -1

    def set_progress_object(self, topic, n=0, subtopics=[], nolengthmode=False):
        """ Set the progress bar object with the given topic
        and sub-topics """

        # n=> number of subtopics
        # topic => Topic
        # subtopics => List of subtopics

        # n should be = len(subtopics)
        if n != len(subtopics):
            return False

        # Create progress object
        prog = self._cfg.progressobj
        prog.setTopic(topic)
        #if n==1:
        prog.set(100, 100)
        #else:
        #    prog.set(n, 100)
        
        if nolengthmode:
            prog.setNoLengthMode(True)

        if n>0:
            prog.setHasSub(True)
            if not nolengthmode:
                for x in range(1,n+1):
                    prog.setSubTopic(x, subtopics[x-1])
                    prog.setSub(x, 0.0, 100)
        else:
            pass
            
                               
    def connect2(self, urlobj, showprogress=True):
        """ Connect to the Internet fetch the data of the passed url.
        This is called by the stand-alone URL grabber """

        # This routine has two return values
        #
        # -1 => Could not connect to URL and download data due
        #       to some error.
        # 0 => Downloaded URL and got data without error.
        
        data = '' 

        # Reset the http headers
        self._headers.clear()
        retries = 1
        numtries = 0

        urltofetch = urlobj.get_full_url()
        filename = urlobj.get_filename()

        dmgr = GetObject('datamanager')
            
        while numtries <= retries and not self.__error['fatal']:

            errnum = 0
            try:
                # Reset error
                self.__error = { 'number' : 0,
                                 'msg' : '',
                                 'fatal' : False }

                numtries += 1

                # create a request object
                request = urllib2.Request(urltofetch)
                byterange = urlobj.range
                
                if byterange:
                    range1 = byterange[0]
                    range2 = byterange[-1]
                    request.add_header('Range','bytes=%d-%d' % (range1,range2))
                
                self.__freq = urllib2.urlopen(request)
                
                # Set http headers
                self.set_http_headers()

                encoding = self.get_content_encoding()
                ctype = self.get_content_type()
                clength = int(self.get_content_length())

                if clength==0:
                    clength_str = 'Unknown'
                elif clength>=1024*1024:
                    clength_str = '%dM' % (clength/(1024*1024))
                elif clength >=1024:
                    clength_str = '%dK' % (clength/1024)
                else:
                    clength_str = '%d bytes' % clength

                if not urlobj.range:
                    if clength:
                        logconsole('Length: %d (%s) Type: %s' % (clength, clength_str, ctype))
                        nolengthmode = False
                    else:
                        logconsole('Length: (%s) Type: %s' % (clength_str, ctype))
                        nolengthmode = True

                    logconsole('Content Encoding: %s\n' % encoding)

                trynormal = False
                # Check constraint on file size
                if (not byterange and self._cfg.forcesplit) or \
                       (not byterange and not self.check_content_length()):
                    maxsz = self._cfg.maxfilesize
                    if not self._cfg.forcesplit:
                        logconsole('Maximum file size for single downloads is %.0f bytes.' % maxsz)
                        logconsole("Url does not match size constraints")
                    else:
                        logconsole('Forcing download into %d parts' % self._cfg.numparts)
                        
                    # Dont do range checking on FTP servers since they
                    # typically support it by default.

                    if urlobj.protocol != 'ftp://':
                        # logconsole('Checking whether server supports multipart downloads...')
                        # See if the server supports 'Range' header
                        # by requesting half the length
                        self._headers.clear()
                        request.add_header('Range','bytes=%d-%d' % (0,clength/2))
                        self.__freq = urllib2.urlopen(request)
                        # Set http headers
                        self.set_http_headers()
                        range_result = self._headers.get('accept-ranges')
                        if range_result.lower()=='bytes':
                            logconsole('Server supports multipart downloads')
                        else:
                            logconsole('Server does not support multipart downloads')
                            resp = raw_input('Do you still want to download this URL [y/n] ?')
                            if resp.lower() !='y':
                                logconsole('Aborting download.')
                                return 3
                            else:
                                logconsole('Downloading URL %s...' % urltofetch)
                                trynormal = True


                    if not trynormal:
                        logconsole('Trying multipart download...')
                        # urlobj.trymultipart = True
                        
                        ret = dmgr.download_multipart_url(urlobj, clength)
                        if ret==1:
                            logconsole('Cannot do multipart download, piece size greater than maxfile size!')
                            return 3
                        elif ret==0:
                            # Set progress object
                            if showprogress:
                                self.set_progress_object(filename,1,[filename],nolengthmode)
                            return 2
                    
                # if this is the not the first attempt, print a success msg
                if numtries>1:
                    logconsole("Reconnect succeeded => ", urltofetch)

                try:
                    # Don't set progress object if multipart download - it
                    # would have been done before.
                    if not urlobj.range and showprogress:
                        self.set_progress_object(filename,1,[filename],nolengthmode)
                    
                    prog = self._cfg.progressobj
                    
                    mypercent = 0.0
                    
                    self._reader = DataReader(self.__freq, urltofetch, clength)
                    # Don't run as thread for multipart downloads
                    if self._cfg.multipart:
                        self._reader.initialize()
                    else:
                        self._reader.start()

                    t1 = time.time()
                    
                    while True:
                        if self._cfg.multipart: self._reader.readNext()
                        

                        if clength:
                            percent,l,bw,eta = self._reader.get_info()
                            
                            if percent and showprogress:
                                prog.setScreenWidth(prog.getScreenWidth())
                                #subdata = {'item-number': urlobj.mindex+1}
                                prog.setSubTopic(1, filename)
                                if urlobj.range:
                                    # If multi-part, calculate actual percentage
                                    urlobj.__class__.partlengths[urlobj.mindex] = l
                                    # Get data-downloaded sofar
                                    datasofar = sum(urlobj.__class__.partlengths)
                                    percent = int(100*float(datasofar)/float(urlobj.clength))
                                    t = threading.currentThread()
                                    prog.setSubTopic(1, '('+t.getName()+') ' + filename)

                                prog.setSub(1, percent, 100) #, subdata=subdata)
                                prog.show()
                                    
                            if percent==100.0: break
                        else:
                            if mypercent and showprogress:
                                prog.setScreenWidth(prog.getScreenWidth())
                                prog.setSubTopic(1, filename)
                                prog.setSub(1, mypercent, 100)
                                prog.show()
                                
                            if self._reader._flag: break
                            mypercent += 2.0
                            if mypercent==100.0: mypercent=0.0

                    self._elapsed = time.time() - t1
                    
                    data = self._reader.get_data()

                except MemoryError, e:
                    # Catch memory error for sockets
                    pass
                    
                break
            except urllib2.HTTPError, e:

                try:
                    errbasic, errdescn = (str(e)).split(':',1)
                    parts = errbasic.strip().split()
                    self.__error['number'] = int(parts[-1])
                    self.__error['msg'] = errdescn.strip()
                except:
                    pass

                if self.__error['msg']:
                    logconsole(self.__error['msg'], '=> ',urltofetch)
                else:
                    logconsole('HTTPError:',urltofetch)

                try:
                    errnum = int(self.__error['number'])
                except:
                    pass

                if errnum == 407: # Proxy authentication required
                    self.__proxy_query(1, 1)
                elif errnum == 503: # Service unavailable
                    self.__error['fatal']=True                        
                elif errnum == 504: # Gateway timeout
                    self.__error['fatal']=True                        
                elif errnum in range(500, 505): # Server error
                    self.__error['fatal']=True
                elif errnum == 404:
                    self.__error['fatal']=True
                elif errnum == 401: # Site authentication required
                    self.__error['fatal']=True
                    break

            except urllib2.URLError, e:
                errdescn = ''
                
                try:
                    errbasic, errdescn = (str(e)).split(':',1)
                    parts = errbasic.split()                            
                except:
                    try:
                        errbasic, errdescn = (str(e)).split(',')
                        parts = errbasic.split('(')
                        errdescn = (errdescn.split("'"))[1]
                    except:
                        pass

                try:
                    self.__error['number'] = int(parts[-1])
                except:
                    pass
                
                if errdescn:
                    self.__error['msg'] = errdescn

                if self.__error['msg']:
                    logconsole(self.__error['msg'], '=> ',urltofetch)
                else:
                    logconsole('URLError:',urltofetch)

                errnum = self.__error['number']
                if errnum == 10049 or errnum == 10061: # Proxy server error
                    self.__proxy_query(1, 1)

            except IOError, e:
                self.__error['number'] = 31
                self.__error['fatal']=True
                self.__error['msg'] = str(e)                    
                # Generated by invalid ftp hosts and
                # other reasons,
                # bug(url: http://www.gnu.org/software/emacs/emacs-paper.html)
                logconsole(e,'=>',urltofetch)

            except ValueError, e:
                self.__error['number'] = 41
                self.__error['msg'] = str(e)                    
                logconsole(e,'=>',urltofetch)

            except AssertionError, e:
                self.__error['number'] = 51
                self.__error['msg'] = str(e)
                logconsole(e,'=>',urltofetch)

            except socket.error, e:
                self.__error['msg'] = str(e)
                errmsg = self.__error['msg']

                logconsole('Socket Error: ',errmsg,'=> ',urltofetch)

            # attempt reconnect after some time
            time.sleep(self.__sleeptime)

        if data: self.__data = data
            
        if data:
            return 0
        else:
            return -1
        
    def get_error(self):
        return self.__error

    def set_content_info(self, urlobj):
        """ Set the content information on the current
        url object """

        # set this on the url object
        urlobj.set_url_content_info(self._headers)

    def set_http_headers(self):
        """ Set http header dictionary from current request """

        self._headers.clear()
        for key,val in dict(self.__freq.headers).iteritems():
            self._headers[key] = val
        
    def print_http_headers(self):
        """ Print the HTTP headers for this connection """

        print 'HTTP Headers '
        for k,v in self._headers().iteritems():
            print k,'=> ', v

        print '\n'

    def get_content_length(self):

        clength = self._headers.get('content-length', 0)
        if clength != 0:
            # Sometimes this could be two numbers
            # separated by commas.
            return clength.split(',')[0].strip()
        else:
            return len(self.__data)

    def check_content_length(self):

        # check for min & max file size
        try:
            length = int(self.get_content_length())
        except:
            length = 0
            
        return (length <= self._cfg.maxfilesize)
        
    def get_content_type(self):

        ctype = self._headers.get('content-type','')
        if ctype:
            # Sometimes content type
            # definition might have
            # the charset information,
            # - .stx files for example.
            # Need to strip out that
            # part, if any
            if ctype.find(';') != -1:
                ctype2, charset = ctype.split(';')
                if ctype2: ctype = ctype2
            
        return ctype
            
    def get_last_modified_time(self):

        return self._headers.get('last-modified','')

    def get_content_encoding(self):
        return self._headers.get('content-encoding', 'plain')
                                 
    def __write_url(self, filename):
        """ Write downloaded data to the passed file """

        if self.__data=='':
            return 0

        try:
            extrainfo('Writing file ', filename)
            f=open(filename, 'wb')
            f.write(self.__data)
            f.close()
        except IOError,e:
            debug('IO Exception' , str(e))
            return 0
        except ValueError, e:
            return 0

        return 1

    def wrapper_connect(self, urlobj):
        """ Wrapper for connect methods """

        if self._cfg.nocrawl:
            return self.connect2(urlobj)
        else:
            url = urlobj.get_full_url()
            # See if this URL is in cache, then get its lmt time & data
            dmgr=GetObject('datamanager')

            lmt,cache_data = dmgr.get_last_modified_time_and_data(urlobj)
            return self.connect(url, urlobj, True, self._cfg.retryfailed, lmt)            
                        
    def save_url(self, urlobj):
        """ Download data from the url <url> and write to
        the file <filename> """

        # Rearranged this to take care of http 304
        url = urlobj.get_full_url()

        # See if this URL is in cache, then get its lmt time & data
        dmgr=GetObject('datamanager')
        lmt,cache_data = dmgr.get_last_modified_time_and_data(urlobj)
        res = self.connect(url, urlobj, True, self._cfg.retryfailed, lmt)
        
        # If it was a rules violation, skip it
        if res==2: return res

        # If this became a request for multipart download
        # wait for the download to complete.
        if res==3:
            # Trying multipart download...
            pool = dmgr.get_url_threadpool()
            while not pool.get_download_status(url):
                time.sleep(1.0)

            data = pool.get_url_data(url)
            self.__data = data

            directory = urlobj.get_local_directory()
            if dmgr.create_local_directory(directory) == 0:
                return self.__write_url( urlobj.get_full_filename() )
            else:
                extrainfo("Error in creating local directory for", url)
                return 0
                
        retval=0
        # Apply word filter
        if not urlobj.starturl:
            if urlobj.is_webpage() and not GetObject('ruleschecker').apply_word_filter(self.__data):
                extrainfo("Word filter prevents download of url =>", url)
                return 5

        # If no need to save html files return from here
        if urlobj.is_webpage() and not self._cfg.html:
            extrainfo("Html filter prevents download of url =>", url)
            return 5

        # Get last modified time
        timestr = self.get_last_modified_time()
        filename = urlobj.get_full_filename()

        if self._cfg.cachefound:
            # Three levels of cache check.
            # If this caused a 304 error, then our copy is up-to-date
            # so nothing to be done.
            if res==1:
                extrainfo("Project cache is uptodate =>", url)
                # Set the data as cache-data
                self.__data = cache_data
                return 3
            
            # Most of the web-servers will work with above logic. For
            # some reason if the server does not return 304, we have
            # two fall-back checks.
            #
            # 1. If a time-stamp is returned, this is compared with
            # local timestamp.
            # 2. If no time-stamp is returned, we do the actual check
            # of comparing a checksum of the downloaded data with the
            # existing checksum.
            
            update, fileverified = False, False
            
            if timestr:
                try:
                    lmt = time.mktime( time.strptime(timestr, "%a, %d %b %Y %H:%M:%S GMT"))
                    update, fileverified = dmgr.is_url_uptodate(urlobj, filename, lmt, self.__data)

                    # No need to download
                    if update and fileverified:
                        extrainfo("Project cache is uptodate =>", url)
                        return 3                        
                except ValueError, e:
                    pass

            else:
                datalen = self.get_content_length()
                update, fileverified = dmgr.is_url_cache_uptodate(urlobj, filename, datalen, self.__data)
                # No need to download
                if update and fileverified:
                    extrainfo("Project cache is uptodate =>", url)
                    return 3

            # If cache is up to date, but someone has deleted
            # the downloaded files, instruct data manager to
            # write file from the cache.
            if update and not fileverified:
                if dmgr.write_file_from_cache(urlobj):
                    return 4
        else:
            # If no cache was loaded, then create the cache.
            if timestr:
                lmt = time.mktime( time.strptime(timestr, "%a, %d %b %Y %H:%M:%S GMT"))
                dmgr.wrapper_update_cache_for_url2(urlobj, filename, lmt, self.__data)
            else:
                datalen = self.get_content_length()
                dmgr.wrapper_update_cache_for_url(urlobj, filename, datalen, self.__data)


        directory = urlobj.get_local_directory()
        if dmgr.create_local_directory(directory) == 0:
            retval=self.__write_url( filename )
        else:
            extrainfo("Error in creating local directory for", url)
            
        return retval

    def calc_bandwidth(self, urlobj):
        """ Calculate bandwidth using URL """

        url = urlobj.get_full_url()
        # Set verbosity to silent
        logobj = GetObject('logger')
        self._cfg.verbosity = 0
        logobj.setLogSeverity(0)
        ret = self.connect2(urlobj, showprogress=False)
        # Reset verbosity
        self._cfg.verbosity = self._cfg.verbosity_default
        logobj.setLogSeverity(self._cfg.verbosity)
        
        if self.__data:
            return float(len(self.__data))/(self._elapsed)
        else:
            return 0
        
    def url_to_file(self, urlobj):
        """ Save the contents of this url <url> to the file <filename>.
        This is used by the -N option of HarvestMan """

        url = urlobj.get_full_url()
        print 'Connecting to %s...' % urlobj.get_full_domain()
        ret = self.connect2(urlobj)
        if ret==2:
            # Trying multipart download...
            pool = GetObject('datamanager').get_url_threadpool()
            while not pool.get_download_status(url):
                time.sleep(1.0)
            print 'Data download completed.'
            data = pool.get_url_data(url)
            self.__data = data
                
        if self.__data:
            n, filename = 1, urlobj.get_filename()
            origfilename = filename
            # Check if file exists, if so save to
            # filename.#n like wget.
            while os.path.isfile(filename):
                filename = ''.join((origfilename,'.',str(n)))
                n += 1
                
            res=self.__write_url(filename)
            if res:
                print '\nSaved to %s.' % filename
                return res
        else:
            print 'Download of URL',url ,'not completed.\n'

        return 0

    def get_data(self):
        return self.__data
    
    def get__error(self):
        """ Return last network error code """

        return self.__error

    def get_reader(self):
        """ Return reader thread """

        return self._reader
    
class HarvestManUrlConnectorFactory(object):
    """ This class acts as a factory for HarvestManUrlConnector
    objects. It also has methods to control the number of
    active connectors, and the number of simultaneous requests
    to the same server """

    def __init__(self, maxsize):
        # The requests dictionary
        self.__requests = {}
        # Semaphore object to control
        # active connections
        self.__sema = tg.BoundedSemaphore(maxsize)
        # tg.Condition object to control
        # number of simultaneous requests
        # to the same server.
        self.__reqlock = tg.Condition(tg.RLock())
        self._cfg = GetObject('config')
        
    def create_connector(self, server):
        """ Create a harvestman connector to
        the given server which can be used to download
        a url """
        
        # Acquire the semaphore. This will
        # reduce the semaphore internal count
        # so if the number of current connections
        # is exceeded, this call will block the
        # calling thread.
        self.__sema.acquire()
        # Even if the number of connections is
        # below the maximum, the number of requests
        # to the same server can exceed the maximum
        # count. So check for that condition. If
        # the number of current active requests to
        # the server is equal to the maximum allowd
        # this call will also block the calling
        # thread
        self.add_request(server)
        
        # Make a connector 
        connector = HarvestManUrlConnector()
        return connector
        
    def remove_connector(self, server):
        """ Remove a connector after use """

        # Release the semaphore once to increase
        # the internal count
        self.__sema.release()
        # Decrease the internal request count on
        # the server
        self.remove_request(server)
        
    def add_request(self, server):
        """ Increment internal request count
        to the server by one. Block if
        the number of current requests matches
        the maximum allowed. Uses a Condition
        object to manage threads """

        try:
            self.__reqlock.acquire()
            currval = self.__requests.get(server, 0)
            if currval >= self._cfg.requests:
                # Release lock and wait on condition
                self.__reqlock.wait()

            if currval < self._cfg.requests:
                self.__requests[server] = currval + 1
        finally:
            # Release lock
            self.__reqlock.release()
    
    def remove_request(self, server):
        """ Decrement internal request count by
        one. Wake up all waiting threads (waiting
        on the Condition object) """

        currval=0
        try:
            # Acquire lock 
            self.__reqlock.acquire()

            try:
                currval = self.__requests.get(server, 0)
                if currval:
                    self.__requests[server] = currval - 1
            except KeyError, e:
                debug(str(e))
                return None

            if currval == self._cfg.requests:
                # Wake up all threads waiting
                # on the condition
                self.__reqlock.notifyAll()

        finally:
            # Release lock          
            self.__reqlock.release()
        
# test code
if __name__=="__main__":

    conn = HarvestManUrlConnector()

    Initialize()
    # Note: this test works only for a client
    # directly connected to the internet. If
    # you are behind a proxy, add proxy code of
    # harvestManUrlConnectorUrl class here.

    # FIXME: I need to move this initialize to somewhere else!
    conn.initialize()
    conn.configure()

    # Check for http connections
    print 'Testing HTTP connections...'
    conn.url_to_file('http://www.python.org/index.html', 'python.org-index.html')
    # print the HTTP headers
    conn.print_http_headers()
    
    conn.url_to_file('http://www.rediff.com', 'rediff.com-index.html')
    # print the HTTP headers
    conn.print_http_headers()
    
    conn.url_to_file('http://www.j3d.org', 'j3d-org.index.html')
    # print the HTTP headers
    conn.print_http_headers()
    
    conn.url_to_file('http://www.yahoo.com', 'yahoo-com.index.html')
    # print the HTTP headers
    conn.print_http_headers()   

    # Check for ftp connections
    print 'Testing FTP connections...'  
    conn.url_to_file('ftp://ftp.gnu.org', 'ftp.gnu.org-index.html')

    # print the HTTP headers
    conn.print_http_headers()   

