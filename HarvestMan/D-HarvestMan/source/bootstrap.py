"""
Bootstrap a D-HarvestMan client in the machine.
This script will run as a service listening for
queries from the D-HarvestMan master at port
3600 in the system.

When someone connects to it, it asks for a
special key for ACK. If the key is correct, it
assumes that this program is the master. It then
creates a special session key and sends it to
the master.

Once the master acknowledges it, it sends an ACK
back to this script, with the same session key
and its host information. If the masters key matches
the key initially sent, the script bootstraps
a HarvestMan slave process and hands over the key
to it along with information to contact the master.

Then the service typically goes idle. After that
if it recieves query from another master it will say
that the host is already having a HarvestMan client
process running. 


Created Anand B Pillai 07/11/05
"""

import sys,os
import socket
import threading
import SocketServer
import ConfigParser
import md5
import signal

from constants import *
from common import *

class DHarvestManBootStrapService(object):
    """ A socket server which acts as a bootstrap
    service for D-HarvestMan """

    instance = None

    def set_instance(inst):
        DHarvestManBootStrapService.instance = inst
        print 'INSTANCE=',inst

    set_instance = staticmethod(set_instance)

    def get_instance():
        return DHarvestManBootStrapService.instance

    get_instance = staticmethod(get_instance)    
        
    def __init__(self, host='localhost',port=3600):
        self._host = host
        self._port = port
        # HarvestMan directory path
        self._hmandir = ''
        # TCP server
        self._server = None
        # Pyro version
        self._pyroversion = ''
        # Status of D-HarvestMan slave
        self._slave_status = SLAVE_NOT_RUNNING
        # Mgr protocol
        self._protocol = ''
        # Contact information for mgr
        # Typically, a two-tuple of the RPC (Pyro)
        # object name and hostip.
        self._mgrinfo = ()
        # Slave process id
        self._spid = -1
        
        # First check settings and initialize
        # things accordingly
        self._initialize()

    def _initialize(self):
        """ Initialization steps """

        # Read the config file located
        # at /etc/d-harvestman.conf
        self._read_config()
        # We will reach here if things
        # go well so far!

        # Check for Pyro installation
        # in Python.
        self._validate_python_runtime()
        # If we reach here, everything is fine...
        print 'All checks completed OK.'

    def _read_config(self):
        """ Read d-harvestman configuration
        files and set variables accordingly """

        
        # The file should be present in
        # /etc/d-harvestman.conf in the
        # ConfigParser format.
        if os.name == 'posix':
            confpath = '/etc/d-harvestman.conf'
        elif os.name == 'nt':
            confpath = 'C:/d-harvestman.conf'
            
        if not os.path.isfile(confpath):
            print 'Fatal Error: D-HarvestMan config file <%s> not found!' % confpath
            sys.exit(1)

        # Parse it
        parser = ConfigParser.ConfigParser()
        parser.readfp(open(confpath))
        # The config file right now has only one
        # section. This section shows the Path where
        # HarvestMan is installed. The section is
        # titled 'Paths'. The path's variable name
        # is 'HarvestMan'. It is the directory where
        # HarvestMan is installed.

        # Extract this path.
        if not 'Paths' in parser.sections():
            print 'Fatal Error: Could not find [Paths] section in %s' % confpath
            sys.exit(1)

        # Extract value for 'HarvestMan'
        self._hmandir = parser.get('Paths','HarvestMan')
        # Replace any trailing or beginning quote characters
        if self._hmandir[0] in ('"',"'"):
            self._hmandir = self._hmandir[1:]
        if self._hmandir[-1] in ('"',"'"):
            self._hmandir = self._hmandir[:-1]            
        
        print self._hmandir
        if not self._hmandir:
            print 'Fatal Error: Null value for [HarvestMan] variable'
            sys.exit(1)

        # Find out if this is valid
        if os.path.isdir(self._hmandir):
            print self._hmandir
            # See if it contains a file called 'harvestman.py'
            hmanfile = os.path.join(self._hmandir, 'harvestman.py')
            if os.path.isfile(hmanfile):
                print 'Detected HarvestMan module at %s' % hmanfile
                return 0

        print 'Fatal Error: Either HarvestMan directory or HarvestMan module not found!'
        sys.exit(1)

    def _validate_python_runtime(self):
        """ Validate the Python runtime. This right now
        checks for Pyro. Catch all exceptions right here
        and take necessary actions (no return values) """

        version = check_pyro()
        if version != -1:
            self._pyroversion = str(version)
            # Okay, now see if the version of Pyro
            # is on or above 3.4
            print 'Pyro version %s detected...' % version
            versioninfo = version.split('.')
            major = int(versioninfo[0])
            minor = int(versioninfo[1])
        
            if major >=3 and minor >=4:
                print 'Pyro installation validated.'
            else:
                print 'Pyro version should be at least 3.4!'
                print 'Current Pyro version is invalid.'
                sys.exit(1)

    def start_server(self):
        """ Start TCP server listening for incoming connections """

        print 'Starting D-HarvestMan boostrap service on %s:%s...' \
              % (self._host, str(self._port))
        self._server = SocketServer.ThreadingTCPServer((self._host, self._port),
                                                       DHarvestManServiceHandler)
        self._server.serve_forever()

    def get_hmanmodule(self):
        return os.path.join(self._hmandir, 'harvestman.py')
        

class DHarvestManServiceHandler(SocketServer.BaseRequestHandler):
    """ The Request handler class for DHarvestManBootStrapService """

    BUFSIZ = 8192

    def __init__(self, req, caddr, server):
        # Session key
        self._session_key = ''
        # Service handle
        self._handle = DHarvestManBootStrapService.get_instance()
        SocketServer.BaseRequestHandler.__init__(self, req, caddr, server)
        
    def handle(self):

        while True:
            data = self.request.recv(self.BUFSIZ)
            if not data: break
            print data

            # If this is a D-HarvestMan manager handshake
            # initiation, it will be a string in the following
            # format.

            # <KEY>:<PROTOCOL>
            # The key for D-HarvestMan is 'ADAPT'
            # The protocol is the protocol for communication
            # Right now this has to be 'PYRO'

            # The hand-shaking starts from now.
            if self._verify_mgr_handshake(data):
                print 'Starting D-HarvestMan manager hand-shake...'
                # Create a session key.
                self._session_key = self._create_session_key()
                # Send it to the client
                print 'Sending session key...'
                self.request.sendall(''.join(('KEY ',self._session_key)))
                print 'Done.'

            # This could be the mgr sending back the session key
            elif self._verify_mgr_session_key(data):
                print 'Verified manager identity.'
                # Request for command
                self.request.sendall('CMD REQUEST_COMMAND')
                data = self.request.recv(self.BUFSIZ)
                # These could be commands to manage the slave process
                cmd = self._parse_mgr_command(data)
                print 'COMMAND =>', cmd
                if cmd == 'START_SLAVE':
                    # Request for Pyro information
                    info = self._send_recv_command('SEND_CONTACTINFO')
                    # Parse it
                    self._parse_mgr_contact_info_cmd(info)
                    # Ping to see mgr if it is alive
                    # (This is a bit reduntant!)
                    print 'MGR INFO=>',self._mgrinfo
                    mgr_ip = self._mgrinfo[1]
                    if icmp_ping(mgr_ip):
                        # Request parameters for slave. The manager
                        # should return the slave's starting URL,
                        # the base-directory and a project name.
                        # The fetchlevel is set to 1 by default.
                        # Though we suppply that also...
                        data = self._send_recv_command('REQUEST_SLAVE_PARAMS')
                        # The data should be a string of the form
                        # "URL:<url>,BASEDIR:<basedir>,NAME:<name>,FETCHLEVEL:<fetchlevel>"
                        # Start D-HarverstMan slave process.
                        if self._start_slave_process(data):
                            # Send STATUS message...
                            self._send_status_msg('SLAVE_RUNNING')
                        else:
                            self._send_status_msg('SLAVE_NOT_RUNNING')
                            
                elif cmd == 'STOP_SLAVE':
                    # Stop the slave process
                    if self._stop_slave_process():
                        self._send_status_msg('SLAVE_STOPPED')
                    else:
                        self._send_status_msg('SLAVE_NOT_STOPPED')
                elif cmd == 'RESTART_SLAVE':
                    # Restart the slave process with a new URL
                    data = self._send_recv_command('REQUEST_URL')
                    if self._restart_slave_process(data):
                        # Send STATUS message...
                        self._send_status_msg('SLAVE_RESTARTED')                    
                    else:
                        self._send_status_msg('SLAVE_NOT_RESTARTED')                    
                
        self.request.close()

    def _send_recv_command(self, cmd):
        """ Send the cmd and recv data. Return
        the data recvd """

        data = ''.join(('CMD ',cmd))
        print 'Sending CMD =>', data
        self.request.sendall(data)
        data = self.request.recv(self.BUFSIZ)
        return data

    def _send_status_msg(self, msg):
        self.request.sendall(''.join(('STATUS ',msg)))
        
    def _parse_mgr_contact_info_cmd(self, data):
        """ Parse mgr contact information """

        # The data is of the following form
        # ACK CMD CONTACTINFO OBJNAME:HOSTIP

        print 'Data =>', data
        verify, info = self._verify_mgr_command_ack(data, 'SEND_CONTACTINFO')
        if verify and info:
            # Split it into two
            mgrinfo = info.split(':')
            setattr(self._handle, '_mgrinfo',mgrinfo)
            return True

    def _parse_mgr_command(self, data):
        """ Verifies a command sent by the manager,
        strips of the CMD part and returns just
        the command part """

        # Every command should include the session
        # key in the form "CMD <cmdstring>#<SESSIONKEY>"
        parts = data.split('#')
        print 'Parts=>', parts
        if len(parts)==2:
            if parts[1] == self._session_key:
                print 'Session key verified.'
                # Split again
                parts = parts[0].split()
                if parts[0]=='CMD':
                    return parts[1]
            else:
                print 'Session key not verified'
                return 'INVALID_COMMAND'

        return 'INVALID_COMMAND'
    
    def _verify_mgr_command_ack(self, data, cmd):
        """ Verifies the ack of a command by
        the manager, strips of the ACK part
        and returns only the string which contains
        the information """
        
        parts = data.split()
        print 'Parts=>', parts
        if len(parts)==4:
            # The first two strings have to be 'ACK CMD'
            if parts[0] == 'ACK' and parts[1] == 'CMD':
                # The next has to be the command itself
                if parts[2] == cmd:
                    # The last portion is the required info
                    return (True, parts[3])

        return (False, '')
        
    def _verify_mgr_handshake(self, data):
        """ Verify if this is a D-HarvestMan mgr handshake """

        parts = data.split()
        print parts

        if parts[0] == 'IDENTIFIER':
            key, protocol = parts[1].split(':')

            if key == 'ADAPT':
                self._protocol = protocol
                if protocol == 'PYRO':
                    return True
            

        return False
        

    def _create_session_key(self):
        """ Create a key for the current session
        with the mgr """

            
        m = md5.new()
        # The key is pretty simple. It consists
        # of the machine's I.P, a hash of it
        # and an md5 hash of the whole data.

        # i.e <i.p>:<timestamp>:<hash>
        try:
            ip = getipaddress()
            iphash = abs(hash(str(ip)))
            key = ''.join((str(ip),'_',str(iphash)))
            m = md5.new()
            m.update(key)
            mdhash = m.hexdigest()
            key = ''.join((key,':',str(mdhash)))

            return key
        except Exception, e:
            print e
            # Just return a simple key
            simple_key = 'D-HARVESTMAN'
            m.update(key)
            mdhash = m.hexdigest()        
            simple_key = ''.join((simple_key,':',str(mdhash)))
            return simple_key

    def _verify_mgr_session_key(self, data):
        """  Verify manager session key """

        if data:
            parts = data.split()
            if parts[0] == 'ACK':
                cmd, key =parts[1], parts[2]
                # Verify against session key
                if cmd == 'KEY' and key == self._session_key:
                    return True

        return False

    def _start_slave_process(self, data):
        """ Starts the slave process """

        # Check if slave already running
        if self._slave_status == SLAVE_RUNNING:
            print 'Error: Slave is already running on this machine'
            self.request.sendall('ERROR: Slave already running!')
            return False
        
        verify, info = self._verify_mgr_command_ack(data, 'REQUEST_SLAVE_PARAMS')
        if (not verify) or (not info):
            print 'Manager ack not verified'
            return False
        
        print 'Starting HarvestMan slave process...'
        # Start process, it needs to be supplied
        # the master proxy name, ip and protocol
        # It also needs to be given the fetchlevel
        # the base-dir, and a project name.
        parts = info.split(',')
        print 'PARTS=>',parts
        
        url,basedir,name,fetchlevel='','~/websites','',1
        print 'HERE'
        for part in parts:
            print 'PART IN LOOP=>',part
            idx = part.find(':')
            key, value = part[:idx].strip(), part[idx+1:]
            print 'KEY=>',key
            print 'VALUE=>',value
            
            if key == 'URL':
                url = str(value)
            elif key == 'BASEDIR':
                basedir = str(value)
            elif key == 'NAME':
                name = str(value)
            elif key == 'FETCHLEVEL':
                fetchlevel = str(value)

        print 'URL=>',url
        print 'PROJ=>',name
        print 'BASEDIR=>',basedir
        
        if url and basedir and name:
            print 'VALID!'
            hmanpath = self._handle.get_hmanmodule()
            print 'HMANPATH=>',hmanpath
            # Start it as a D-HarvestMan slave
            mgr_args = ''.join((self._mgrinfo[0],':',self._mgrinfo[1],':',self._protocol))
            print mgr_args
            if os.name == 'posix':
                cmd = 'python'
            elif os.name == 'nt':
                cmd = os.path.join(sys.prefix,'python.exe')
                
            args = [cmd,hmanpath,'-p',name,'-b',basedir,'-f',fetchlevel,'-l 0',
                    ''.join(('--slave=',mgr_args)),url]
            if os.name == 'posix':
                pid = os.spawnvpe(os.P_NOWAIT,cmd,args,os.environ)
            elif os.name == 'nt':
                pid = os.spawnv(os.P_NOWAIT,cmd,args)
                
            if pid:
                # Save the process id
                setattr(self._handle,'_spid',pid)
                setattr(self._handle,'_slave_status',SLAVE_RUNNING)
                print 'PROCESS ID=>',pid
                
                return True
        else:
            print 'Valid slave parameters not received'
            
        return False
        pass

    def _stop_slave_process(self):
        """ Stop the slave process """

        if self._slave_status != SLAVE_RUNNING:
            print 'Slave is not running'
            self.request.sendall('ERROR: Slave not running')
            return False

        # Kill the slave process
        try:
            os.kill(self._spid, signal.SIGKILL)
            self._spid = -1
            setattr(self._handle,'_slave_status',SLAVE_RUNNING)            
            return True
        except OSError, e:
            print e
            return False

        return False

    def _restart_slave_process(self):
        """ Restart the slave process """
        
        if self._slave_status != SLAVE_RUNNING:
            print 'Slave is not running'
            self.request.sendall('ERROR: Slave not running')            
            return False

        verify, info = self._verify_mgr_command_ack(data, 'REQUEST_URL')
        if (not verify) or (not info):
            print 'Manager ack not verified'
            return False

        idx = parts.find(':')
        key, value = part[:idx].strip(), part[idx+1:]
        if key == 'URL' and value:
            url = value
            # Kill the slave process
            if self._stop_slave_process()==0:
                # Restart it
                return self._start_slave_process(url)
        
        return False

    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            if hasattr(self._handle,name):
                return getattr(self._handle,name)
            
        
if __name__=="__main__":
    import sys
    
    b=DHarvestManBootStrapService(port=int(sys.argv[1]))
    DHarvestManBootStrapService.set_instance(b)
    b.start_server()
    


