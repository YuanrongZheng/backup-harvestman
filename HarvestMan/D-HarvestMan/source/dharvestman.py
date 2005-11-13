""" D-HarvestMan interface module. This module consists
of both the manager and slave interfaces in one.

Created - Anand B Pillai 12/11/05

"""
import harvestman
import Pyro.core
from Pyro.errors import PyroError, ProtocolError
from constants import *
from urlparser import HarvestManUrlParser
from common import *

import time
import os
import socket
import md5
import lrucache

class Manager(harvestman.harvestMan, Pyro.core.ObjBase):

    def __init__(self, pyroname='DHarvestMan'):
        self.USER_AGENT = "D-HarvestMan 1.4"
        # Pyro obj name
        self._pyroname = pyroname
        # Test code
        self.flag = False
        # List of running slaves
        self._slaves = []
        # Dictionary of session_keys
        # to slave ip mappings
        self._sessionkeys = {}
        # Dictionary of slave ip's
        # to slave status
        self._slavestatus = {}
        # Dictionary of slave ips
        # to crawl status
        self._crawlstatus = {}
        # Dictionary of slave ips
        # to slave ids
        self._slaveids = {}
        # Dictionary of slave ips
        # to their URLs
        self._slaveurls = {}
        # Cache of announced urls
        self._urlcache = lrucache.LRUCache(3000)
        Pyro.core.ObjBase.__init__(self)        
        pass

    def test_code(self):
        # Test code for Pyro.
        for x in range(1000):
            print 'Me =>',x
            if self.flag: break
            time.sleep(1.0)

        print 'FINISHED'

    def set_flag(self):
        # Test code for Pyro
        self.flag = True

    def slave_started(self, slave_ip):
        """ Callback called by slave crawlers when
        they startup and just before they start
        crawling """

        # Create an id for the slave and return it
        lastid = 1
        for value in self._slaveids.values():
            if value > lastid:
                lastid = value

        slaveid = lastid + 1

        self._slaveids[slave_ip] = slaveid
        return slaveid

    def crawl_started(self, slave_ip):
        """ Callback called after a slave is started """
        
        self._crawlstatus[slave_ip] = CRAWL_STARTED
        
    def crawl_finished(self, slave_ip):
        """ Callback called by slave after its
        crawl finishes """

        self._crawlstatus[slave_ip] = CRAWL_FINISHED

    def slave_stopped(self, slave_ip):
        """ Callback called  by a slave just before it is stopped """
        
        # The slave process currently dies after a crawl
        # is finished. So we are setting the next status
        # info. Ideally the slave should wait for some time
        # in a loop for new URLs before going down.
        # Once this change is made, uncomment the following
        # lines.
        self._slavestatus[slave_ip] = SLAVE_STOPPED
        self.remove_slave_info(slave_ip)

    def find_idle_slave(self):
        """ Return an idle slave """

        for ip,val in self._crawlstatus.items():
            if val == CRAWL_FINISHED:
                if self._slavestatus[ip] == SLAVE_RUNNING:
                    return ip

    def run_projects(self):
        """ Run the HarvestMan projects specified in the config file """
        
        # Prepare myself
        self._prepare()
        
        # Get program options
        self._cfg.get_program_options()

        # In D-HarvestMan, fetchlevel is always 1
        # i.e crawling only the current domain.
        self._cfg.fetchlevel = 1
        
        # Set locale - To fix errors with
        # regular expressions on non-english web
        # sites.
        self.set_locale()
        
        self.register_common_objects()
        
        # Welcome messages
        if self._cfg.verbosity:
            self.welcome_message()    
          
        print self._cfg.d_manager
        print self._cfg.d_maxdomains
        print self._cfg.d_ipmin, self._cfg.d_ipmax
        print self._cfg.d_slaves

        # In D-HarvestMan we will be crawling
        # only one project in a given session.
        self._cfg.url = self._cfg.urls[0]
        if not self._cfg.nocrawl:
            self._cfg.project = self._cfg.projects[0]
            self._cfg.verbosity = self._cfg.verbosities[0]
            self._cfg.projtimeout = self._cfg.projtimeouts[0]
            self._cfg.basedir = self._cfg.basedirs[0]

            self.run_project()
            # self.test_code()
            # status = self.start_slave('http://www.python.org/')
            # if status==1:
            #    print 'Slave is running...'
            # ip = self.find_slave_ip('http://www.python.org/doc/current/tut/tut.html')
            # print 'FOUND IP=>',ip
            # self.stop_slave(ip)
                
    # Callback funcs
    def url_found(self, url):
        """ A URL not belonging to the current domain of a slave
        is found """

        flag = False
        # First see if this url is there in my cache
        if url in self._urlcache:
            # Find status
            status = self._urlcache[url]
            # Status has the following values.
            # 1 => Announced and accepted by some slave
            # 2 => Announced, no slave was found, started
            #      a new slave for this domain.
            # 3 => Announced, a slave was found, but
            #      it did not accept it due to some error.
            # 4 => Announced, no slave was found, could not
            #      start a new crawler since we are at the
            #      limit.
            # 5 => Announced, no slave was found, could not
            #      start a new crawler due to some other error.
            if status==1 or status==2:
                print 'URL %s was accepted by a slave before' % url
                return '0:1'
            elif status==3 or status==4 or status==5:
                flag = True
        else:
            # Not there in cache
            flag = True

        # First see if any crawler is crawling this domain.
        ip = self.find_slave_ip(url)
        if ip:
            # Announce the new url to it
            status = self.send_url(ip, url)
            if status==1:
                print 'URL %s was accepted by slave %s' % (url, ip)
                self._urlcache[url] = 1
                return '1:1'
            else:
                print 'URL %s was not accepted by slave %s' % (url, ip)
                self._urlcache[url] = 3                
                return '0:3'                
        else:
            # See if any slave is idling
            ip = self.find_idle_slave()
            if ip:
                status = self.send_url(ip, url)
                if status==1:
                    print 'URL %s was accepted by slave %s' % (url, ip)
                    self._urlcache[url] = 1
                    return '1:1'

            # No slave is crawling this domain.
            # See if we can start a new slave
            print 'Number of running slaves =>',len(self._slaves)
            if len(self._slaves) < self._cfg.d_maxdomains:
                # Try starting a new slave with the new url
                status = self.start_slave(url)
                if status==1:
                    print 'Successfully started slave for url %s' % url
                    self._urlcache[url] = 2                                    
                    return '1:2'
                else:
                    print 'Failed to start slave for url %s' % url
                    self._urlcache[url] = 5
                    return '0:4'
            else:
                # We are at the limit
                print 'Reached limit of maximum number of crawlers, could not start a new one'
                self._urlcache[url] = 4                                                    
                return '0:2'
                
        pass

    def remove_slave_info(self, ip):
        """ Remove slave info from all state variables
        This could be called when a slave is removed from
        the cluster, such as when it is stopped.
        """

        try:
            self._slaves.remove(ip)
            del self._slaveids[ip]
            del self._slaveurls[ip]
            del self._sessionkeys[ip]
        except (ValueError, KeyError), e:
            print e
        
    def _verify_hash(self, key, hashval):
        """ Verify md5 hash for the given key """

        m = md5.new()
        m.update(key)
        digest = str(m.hexdigest())
        if digest == hashval:
            return True

        return False

    def _establish_connection(self, ip):
        """ Establish a TCP connection with the ip and
        return the socket object """
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, int(self._cfg.d_serviceport)))
            # Send IDENTIFIER
            sock.send('IDENTIFIER ADAPT:PYRO')
            data = sock.recv(1024)
            print data
            cmd, key = data.split()
            print 'Key=>',key
            key2, hashval = key.split(':')
            # Verify hash
            if self._verify_hash(key2, hashval):
                print 'Sesson key verified and saved...'
                # Save session key
                self._sessionkeys[ip] = key
                data = ''.join(('ACK ',data))
                sock.send(data)
                data = sock.recv(1024)
                # This should be a message requesting
                # command
                cmd, key = data.split()
                if cmd == 'CMD' and key == 'REQUEST_COMMAND':
                    print 'Service ready to accept commands.'
                    return sock
        except socket.error, e:
            print e
            
    def _boostrap_slave(self, ip, url):
        """ Bootstrap a slave with the given URL """        

        try:
            sock = self._establish_connection(ip)
            sock.sendall(self._make_command_string('START_SLAVE',ip))
            data = sock.recv(1024)
            print data 
            cmd, key = data.split()
            if key=='SEND_CONTACTINFO':
                myip = str(getipaddress())
                sock.send('ACK CMD %s %s:%s' % (key, self._pyroname, myip))

            data = sock.recv(1024)
            cmd, key = data.split()

            if cmd == 'CMD' and key == 'REQUEST_SLAVE_PARAMS':
                # Create a project name from url
                # Project name is 'project_' plus hash of the url
                name = ''.join(('project_',str(abs(hash(url)))))
                basedir = '~/websites'
                fetchlevel = 1
                data = ''.join(('ACK CMD ',key,' ',
                                ''.join(('URL:'+url,
                                         ',BASEDIR:'+basedir,
                                         ',NAME:'+name,
                                         ',FETCHLEVEL:'+str(fetchlevel)))))
                sock.send(data)

            data = sock.recv(1024)
            cmd, key = data.split()                        

            if cmd == 'STATUS':
                if key == 'SLAVE_RUNNING':
                    # Set status
                    self._slavestatus[ip] = SLAVE_RUNNING
                    return True
                else:
                    return False
            else:
                print 'Hash of session key not verified, closing connection...!'
                sock.close()
                return False
            
            sock.close()
        except socket.error, e:
            print e
            
        return False


    def find_slave_ip(self, url):
        """ Find the slave who could be crawling the domain
        belonging to the given url """

        # Find the domain of this url
        h = HarvestManUrlParser(url)
        domain = h.get_domain()
        return self.find_slave_ip2(domain)

    def find_slave_ip2(self, domain):
        """ Find the slave who could be crawling the domain
        belonging to the given domain """        

        for ip, urlobj in self._slaveurls.items():
            url_domain = urlobj.get_domain()
            if domain == url_domain:
                return ip

    def _make_command_string(self, cmd, ip):
        """ Create a command string for communicating
        with the DHarvestMan service """

        # The command string is of the following form
        # 'CMD <cmdstring>#<SESSIONKEY>
        cmdstring = ''.join(('CMD ',cmd,'#',self._sessionkeys[ip]))
        return cmdstring

    def send_url(self, ip, url):
        """ Send a new URL to an existing slave """

        # Need to do this, for the time being it
        # always returns 1
        return 1
    
    def stop_slave(self, ip):
        """ Stop the slave with the given ip """

        status = self._slavestatus.get(ip, SLAVE_STATUS_UNKNOWN)
        if status == SLAVE_RUNNING:
            try:
                sock = self._establish_connection(ip)
                print 'BEFORE MAKING COMMAND STRING'
                cmd = self._make_command_string('STOP_SLAVE',ip)
                sock.send(cmd)
                data = sock.recv(1024)
                print 'DATA=>',data
                # Check for status
                key, msg = data.split()
                if key == 'STATUS':
                    if msg == 'SLAVE_STOPPED':
                        self._slavestatus[ip] = SLAVE_STOPPED
                        self.remove_slave_info(ip)
                        print 'Slave successfully stopped.'
                        return 1
                    else:
                        print 'Error stopping slave.'
            except socket.error, e:
                print e
        else:
            print 'Slave is not running!'
                
        return 0
                
    def start_slave(self, url):
        """ Start a slave with the given URL """

        # First the slaves list is examined. Then the ip range
        slave_list = self._cfg.d_slaves
        # Boostrap status
        # 0 => not successful
        # 1 => successful
        
        status = 0
        if slave_list:
            for ip in slave_list:
                if ip not in self._slaves:
                    print 'IP=>',ip
                    if self._boostrap_slave(ip, url):
                        status=1
                        self._slaves.append(ip)
                        self._slaveurls[ip] = HarvestManUrlParser(url)                        
                        break

        # Not successful, try I.P range
        if not status:
            ip_min = self._cfg.d_ipmin
            ip_max = self._cfg.d_ipmax

            if ip_min and ip_max:
                min_val = int(ip_min.split('.')[-1])
                max_val = int(ip_max.split('.')[-1])

                ip_rest = ip_min[:ip_min.rfind('.')]

                for x in range(min_val, max_val+1):
                    ip = ''.join((ip_rest,'.',str(x)))
                    if not ip in self._slaves:
                        print 'IP=>',ip
                        if self._boostrap_slave(ip, url):
                            status=1
                            self._slaves.append(ip)
                            self._slaveurls[ip] = HarvestManUrlParser(url)
                            break
                        
        return status
    
                        
class RemoteManager(object):

    def __init__(self,name='DHarvestMan'):
        self._daemon = None
        self._uri = ''
        self._name = name
        self._mgr = Manager(name)
        pass

    def _bootstrap(self):
        cmd = 'python'
        args = [cmd,'startmgr.py',self._name]
        os.spawnvp(os.P_NOWAIT, cmd, args)
        
    def StartManager(self):
        Pyro.core.initServer()
        self._daemon=Pyro.core.Daemon()
        
        self._uri = self._daemon.connect(self._mgr,self._name)
        
        print "The daemon runs on port:", self._daemon.port
        print "The object's uri is:", self._uri

        self._bootstrap()
        self._daemon.requestLoop()    
        print 'HI'

if __name__=="__main__":
    o = RemoteManager()
    o.StartManager()
