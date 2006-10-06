# -- coding: latin-1
""" HarvestManConfig.py - Module to keep configuration options
    for HarvestMan program and its related modules. This software is
    part of the HarvestMan program.

    Author: Anand B Pillai.

    For licensing information see the file LICENSE.txt that
    is included in this distribution.

    Jan 2 2004        Anand   1.3.1 bug fix version.
    Feb 12 2004       Anand   1.3.2 version
                              development started.
    May 28 2004       Anand   1.4 version development. Derived
                              HarvestManStateObject from dict type.
                              (Note that this limits the program to
                              Python 2.2 and later versions.)
    Jun 14 2004       Anand   1.3.9 release.
    Sep 20 2004       Anand   1.4 development. Added system.locale
                              property to fix bug #B1095681194.6 .

    Sep 22 2004       Anand   1.4 development. Added a config property
                              for controlling download by time limit.

                              Performance fix - Set the default tracker
                              size to three.
    Oct 25 2004      Anand    Added config variables for urlserver.                              
    Jan 01 2006      jkleven  Change "skipqueryforms" to "getqueryforms" 
                              So in config file <forms value="0"/> meaning
                              is consistent with other types like 
                              images=1 and html=1
    Jan 10 2006      Anand    Converted from dos to unix format (removed
                              Ctrl-Ms).
"""

PROG_HELP = """\

%(appname)s %(version)s %(maturity)s: A multithreaded web crawler.

Usage: %(appname)s [options] URL

%(appname)s has two modes of working in the command-line.

In the default mode, %(appname)s works like a crawler. If you
pass one of the -N or --nocrawl options, %(appname)s only downloads
the url and saves it to the disk, similar to wget.

options:

    -h, --help:                 Show this message and exit
    -v, --version               Print version information and exit

    -p, --project=PROJECT       Set the (optional) project name to PROJECT. 
    -b, --basedir=BASEDIR       Set the (optional) base directory to BASEDIR.
    
    -C, --configfile=CFGFILE    Read all options from the configuration file CFGFILE.
    -P, --projectfile=PROJFILE  Load the project file PROJFILE.
    -V, --verbosity=LEVEL       Set the verbosity level to LEVEL. Ranges from 0-5.

    -f, --fetchlevel=LEVEL      Set the fetch-level of this project to LEVEL. Ranges
                                from 0-4.
    -N, --nocrawl               Only download the passed url (wget-like behaviour).
    
    -l, --localize=yes/no       Localize urls after download.
    -r, --retry=NUM             Set the number of retry attempts for failed urls to NUM.
    -Y, --proxy=PROXYSERVER     Enable and set proxy to PROXYSERVER (host:port).
    -U, --proxyuser=USERNAME    Set username for proxy server to USERNAME.
    -W, --proxypass=PASSWORD    Set password for proxy server to PASSWORD.
    -n, --connections=NUM       Limit number of simultaneous network connections to NUM.
    -c, --cache=yes/no          Enable/disable caching of downloaded files. If enabled,
                                files won't be downloaded unless their timestamp is
                                newer than the cache timestamp.
    
    -d, --depth=DEPTH           Set the limit on the depth of urls to DEPTH.
    -w, --workers=NUM           Enable worker threads and set the number of worker
                                threads to NUM. 
    -T, --maxthreads=NUM        Limit the number of tracker threads to NUM.
    -M, --maxfiles=NUM          Limit the number of files downloaded to NUM.
    -t, --timelimit=TIME        Run the program for the specified time TIME.

    -s, --urlserver=yes/no      Enable/disable urlserver running on port 3081.
    -S, --subdomain=yes/no      Enable/disable subdomain setting. If this is
                                enabled, servers with the same base server name
                                such as http://img.foo.com and http://pager.foo.com
                                will be considered as distinct servers. 
    
    -R, --robots=yes/no         Enable/disable Robot Exclusion Protocol.
    -u, --urlfilter=FILTER      Use regular expression FILTER for filtering urls.

    --urlslist=FILE             Dump a list of urls to file FILE.
    --urltree=FILE              Dump a file containing hierarchy of urls to FILE.

Mail bug reports and suggestions to <abpillai@gmail.com>.
"""

import os, sys
import getopt

from common import *

class HarvestManStateObject(dict):
    """ Internal config class for the program """

    def __init__(self):
        """ Initialize dictionary with the most common
        settings and their values """

        self._init1()
        self._init2()
        self._init3()

    def _init1(self):
        
        self.version='1.5'
        self.maturity="beta 1"
        self.appname='HarvestMan'
        self.progname="".join((self.appname," ",self.version," ",self.maturity))
        self.url=''
        # New var in 1.4.5 to store multiple starting urls
        self.urls = []
        self.project=''
        # New var in 1.4.5 to store multiple starting project names
        self.projects = []
        # New var in 1.4.1 to indicate combining of projects        
        self.combine = False
        self.basedir=''
        # New var in 1.4.5 to store multiple base dirs        
        self.basedirs = []
        # New var in 1.4.5 to store multiple verbosities
        self.verbosities=[]
        # New var in 1.4.5 to store multiple timeouts
        self.projtimeouts = []
        # New var in 1.4.5 to map urls to project names, basedirs & other project
        # related vars.
        self.urlmap = {}
        # New in 1.4.5 for archiving
        # downloaded files.
        self.archive = 0
        # Format for storing archives
        # Supported - bz2,gz.
        self.archformat = 'bzip'
        # New in 1.4.5 for storing
        # url headers
        self.urlheaders = 0
        # Format for storing url headers
        # Supported - dbm (shelve)
        self.urlheadersformat = 'dbm'
        self.configfile = 'config.xml'
        self.projectfile = ''         
        self.proxy=''
        self.puser=''
        self.ppasswd=''
        self.proxyenc=True
        self.siteusername=''   
        self.sitepasswd=''     
        self.proxyport=0
        self.errorfile='errors.log'
        self.localise=2
        self.jitlocalise=0
        self.images=1
        self.depth=10
        self.html=1
        self.robots=1
        self.eserverlinks=0
        self.epagelinks=1
        self.fastmode=1
        self.usethreads=1
        self.maxfiles=5000
        self.maxextservers=0
        self.maxextdirs=0
        self.retryfailed=1
        self.extdepth=0
        self.maxtrackers=4
        self.urlfilter=''
        self.wordfilter=''
        self.inclfilter=[]
        self.exclfilter=[]
        self.allfilters=[]
        self.serverfilter=''
        self.serverinclfilter=[]
        self.serverexclfilter=[]
        self.allserverfilters=[]
        self.urlpriority = ''
        self.serverpriority = ''
        self.urlprioritydict = {}
        self.serverprioritydict = {}
        self.verbosity=2
        self.timeout=240
        self.fetchertimeout=self.timeout
        self.getimagelinks=1
        self.getstylesheets=1
        self.threadpoolsize=10
        self.renamefiles=0
        self.fetchlevel=0
        self.browsepage=0
        self.htmlparser=0
        self.checkfiles=1
        self.cookies=1
        self.pagecache=1
        # New internal flag - Added Jan 8 2006
        self.cachefound=0
        self._error=''
        self.starttime=0
        self.endtime=0
        self.javascript = True
        self.javaapplet = True
        self.connections=5
        # Values => 'pickled' or 'dbm'        
        self.cachefileformat='pickled' 
        # 1. Testing the code (no browse page)
        self.testing = False 
        # 2. Testing the browse page (no crawl)
        self.testnocrawl = False
        self.nocrawl = False
        self.ignorekbinterrupt = False
        self.subdomain = False
        self.getqueryforms = False
        self.requests = 5
        self.bytes = 20.00 # Not used!
        self.projtimeout = 300 
        self.downloadtime = 0.0
        self.locale = 'C'
        self.defaultlocale = 'C'
        self.timelimit = -1
        self.terminate = False
        self.datacache = True
        self.urlserver = False
        self.urlhost = 'localhost'
        self.urlport = 3081
        self.urlserver_protocol='tcp'
        self.blocking = False
        self.junkfilter = True
        # Junk filter domain specific flag, not used
        self.junkfilterdomains = True
        # Junk filter patterns specific flag, not used
        self.junkfilterpatterns = True
        self.urltreefile = ''
        self.urllistfile = ''
        # Maximum file size is 1MB
        self.maxfilesize=1048576
        # Minimum file size is 0 bytes
        self.minfilesize=0
        # config file format
        self.format = 'xml'
        # 1.4.5 b1 - Option to
        # not create directories
        # for urls
        self.rawsave = False
        # 1.4.5 final - To indicate
        # that the configuration was
        # read from a project file
        self.fromprojfile = False
        
    def _init2(self):
        
        # create the dictionary of mappings containing
        # config options to dictionary keys and their
        # types

        # The dictionary containing the mapping
        # of config options to dictionary keys and their types
        self._options = {
                            'project.url' : ('url', 'str'),
                            'project.name' : ('project', 'str'),
                            'project.urls' : ('urls', 'list'),
                            'project.names' : ('projects', 'list'),
                            'project.basedir' : ('basedir', 'str'),
                            'project.verbosity' : ('verbosity', 'int'),
                            'project.timeout' : ('projtimeout', 'float'),

                            'network.proxyserver' : ('proxy', 'str'),
                            'network.proxyuser' : ('puser', 'str'),
                            'network.proxypasswd' : ('ppasswd', 'str'),
                            'network.proxyport' : ('proxyport', 'int'), 
                            'network.urlserver' : ('urlserver','int'),
                            'network.urlport'   : ('urlport', 'int'),
                            'network.urlhost'   : ('urlhost', 'str'),

                            'download.javascript'   : ('javascript', 'int'),
                            'download.javaapplet'   : ('javaapplet', 'int'),
                            'download.rename' : ('renamefiles', 'int'),
                            'download.cookies' : ('cookies', 'int'),
                            'download.retries' : ('retryfailed', 'int'),
                            'download.html': ('html', 'int'),
                            'download.images' : ('images', 'int'),
                            'download.forms' : ('getqueryforms', 'int'),
                            'download.cache' : ('pagecache', 'int'),
                            'download.datacache' : ('datacache', 'int'),

                            'control.stylesheetlinks' : ('getstylesheets', 'int'),
                            'control.imagelinks' : ('getimagelinks', 'int'),

                            'control.fetchlevel' : ('fetchlevel', 'int'),
                            'control.extpagelinks' : ('epagelinks', 'int'),
                            'control.extserverlinks' : ('eserverlinks', 'int'),
                            'control.depth' : ('depth', 'int'),
                            'control.extdepth' : ('extdepth', 'int'),
                            'control.subdomain'   : ('subdomain', 'int'),
                            'control.maxextdirs' : ('maxextdirs', 'int'),
                            'control.maxextservers' : ('maxextservers', 'int'),
                            'control.maxfiles'      : ('maxfiles', 'int'),
                            'control.maxfilesize'   : ('maxfilesize', 'int'),
                            'control.connections' : ('connections', 'int'),
                            'control.requests'    : ('requests', 'int'),
                            'control.timelimit'   : ('timelimit', 'int'),
                            
                            'control.robots' : ('robots', 'int'),
                            'control.urlpriority' : ('urlpriority', 'str'),
                            'control.serverpriority' : ('serverpriority', 'str'),
                            'control.urlprioritydict' : ('urlprioritydict', 'dict'),
                            'control.serverprioritydict' : ('serverprioritydict', 'dict'),
                            
                            'control.urlfilter' : ('urlfilter', 'str'),
                            'control.serverfilter' : ('serverfiler', 'str'),
                            'control.wordfilter' : ('wordfilter', 'str'),
                            'control.urlfilterre' : (('inclfilter', 'list'), ('exclfilter', 'list'),
                                                   ('allfilters', 'list')),
                            'control.serverfilterre' : (('serverinclfilter', 'list'),
                                                      ('serverexclfilter', 'list'),
                                                      ('allserverfilters', 'list')),

                            'control.junkfilter'  : ('junkfilter', 'int'),

                            'system.trackers' : ('maxtrackers', 'int'),
                            'system.threadtimeout' : ('timeout', 'float'),
                            'system.locale': ('locale', 'str'),   
                            'system.workers' : ('usethreads', 'int'),
                            'system.threadpoolsize' : ('threadpoolsize', 'int'),
                            'system.fastmode' : ('fastmode', 'int'),

                            'indexer.localise' : ('localise', 'int'),

                            'files.configfile' : ('configfile', 'str'),   
                            'files.projectfile' : ('projectfile', 'str'), 
                            'files.urllistfile' : ('urllistfile', 'str'),
                            'files.urltreefile'  : ('urltreefile', 'str'),
                            'files.archive'      : ('archive', 'int'),
                            'files.archformat'   : ('archformat', 'str'),
                            'files.urlheaders'   : ('urlheaders', 'int'),
                            'files.urlheaderformat' : ('urlheadersformat', 'str'),

                            'display.browsepage' : ('browsepage', 'int'),
                            'nocrawl'            : ('nocrawl', 'int')

                          }

    def _init3(self):
        
        # For mapping xml entities to config entities
        
        self.xml_map = { 'projects_combine' : ('combine', 'int'),
                         'project_skip' : ('skip', 'int'),
                         'url' : [('url', 'str'), ('urls','list:str')],
                         'name': [('project', 'str'), ('projects','list:str')],
                         'basedir' : [('basedir','str'), ('basedirs', 'list:str')],
                         'verbosity_value' : [('verbosity','int'), ('verbosities','list:int')],
                         'timeout_value' : [('projtimeout','float'),('projtimeouts','list:float')],

                         'proxyserver': ('proxy','str'),
                         'proxyuser': ('puser','str'),
                         'proxypasswd' : ('ppasswd','str'),
                         'proxyport_value' : ('proxyport','int'),

                         'urlserver_status' : ('urlserver','int'),
                         'urlhost' : ('urlhost','str'),
                         'urlport_value' : ('urlport','int'),

                         'html_value' : ('html','int'),
                         'images_value' : ('images','int'),
                         'javascript_value' : ('javascript','int'),
                         'javaapplet_value' : ('javaapplet','int'),
                         'forms_value' : ('getqueryforms','int'),

                         'cache_status' : ('pagecache','int'),
                         'datacache_value' : ('datacache','int'),

                         'urllistfile' : ('urllistfile', 'str'),
                         'urltreefile' : ('urltreefile', 'str'),
                         'archive_status' : ('archive', 'int'),
                         'archive_format' : ('archformat', 'str'),
                         'urlheaders_status' : ('urlheaders', 'int'),
                         'urlheaders_format': ('urlheadersformat', 'str'),
                         
                         'retries_value': ('retryfailed','int'),
                         'imagelinks_value' : ('getimagelinks','int'),
                         'stylesheetlinks_value' : ('getstylesheets','int'),
                         'fetchlevel_value' : ('fetchlevel','int'),
                         'extserverlinks_value' : ('eserverlinks','int'),
                         'extpagelinks_value' : ('epagelinks','int'),
                         'depth_value' : ('depth','int'),
                         'extdepth_value' : ('extdepth','int'),
                         'subdomain_value' : ('subdomain','int'),
                         'maxextservers_value' : ('maxextservers','int'),
                         'maxextdirs_value' : ('maxextdirs','int'),
                         'maxfiles_value' : ('maxfiles','int'),
                         'maxfilesize_value' : ('maxfilesize','int'),
                         'connections_value' : ('connections','int'),
                         'requests_value' : ('requests','int'),
                         'robots_value' : ('robots','int'),
                         'timelimit_value' : ('timelimit','int'),
                         'urlpriority' : ('urlpriority','str'),
                         'serverpriority' : ('serverpriority','str'),
                         'urlfilter': ('urlfilter','str'),
                         'serverfilter' : ('serverfilter','str'),
                         'wordfilter' : ('wordfilter','str'),
                         'junkfilter_value' : ('junkfilter','int'),
                         'workers_status' : ('usethreads','int'),
                         'workers_size' : ('threadpoolsize','int'),
                         'workers_timeout' : ('timeout','float'),
                         'trackers_value' : ('maxtrackers','int'),
                         'locale' : ('locale','str'),
                         'fastmode_value': ('fastmode','int'),
                         'localise_value' : ('localise','int'),
                         'browsepage_value' : ('browsepage','int'),
                         }

    def assign_option(self, option_val, value):
        """ Assign values to internal variables
        using the option specified """

        # Currently this is used only to parse
        # xml config files.
        if len(option_val) == 2:
            key, typ = option_val
            # If type is not a list, the
            # action is simple assignment

            # Bug fix: If someone has set the
            # value to 'True'/'False' instead of
            # 1/0, convert to bool type first.
            
            if type(value) in (str, unicode):
                if value.lower() == 'true':
                    value = 1
                elif value.lower() == 'false':
                    value = 0

            if typ.find('list') == -1:
                # do any type casting of the option
                fval = (eval(typ))(value)
                self[key] = fval
                
                # If type is list, the action is
                # appending, after doing any type
                # casting of the actual value
            else:
                # Type is of the form list:<actual type>
                typ = (typ.split(':'))[1]
                fval = (eval(typ))(value)
                var = self[key]
                var.append(fval)

            #print 'Option set for %s %s' % (option_val, value)
        else:
            debug('Error in option value %s!' % option_val)
            
    def set_option_xml(self, option, value):
        """ Set an option from the xml config file """

        option_val = self.xml_map.get(option, None)

        if option_val:
            if type(option_val) is tuple:
                self.assign_option(option_val, value)
            elif type(option_val) is list:
                # If the option_val is a list, there
                # might be multiple vars to set.
                for item in option_val:
                    # The item has to be a tuple again...
                    if type(item) is tuple:
                        # Set it
                        self.assign_option(item, value)
        else:
            #print 'Could not find key for xml option %s' % option
            pass
                       
    def set_option(self, option, value, negate=0):
        """ Set the passed option in the config class
        with its value as the passed value """

        # find out if the option exists in the dictionary
        if option in self._options.keys():
            # if the option is a string or int or any
            # non-seq type

            # if value is an emptry string, return error
            if value=="": return -1

            # Bug fix: If someone has set the
            # value to 'True'/'False' instead of
            # 1/0, convert to bool type first.
            if type(value) in (str, unicode):
                if value.lower() == 'true':
                    value = 1
                elif value.lower() == 'false':
                    value = 0
            
            if type(value) is not tuple:
                # get the key for the option
                key = (self._options[option])[0]
                # get the type of the option
                typ = (self._options[option])[1]
                # do any type casting of the option
                fval = (eval(typ))(value)
                # do any negation of the option
                if type(fval) in (int,bool):
                    if negate: fval = not fval
                # set the option on the dictionary
                self[key] = fval
                
                return 1
            else:
                # option is a tuple of values
                # iterate through all values of the option
                # see if the size of the value tuple and the
                # size of the values for this key match
                _values = self._options[option]
                if len(_values) != len(value): return -1

                for index in range(0, len(_values)):
                    _v = _values[index]
                    if len(_v) !=2: continue
                    _key, _type = _v

                    v = value[index]
                    # do any type casting on the option's value
                    fval = (eval(_type))(v)
                    # do any negation
                    if type(fval) in (int,bool):                    
                        if negate: fval = not fval
                    # set the option on the dictionary
                    self[_key] = fval

                return 1

        return -1

    def get_variable(self, option):
        """ Get the variable for the passed option
        if it exists in the config file, otherwise
        return None """

        # Note: if the option matches more than one
        # variable, the return is a list of variables
        # otherwise a single variable

        if option in self._options.keys():
            value = self._options[option]

            if type(value[0]) is not tuple:
                key = value[0]
                return self.key
            else:
                # the values are tuples
                ret=[]
                for v in value:
                    key = v[0]
                    ret.append(self.key)
                    
                return ret
        else:
            return None

    def get_variable_type(self, option):
        """ Get the type of the variable for the passed
        option if it exists in the config file, else return
        None """

        # Note: if the option matches more than one variable
        # the return is a list of types, otherwise a single type

        if option in self._options.keys():
            value = self._options[option]

            if type(value[0]) is not tuple:
                typ = value[1]
                return typ
            else:
                # the values are tuples
                ret=[]
                for v in value:
                    typ = v[1]
                    ret.append(typ)
                return ret
        else:
            return None


    def Options(self):
        """ Return the options dictionary """

        return self._options

    def parse_arguments(self):
        """ Parse the command line arguments """

        # This function has 3 return values
        # -1 => no cmd line arguments/invalid cmd line arguments
        # ,so force program to read config file.
        # 0 => existing project file supplied in cmd line
        # 1 => all options correctly read from cmd line

        # if no cmd line arguments, then use config file,
        # return -1
        if len(sys.argv)==1:
            return -1

        # Otherwise parse the arguments, the command line arguments
        # are the same as the variables(dictionary keys) of this class.
        # Description
        # Options needing no arguments
        #
        # -h => prints help
        # -v => prints version info

        soptions = 'hvNp:c:b:C:P:V:t:f:l:w:r:n:d:T:R:u:Y:U:W:s:V:M:S:'
        longoptions = [ "configfile=", "projectfile=",
                        "project=", "help","nocrawl",
                        "version", "basedir=",
                        "verbosity=", "depth=","urlfilter=",
                        "maxthreads=","maxfiles=","timelimit=",
                        "retry=","connections=","subbdomain=",
                        "localize=","fetchlevel=","proxy=",
                        "proxyuser=","proxypass=","urlserver=",
                        "cache=","urlslist=","urltree="
                        ]

        arguments = sys.argv[1:]
        try:
            optlist, args = getopt.getopt(arguments, soptions, longoptions)
        except getopt.GetoptError, e:
            sys.exit('Error: ' + str(e))

        if args:
            self.set_option_xml('url',self.process_value(args[0]))
            args.pop(0)
            for idx in range(0,len(args),2):
                item, value = args[idx], args[idx+1]
                optlist.append((item,value))

        # print optlist
        
        for option, value in optlist:
            # first parse arguments with no options
            if option in ('-h', '--help'):
                self.print_help()
                sys.exit(0)
            elif option in ('-v', '--version'):
                self.print_version_info()
                sys.exit(0)
            elif option in ('-C', '--configfile'):
                if self.check_value(value):
                    self.set_option('files.configfile', self.process_value(value))
                    # No need to parse further values
                    return -1
            elif option in ('-P', '--projectfile'):
                if self.check_value(value):
                    self.set_option('files.projectfile', self.process_value(value))
                    import utils 

                    projector = utils.HarvestManProjectManager()

                    if projector.read_project() == 0:
                        # No need to parse further values
                        return 0

            elif option in ('-b', '--basedir'):
                if self.check_value(value): self.set_option_xml('basedir', self.process_value(value))
            elif option in ('-p', '--project'):
                if self.check_value(value): self.set_option_xml('name', self.process_value(value))
            elif option in ('-r', '--retry'):
                if self.check_value(value): self.set_option_xml('retries_value', self.process_value(value))
            elif option in ('-l', '--localize'):
                if self.check_value(value): self.set_option_xml('localise_value', self.process_value(value))
            elif option in ('--f', '--fetchlevel'):
                if self.check_value(value): self.set_option_xml('fetchlevel_value', self.process_value(value))
            elif option in ('-T', '--maxthreads'):
                if self.check_value(value): self.set_option_xml('trackers_value', self.process_value(value))
            elif option in ('-M', '--maxfiles'):
                if self.check_value(value): self.set_option_xml('maxfiles_value', self.process_value(value))
            elif option in ('-t', '--timelimit'):
                if self.check_value(value): self.set_option_xml('timelimit_value', self.process_value(value))
            elif option in ('-w','--workers'):
                self.set_option_xml('workers_status',1)
                if self.check_value(value): self.set_option_xml('workers_size', self.process_value(value))                
            elif option in ('-u', '--urlfilter'):
                if self.check_value(value): self.set_option_xml('urlfilter', self.process_value(value))
            elif option in ('-d', '--depth'):
                if self.check_value(value): self.set_option_xml('depth_value', self.process_value(value))
            elif option in ('-R', '--robots'):
                if self.check_value(value): self.set_option_xml('robots_value', self.process_value(value))
            elif option in ('--urllistfile'):
                if self.check_value(value): self.set_option_xml('urllistfile', self.process_value(value))
            elif option in ('--urltreefile'):
                if self.check_value(value): self.set_option_xml('urltreefile', self.process_value(value))
            elif option in ('-N','--nocrawl'):
                self.nocrawl = True
            elif option in ('-Y', '--proxy'):
                if self.check_value(value):
                    # Set proxyencrypted flat to False
                    self.proxyenc=False
                    self.set_option_xml('proxyserver', self.process_value(value))
            elif option in ('-U', '--proxyuser'):
                if self.check_value(value): self.set_option_xml('proxyuser', self.process_value(value))                
            elif option in ('-W', '--proxypass'):
                if self.check_value(value): self.set_option_xml('proxypasswd', self.process_value(value))
            elif option in ('-s', '--urlserver'):
                if self.check_value(value): self.set_option_xml('urlserver_status', self.process_value(value))
            elif option in ('-S', '--subdomain'):
                if self.check_value(value): self.set_option_xml('subdomain_value', self.process_value(value))                
                
            elif option in ('-c', '--cache'):
                if self.check_value(value): self.set_option_xml('cache_status', self.process_value(value))
            elif option in ('-n', '--connections'):
                if self.check_value(value): self.set_option_xml('connections_value', self.process_value(value))
            elif option in ('-V','--verbosity'):
                if self.check_value(value): self.set_option_xml('verbosity_value', self.process_value(value))
            else:
                print 'Ignoring invalid option ', option

        if self.nocrawl:
            self.pagecache = False
            self.rawsave = True
            self.localise = 0
            # Set project name to ''
            self.set_option_xml('name','')
            # Set basedir to dot
            self.set_option_xml('basedir','.')
            
        # Error in option value
        if self._error:
            print self._error, value
            return -1

        return 1

    def check_value(self, value):
        """ This function checks the values for options
        when options are supplied as command line arguments.
        Returns 0 on any error and non-zero if ok """

        # check #1: If value is a null, return 0
        if not value:
            self._error='Error in option value, value should not be empty!'
            return 0

        # no other checks right now
        return 1

    def process_value(self, value):
        """ This function processes values of command line
        arguments and returns values which can be used by
        this class """

        # a 'yes' is treated as 1 and 'no' as 0
        # also an 'on' is treated as 1 and 'off' as 0
        # Other valid values: integers, strings, 'YES'/'NO'
        # 'OFF'/'ON'

        ret=0
        # We expect the null check has been done before
        val = value.lower()
        if val in ('yes', 'on'):
            return 1
        elif val in ('no', 'off'):
            return 0

        # convert value to int
        try:
            ret=int(val)
            return ret
        except:
            pass

        # return string value directly
        return str(value)

    def print_help(self):
        """ Prints the help information """

        print PROG_HELP % {'appname' : self.appname,
                           'version' : self.version,
                           'maturity' : self.maturity }

    def print_version_info(self):
        """ Print version information """

        print 'Version: %s %s' % (self.version, self.maturity)

    def __fix(self):
        """ Fix errors in config variables """

        # If there is more than one url, we
        # combine all the project related
        # variables into a dictionary for easy
        # lookup.
        num=len(self.urls)
        if num==0:
            sys.exit("Fatal Error: No URLs given, Aborting.")
            
        if not len(self.projtimeouts): self.projtimeouts.append(self.projtimeout)
        if not len(self.verbosities): self.verbosities.append(self.verbosity)
        
        if num>1:
            # Check the other list variables
            # If their length is less than url length
            # make up for it.
            for x in range(num-len(self.projects)):
                self.projects.append(self.projects[x])
            for x in range(num-len(self.basedirs)):
                self.basedirs.append(self.basedirs[x])                    
            for x in range(num-len(self.verbosities)):
                self.verbosities.append(self.verbosities[x])
            for x in range(num-len(self.projtimeouts)):
                self.projtimeouts.append(self.projtimeouts[x])
                

        # Fix url error
        for x in range(len(self.urls)):
            url = self.urls[x]

            # If null url, return
            if not url: continue

            # Check for protocol strings
            # http://
            pindex = -1
            pindex = url.find('http://')
            if pindex == -1:
                # ftp://
                pindex = url.find('ftp://')
                if pindex == -1:
                    # https://
                    pindex = url.find('https://')
                    if pindex == -1:
                        # www.
                        pindex = url.find('www.')
                        if pindex == -1:
                            pindex = url.find('file://')
                            if pindex == -1:
                                # prepend http:// to it
                                url = 'http://' + url


            self.urls[x] = url

            # If project is not set, set it to domain
            # name of the url.
            project = None
            try:
                project = self.projects[x]
            except:
                pass

            if not project:
                import urlparser
                h = urlparser.HarvestManUrlParser(url)
                project = h.get_domain()
                self.projects.append(project)

            basedir = None
            try:
                basedir = self.basedirs[x]
            except:
                pass

            if not basedir:
                self.basedirs.append('.')

    def parse_config_file(self):
        """ Opens the configuration file and parses it """

        cfgfile = self.configfile

        # If configuration is an xml file, parse it using
        # xml parser.
        if ((os.path.splitext(cfgfile))[1]).lower() == '.xml':
            import xmlparser
            return xmlparser.parse_xml_config_file(self, cfgfile)
        
        # open config file
        try:
            cf=open(cfgfile, 'r')
        except IOError:
            print 'Fatal error: Cannot find config file', cfgfile
            msg1 = "\nCreate or copy a config file to this directory"
            msg2 = "\nor run the program with the -C option to use \na different config file"
            sys.exit("".join((msg1,msg2)))
            
        # Parsing config file
        while 1:
            l=cf.readline()
            if l=='': break
            # strip '\n' from the string
            l = l.replace('\n','')
            # replace tabs with spaces
            l = l.replace('\t', '    ')
            index = l.find(' ')
            if index == -1: continue
            str1 = l[:index]
            # Any line beginning with a '#' is a comment.
            if str1[0] == '#': continue

            # Mod: From v (1.2alpha) the config file format
            # is changed. We also support ';;' as the comment
            # character (it is the default now)
            if str1[:2] == ';;': continue
            # Get value string
            str2 = l[(index+1):]
            # Modification: Allow comments in the config line also
            # Egs: URL http://www.python.org # The url for download
            for s in ('#', ';;'):
                hashidx = str2.find(s)
                if hashidx != -1:
                    str2 = str2[:hashidx]

            # strip any leading spaces
            str2 = str2.strip()
            if str1 in self.Options().keys():
                self.set_option(str1, str2)
            else:
                print 'Invalid config option', str1

        return 1

    def get_program_options(self):
        """ This function gets the program options from
        the config file or command line """

        # first check in argument list, if failed
        # check in config file
        res = self.parse_arguments()
        if res==-1:
            self.parse_config_file()
            
        # fix errors in config variables
        self.__fix()

    def __getattr__(self, name):
        try:
            return self[intern(name)]
        except KeyError:
            return

    def __setattr__(self, name, value):
        self[intern(name)] = value



