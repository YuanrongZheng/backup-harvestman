# -- coding: iso8859-1
"""
HarvestManCookie.py - Module to implement a basic
CookieManager for HarvestMan. This file is part of the
HarvestMan program.

Description
===========

Manages Cookie Persistance for a domain from User Agent Perspective
Targets RFC 2109. (Very early stages of development)


Author : Nirmal C <nkchidambaram at yahoo dot com>

License
=======
Refer LICENSE.txt file for details.

Copyright
=========

Copyright (C) 2003-2004  Nirmal K Chidambaram & Anand Pillai 

History
======

Anand Sep 02 2003 Mod       Added error checks for anydbm file opening.
                            Added error checks for dbm variable.
                            Added some util functions. Added a test
                            using our connector.
Sep 04 2003        Anand    1.2alpha release.
Jan  2 2004        Anand    1.4 bug fix version development started.
Feb  11 2004       Anand    Fixed a bug with cookie manager (spelling
                            mistake in function name). There is no bug
                            id for this.

Jun 14 2004         Anand          1.3.9 release.                            
                            
TODO
====
We need to replace HTTPRedirectHandler of urllib2 with our own
and add it using OpenerDirector for full RFC 2109 compliance.

"""

from Cookie import SimpleCookie
from Cookie import CookieError
import Cookie
import shelve
import cPickle
import re

from threading import Lock, Condition
from urllib2 import Request

from common import *

class CookieManager(object):
    """ Acts as a CookieManager for a domain , stores retrieves cookies """

    def __init__(self, cookiestore=None):
        self.__internal_cookie = SimpleCookie()

        if cookiestore is None:
            self.__cookiestore = DBMCookieStore('harvestman_cookies.dat')
        else:
            self.__cookiestore = cookiestore

        self._netscape_domain = False
        self.domain_re = re.compile(r"[^.]*")
        self.ipv4_re = re.compile(r"\.\d+$")

    def startswith(str , initial):
        if len(initial) > len(str): return 0
        return string[:len(initial)] == initial

    def __validate_rules_rfc2109(self,temp_cookie,reqhost):
        """ Validates Rules for Cookie as per RFC 2109 """

        try:

            for key in temp_cookie.keys():
                morsel = temp_cookie[key]

                mor = morsel['domain']
                if mor=='':
                    continue
                
                # Rule 1: Validate Domain , if Domain has problems reject cookie
                if  not (mor[0] != '.') or (mor[1:len(mor)-1].find('.')!= -1):
                    del temp_cookie[key]

            # If contains at least one Morsel , return it else return none
            if  len(temp_cookie):
                return temp_cookie
            else:
                return None

        except CookieError:
            print 'Cookie Parsing Error'

    def __validate_rules_rfc2965(self,temp_cookie,reqhost):
        """ Validate rules for cookie as per RFC 2965 """

        # TODO
        pass

    def close_session(self):
        self.__cookiestore.close()

    def set_cookie(self,header,reqhost):
        """ Pushes Cookie to datastore after validating all rules """

        temp_cookie = Cookie.SimpleCookie()

        # We need to take care of lower case strings too
        for k in header.keys():
            if k.lower() == 'set-cookie':
                temp_cookie.load(header[k])
                validate_rules = self.__validate_rules_rfc2109
            elif k.lower() == 'set-cookie2':
                temp_cookie.load(header[k])
                validate_rules = self.__validate_rules_rfc2965

        if validate_rules(temp_cookie,reqhost):
            return self.__push_to_data_store(validate_rules(temp_cookie,reqhost),reqhost)
        else:
            return 0

    def __push_to_data_store(self,cookie,reqhost):
        """ Pushes cookies to data store """

        return  self.__cookiestore.store(cookie,reqhost)

    def get_next_domain(self, domain):
        """ Return a domain from passed domain, by stripping
        of leading characters before a dot """

        # Added anand 02 Sep 2003
        # The domain string must contain at least one dot.
        # Egs: a.b.c.net => .b.c.net => b.c.net => .c.net

        # !!DONT USE => NOT WORKING !!
        if self.startswith(domain, "."):
            domain = domain[1:]
            self._netscape_domain = True
        else:
            domain = self.domain_re.sub("", domain, 1)
            self._netscape_domain = False

        return domain

    def add_cookie_header(self, request, domain):
        """ Add cookie headers to a request """

        # Added Anand Sep 02 2003
        cookies=self.get_cookie(domain)
        if cookies is None: return
        
        for c in cookies:
            request.add_header("Cookie", c.output(header="Cookie:"))

    def get_cookie(self, reqhost):
        """ Retrieves Cookie from data store of Cookie Manager """

        lst =  self.__cookiestore.retrieve(reqhost)
        return self.__apply_retr_rules(lst, reqhost)

    def __apply_retr_rules(self,lst,reqhost):
        """ Apply all retrieval rules - TODO """

        return lst

class AbstractCookieStore:
    """ This class poses as an abstract Cookie store """

    def __init__(self):
        self.__dict__={}

    def __parse_domain_from_reqhost(self,reqhost):
        """ Parses reqhost and gets domain out of it as per RFC 2109 """

        if reqhost.find('http://') == 0:
            reqhost = reqhost[7:]
        if reqhost.find('www') == 0:
            reqhost = reqhost[4:]
        if (reqhost.rfind('/') != -1):
            reqhost = reqhost[:reqhost.rfind('/')]
        return reqhost

    def __get__domain_key(self,cookie,reqhost):
        """ Gets domain, path from cookie , adds up and returns """

        domain = self.__parse_domain_from_reqhost(reqhost)        
        path = '/'

        # checks if there is domain and path settings for cookie
        for key in cookie.keys():
            if cookie[key].has_key('domain'):
                domain = cookie[key]['domain'][1:]
            if cookie[key].has_key('path'):
                path = cookie[key]['path']
            break

        return domain+path      


    def get_hash_to_store(self,cookie,reqhost):
        """ Get the hash value for storage of the cookie """

        # Push to DBM Picked Cookie , keyed by  domain + path
        # Iterate oever cookie and get Morsels , Consider each Morsel as a seperate
        # Cookie and call __get__domain_key Function ,
        # store Morsel aka Cookie in Hash with that key 

        hash_store = {}

        for ckey in cookie.keys():
            new_cook = Cookie.SimpleCookie()
            new_cook.load(cookie[ckey].output())
            key = self.__get__domain_key(new_cook,reqhost)

            if hash_store.has_key(key):
                to_be_added = Cookie.SimpleCookie()
                pickled = cPickle.loads(hash_store[key])
                to_be_added.load(new_cook.output() + ',' + pickled.output())
                hash_store[key] = cPickle.dumps(to_be_added)               
            else:
                hash_store[key] = cPickle.dumps(new_cook)

        return hash_store

    def retrieve_domains(self, reqpath):

        lst = []
        if reqpath.find('http://') == 0:
            reqpath = reqpath[7:]
        if reqpath.find('www') == 0:
            reqpath = reqpath[4:]

        # if uri just points to a domian
        if reqpath.find('/') == -1:
            lst.append(reqpath+'/')

        curpath = -5

        while(curpath != -1):
            if curpath != -5:
                curpath = reqpath.find('/',curpath+1)              
            else:
                curpath = reqpath.find('/',0)               

            if(curpath != -1):
                lst.append(reqpath[:curpath+1])                

            return lst

class DBMCookieStore(AbstractCookieStore):
    """ Persistance for cookies using shelve. (This class is thread safe) """

    def __init__(self,filename):
        """ Initialize """

        self.__filename = filename
        self.__open_data_store()
        self.lck = Condition(Lock())

    def __open_data_store(self):
        """ Open the dbm for writing """

        # Added error checks - Anand
        import os
        
        self.db=None
        
        try:
            if os.path.exists(self.__filename):
                # if the filesize is zero, remove it
                # otherwise dbm cribs.
                st=os.stat(self.__filename)
                if st.st_size==0:
                    try:
                        os.chmod(self.__filename, 0777)
                        os.remove(self.__filename)
                    except OSError, e:
                        print e

            if not os.path.exists(self.__filename):
                # creat if does not exist
                self.db = shelve.open(self.__filename, 'c')
            else:
                # otherwise open for read/write
                self.db = shelve.open(self.__filename, 'w')
                
        except Exception, e:
            debug('Error opening DBM =>', e)

    def store(self,cookie,reqhost):
        """ Store a cookie in the database """

        if self.db is None: return -1
        
        debug('Storing cookie ', cookie)
        # Other Implementors *should* call Baseclass
        # store to get dictionary to store
        # Only one base class anyway :)
        for base in self.__class__.__bases__:
            hash_store = base.get_hash_to_store(self,cookie,reqhost)

        try:
            self.lck.acquire()
            # Store this hash_store to dbm
            for key in hash_store.keys():
                self.db[key] = hash_store[key]
        finally:
            self.lck.release()

        return 1

    def close(self):
        """ Close the database """

        if self.db is None: return -1
        
        try:
            self.lck.acquire()
            self.db.close()
            self.db=None
        except Exception, e:
            print 'Error closing DBM => ', e
        else:
            self.lck.release()

    def retrieve(self,reqpath):
        """ Retrieve cookies from the cookie store """

        if self.db is None: return None
        
        for base in self.__class__.__bases__:
            domains = base.retrieve_domains(self,reqpath)

        cookies = []

        self.lck.acquire()

        for key in domains:
            try:
                if self.db.has_key(key):
                    cookies.append(cPickle.loads(self.db[key]))
            except Exception, e:
                print e

        self.lck.release()
        return cookies

# Test cases
def test():
    # Test code deleted - Dec 15 2004
    print 'Not implemented!'

if __name__ == "__main__":
    test()


