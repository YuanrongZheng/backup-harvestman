# -- coding: iso8859-1
""" HarvestManConfig.py - Module to keep configuration options
    for HarvestMan program and its related modules. This software is
    part of the HarvestMan program.

    Author: Anand B Pillai (anandpillai at letterboxes dot org).

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

"""

PROG_HELP = """\

%(appname)s [options]

%(appname)s is a command-line offline browser. It can be used to download
websites/files from the internet and save them to the disk for offline browsing/
viewing.

This is Version %(version)s.

Authors: Anand B Pillai.
Copyright (C) 2004-2005 Anand B Pillai.

WWW:       http://harvestman.freezope.org
(Please note that the command line interface is not up-to-date with
features of HarvestMan. Try to use the config file option always.)

By default %(appname)s reads its options from a config file named 'config.txt'
in the current directory. If this file is not present, then %(appname)s reads
the options from the command line.

You can use the option '--configfile' to specify a different config filename
on the command line, or the option '--projectfile' to read an existing project
file.

Options:


1. Help Options:

    -h/--help:\t\t\tShow this message
    -v/--version\t\tPrint version information and exit

2. Necessary Options:

    -U/--url\t\t\tStart downloading from this url.
    -P/--project\t\tName of this %(appname)s project.
    -B/--basedir\t\tThe base directory to save downloaded files to.

3. Basic Options:

    -C/--configfile\t\tUse this config filename ('config.txt').
    --PF/--projectfile\t\tLoad this %(appname)s project file.
    -V/--verbosity\t\tThe verbosity level (0-5, 2).
    -H/--html\t\t\tWhether to download html files (yes).*
    -I/--images\t\t\tWhether to download image links of a page (yes). *
    -S/--getcss\t\t\tDownload stylesheets of a page always (yes). *
    -i/--getimages\t\tDownload images of a page always (yes). *
    -F/--fastmode\t\tRun in fastmode (yes).

    --rn/--renamefiles\t\tWhether to try renaming dynamically generated files (no). *
    --fl/--fetchlevel\t\tThe fetchlevel setting (1).

    -r/--retryfailed\t\tNumber of retry attempts on failed links (1). *
    -l/--localise\t\tWhether to localise hyper text links after download (2). *
    -b/--browsepage\t\tTells the program to create a project browser index page (yes). *

4. Advanced Options:

    -j/--jitlocalise\t\tShould try and localise each page immmediately after downnload. (no)
    -t/--usethreads\t\tWhether to download non-html files in multiple threads (yes). *
    -s/--threadpoolsize\t\tSize of the thread pool (20).
    -o/--timeout\t\tTimeout value in seconds for a thread in the thread pool (600 sec) .
    -po/--prjtimeout\t\tTimeout value in seconds for the project (600 sec) .

    -E/--errorfile\t\tThe error file name ('errors.log').
    -L/--logfile\t\tThe name of the message log file ('harvestman.log').
    --UL/--urllistfile\t\tThe filename to dump the list of urls crawled.

    -p/--proxy\t\t\tSet this to the name/ip of the proxy server in your LAN/WAN, if you are behind one.
    -u/--puser\t\t\tSet this to the username for the proxy server, if the proxy needs authentication.
    -w/--ppasswd\t\tSet this to the password for the proxy server, if the proxy needs authentication.
    --pp/--pport\t\tSet this to the port number where the proxy accepts connections (80).

    -n/--username\t\tLogin to the site with this username. *
    -d/--userpasswd\t\tLogin to the site with this password. *

    -c/--checkfiles\t\tAttempt to verify the integrity of files (yes).
    --hp/--htmlparser\t\tThe html parser to use for parsing html files (0). *

5. Download options:

    -k/--cookies\t\tSupport for cookies  (yes). *
    --nc/--connections\t\tEnable so many network connections at a given time (5). *
    --pc/--cachepages\t\tSupport for caching/update of webpages (yes). *
    --ep/--epagelinks\t\tDownload links on pages outside start urls directory (yes). *
    --es/---eserverlinks\tDownload links from external servers (no). *

    --d1/--depth\t\tDepth of fetching on the starting server (10).
    --d2/--extdepth\t\tDepth of fetching on external servers (no limit).

    --M1/--maxdirs\t\tLimit on external directories from which links are fetched (no limit).
    --M2/--maxservers\t\tLimit on external servers from which links are fetched (no limit).
    --M/--maxfiles\t\tMaxmimum number of files to download (3000).
    --MT/--maxthreads\t\tLimit on number of url trackers(threads) to run (10).

    --R/--rep\t\t\tWhether to support Robot Exclusion Protocol (yes). *
    --F1/--urlfilter\t\tThe regular expression for filtering urls.
    --F2/--serverfilter\t\tThe regular expression for filtering outside servers.

    --js/--javascript\t\tDownload server side javascript (.js) files (yes). *
    --ja/--java\t\t\tDownload java class (.class) files (yes). *

    NOTE: Options that need a [yes/no] argument are marked with an asterik '*'.
        You can also use the arguments [on/off] or [1/0] in place of [yes/no].
        These are case-insensitive. The value inside the parantheses at the end
        shows the default value for each option, if any.


"""

import os, sys
import getopt
from common import *

class HarvestManStateObject(dict):
    """ Internal config class for the program """

    def __init__(self):
        """ Initialize dictionary with the most common
        settings and their values """

        self.version='1.4.1'
        self.appname='HarvestMan'
        self.progname='HarvestMan 1.4.1'
        self.url=''
        self.project=''
        self.basedir=''
        self.configfile = 'config.xml'
        self.projectfile = ''         
        self.proxy=''
        self.puser=''
        self.ppasswd=''
        self.siteusername=''   
        self.sitepasswd=''     
        self.proxyport=0
        self.errorfile='errors.log'
        self.urlslistfile= ''
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
        self.timeout=200
        self.getimagelinks=1
        self.getstylesheets=1
        self.threadpoolsize=10
        self.renamefiles=0
        self.fetchlevel=0
        self.browsepage=1 
        self.htmlparser=0
        self.checkfiles=1
        self.cookies=1
        self.pagecache=1
        self._error=''
        self.starttime=0
        self.endtime=0
        self.javascript = True
        self.javaapplet = True
        self.connections=5
        self.cachefileformat='pickled' # Values => 'pickled' or 'xml'
        # 1. Testing the code (no browse page)
        self.testing = True
        # 2. Testing the browse page (no crawl)
        self.testnocrawl = True
        self.ignorekbinterrupt = False
        self.subdomain = False
        self.skipqueryforms = True
        self.requests = 5
        self.bytes = 20.00 # Not used!
        self.projtimeout = 300 
        self.downloadtime = 0.0
        self.tidyhtml = True
        self.locale = 'american'
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
        # Maximum file size is 1MB
        self.maxfilesize=1048576
        # Minimum file size is 0 bytes
        self.minfilesize=0
        # config file format
        self.format = 'xml'
        
        # create the dictionary of mappings containing
        # config options to dictionary keys and their
        # types

        # The dictionary containing the mapping
        # of config options to dictionary keys and their types
        self._options = {
                            'project.url' : ('url', 'str'),
                            'project.name' : ('project', 'str'),
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
                            'download.forms' : ('skipqueryforms', 'int'),
                            'download.cache' : ('pagecache', 'int'),
                            'download.datacache' : ('datacache', 'int'),
                            'download.tidyhtml' : ('tidyhtml', 'int'),

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
                            'files.urlslistfile' : ('urlslistfile', 'str'),
                            'files.urltreefile'  : ('urltreefile', 'str'),

                            'display.browsepage' : ('browsepage', 'int'), 
                            }

        # For mapping xml entities to config entities
        
        self.xml_map = { 'url' : 'project.url',
                         'name': 'project.name',
                         'basedir' : 'project.basedir',
                         'verbosity_value' : 'project.verbosity',
                         'timeout_value' : 'project.timeout',

                         'proxyserver': 'network.proxyserver',
                         'proxyuser': 'network.proxyuser',
                         'proxypasswd' : 'network.proxypasswd',
                         'proxyport_value' : 'network.proxyport',

                         'urlserver_status' : 'network.urlserver',
                         'urlhost' : 'network.urlhost',
                         'urlport_value' : 'network.urlport',

                         'html_value' : 'download.html',
                         'images_value' : 'download.images',
                         'javascript_value' : 'download.javascript',
                         'javaapplet_value' : 'download.javaapplet',
                         'forms_value' : 'download.forms',

                         'cache_status' : 'control.pagecache',
                         'datacache_value' : 'control.datacache',

                         'retries_value': 'download.retries',
                         'tidyhtml_value' : 'download.tidyhtml',

                         'imagelinks_value' : 'control.linkedimages',
                         'stylesheetlinks_value' : 'control.linkedstylesheets',
                         'fetchlevel_value' : 'control.fetchlevel',
                         'extserverlinks_value' : 'control.extserverlinks',
                         'extpagelinks_value' : 'control.extpagelinks',
                         'depth_value' : 'control.depth',
                         'extdepth_value' : 'control.extdepth',
                         'subdomain_value' : 'control.subdomain',
                         'maxextservers_value' : 'control.maxextservers',
                         'maxextdirs_value' : 'control.maxextdirs',
                         'maxfiles_value' : 'control.maxfiles',
                         'maxfilesize_value' : 'control.maxfilesize',
                         'connections_value' : 'control.connections',
                         'requests_value' : 'control.requests',
                         'robots_value' : 'control.robots',
                         'urlpriority' : 'control.urlpriority',
                         'serverpriority' : 'control.serverpriority',
                         'urlfilter': 'control.urlfilter',
                         'serverfilter' : 'control.serverfilter',
                         'wordfilter' : 'control.wordfilter',
                         'junkfilter_value' : 'control.junkfilter',
                         'workers_status' : 'system.usethreads',
                         'workers_size' : 'system.threadpoolsize',
                         'workers_timeout' : 'system.threadtimeout',
                         'trackers_value' : 'system.maxtrackers',
                         'locale' : 'system.locale',
                         'fastmode_value': 'system.fastmode',
                         'localise_value' : 'indexer.localise',
                         'browsepage_value' : 'display.browsepage'
                         }
                         
    def set_option_xml(self, option, value):
        """ Set an option from the xml config file """

        # Pick key for setting regular option
        # from xml map.
        option_key = self.xml_map.get(option, None)
        if option_key:
            self.set_option(option_key, value)
            debug('Option set for %s %s' % (option_key, value))
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
        import sys

        # return value
        res=0
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

        # Options needing arguments (short type)
        #
        # -U => url
        # -P => project
        # -B => base directory
        # -b => browse page
        # -C => new config filename
        # -V => verbosity
        # -M => max files setting
        # -s => thread pool size
        # -o => timeout limit
        # -E => error file name
        # -L => logfile name
        # -p => proxy server
        # -u => username for proxy
        # -w => password for proxy
        # -H => html flag
        # -I => image flag
        # -S => get stylesheets downloaded
        # -i => get images downloaded
        # -r => retry failed links (can have an option but not necessary)
        # -l => localise links
        # -t => threads flag
        # -F => fastmode flag
        # -R => REP flag
        # -n => site username
        # -d => site password
        # -k => cookies support

        # Long type options
        # --url => url
        # --project => project
        # --help => help string
        # --version => version string
        # --basedir => base directory
        # --browsepage => create a project browse page?
        # --configfile => config filename
        # --projectfile => project filename
        # --verbosity => verbosity
        # --html => html
        # --images => images
        # --getcss => css setting
        # --getimages => image setting
        # --ep/--epagelinks => external page links
        # --es/--eserverlinks => external server links
        # --d1/--depth => depth setting
        # --d2/--extdepth => external depth setting
        # --M1/--maxdirs => maxdirs setting
        # --M2/--maxservers => maxservers setting
        # --maxfiles => maxfiles setting
        # --rep => Robot Exclusion Principle setting
        # --F1/--urlfiler => url filters
        # --F2/--serverfilter => server filters
        # --retryfailed => retry failed setting
        # --localise => localise links setting
        # --MT/--maxthreads => maxthreads setting
        # --usethreads => usethreads setting
        # --threadpoolsize => thread pool size setting
        # --timeout => timeout setting
        # --rn/--renamefiles => renamefiles setting
        # --fl/--fetchlevel => fetch level setting
        # --fastmode => fast mode setting
        # --errorfile => errorfile setting
        # --logfile => logfile setting
        # --UL/--urlslistfile => urls list file
        # --proxy => proxy server setting
        # --puser => proxy user setting
        # --ppasswd => proxy passwd setting
        # --pp/--pport => proxy port setting
        # --username => site username
        # --userpasswd => site password
        # --pc/--pagecache => support for webpage caching/update
        # --cookies => support for cookies
        # --nc/--connections => number of network connections
        # --po/--prjtimeout => timeout value in seconds for the project
        # --js/--javascript => option for controlling download of javascript files
        # --ja/--javaapplet => option for controlling download of java applet files

        shortoptionsstring = 'hvU:P:B:b:C:V:M:s:o:E:L:p:u:w:H:I:i:t:F:R:S:l:r:c:j:n:d:k:'
        longoptions = [ "configfile=", "projectfile=",
                        "url=", "project=", "help",
                        "version", "basedir=", "browsepage=",
                        "verbosity=","html=", "images=",
                        "getcss=", "getimages=", "epagelinks=",
                        "eserverlinks=","depth=","d1=", "extdepth=",
                        "d2=", "M1=", "maxdirs=", "M2=", "maxservers=",
                        "maxfiles=", "rep=", "F1=", "urlfilter=", "F2=",
                        "serverfilter=", "retryfailed=","localise=",
                        "MT=", "maxthreads=", "usethreads", "threadpoolsize=",
                        "timeout=","rn", "renamefiles", "fl=", "fetchlevel=",
                        "fastmode=", "errorfile=", "logfile=",
                        "UL=", "urlslistfile=", "proxy=", "puser=",
                        "ppasswd=", "pp=","pport=", "jitlocalise",
                        "checkfiles", "htmlparser=", "hp=", "username=",
                        "userpasswd=", "cookies=", "pagecache=",
                        "pc=", "nc=", "connections=", "po=",
                        "prjtimeout=", "js==", "javascript=",
                        "ja=", "javaapplet="
                        ]

        arguments = sys.argv[1:]
        try:
            optlist, args = getopt.getopt(arguments, shortoptionsstring, longoptions)
        except getopt.GetoptError, e:
            print 'Error: ',e
            return -1

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
            elif option in ('--PF', '--projectfile'):
                if self.check_value(value):
                    self.set_option('files.projectfile', self.process_value(value))
                    import utils 

                    projector = utils.HarvestManProjectManager()

                    if projector.read_project() == 0:
                        # No need to parse further values
                        return 0

            elif option in ('-U', '--url'):
                if self.check_value(value): self.set_option('project.url', self.process_value(value))
            elif option in ('-B', '--basedir'):
                if self.check_value(value): self.set_option('project.basedir', self.process_value(value))
            elif option in ('-P', '--project'):
                if self.check_value(value): self.set_option('project.name', self.process_value(value))
            elif option in ('-H', '--html'):
                if self.check_value(value): self.set_option('download.html', self.process_value(value))
            elif option in ('-I', '--images'):
                if self.check_value(value): self.set_option('download.images', self.process_value(value))
            elif option in ('-S', '--getcss'):
                if self.check_value(value): self.set_option('download.linkedstylesheets', self.process_value(value))
            elif option in ('-i', '--getimages'):
                if self.check_value(value): self.set_option('download.linkedimages', self.process_value(value))
            elif option in ('-r', '--retryfailed'):
                if self.check_value(value): self.set_option('download.retryfailed', self.process_value(value))
            elif option in ('-l', '--localise'):
                if self.check_value(value): self.set_option('indexer.localise', self.process_value(value))
            elif option in ('-l', '--browsepage'):
                if self.check_value(value): self.set_option('display.browsepage', self.process_value(value))
            elif option in ('-c', '--checkfiles'):
                if self.check_value(value): self.set_option('download.checkfiles', self.process_value(value))
            elif option in ('-j', '--jitlocalise'):
                if self.check_value(value): self.set_option('indexer.jitlocalise', self.process_value(value))
            elif option in ('--hp', '--htmlparser'):
                if self.check_value(value): self.set_option('parser.htmlparser', self.process_value(value))
            elif option in ('-t', '--usethreads'):
                if self.check_value(value): self.set_option('system.usethreads', self.process_value(value))
            elif option in ('-s', '--threadpoolsize'):
                if self.check_value(value): self.set_option('system.threadpoolsize', self.process_value(value))
            elif option in ('-o', '--timeout'):
                if self.check_value(value): self.set_option('system.threadtimeout', self.process_value(value))
            elif option in ('--rn', '--renamefiles'):
                if self.check_value(value): self.set_option('download.rename', self.process_value(value))
            elif option in ('--fl', '--fetchlevel'):
                if self.check_value(value): self.set_option('download.fetchlevel', self.process_value(value))
            elif option in ('-F', '--fastmode'):
                if self.check_value(value): self.set_option('system.fastmode', self.process_value(value))
            elif option in ('--MT', '--maxthreads'):
                if self.check_value(value): self.set_option('system.maxtrackers', self.process_value(value))
            elif option in ('--M1', '--maxdirs'):
                if self.check_value(value): self.set_option('control.maxextdirs', self.process_value(value))
            elif option in ('--M2', '--maxservers'):
                if self.check_value(value): self.set_option('control.maxextservers', self.process_value(value))
            elif option in ('--M', '--maxfiles'):
                if self.check_value(value): self.set_option('control.maxfiles', self.process_value(value))
            elif option in ('--F1', '--urlfilter'):
                if self.check_value(value): self.set_option('control.urlfilter', self.process_value(value))
            elif option in ('--F2', '--serverfilter'):
                if self.check_value(value): self.set_option('control.serverfilter', self.process_value(value))
            elif option in ('--ep', '--epagelinks'):
                if self.check_value(value): self.set_option('control.extpagelinks', self.process_value(value))
            elif option in ('--es', '--eserverlinks'):
                if self.check_value(value): self.set_option('control.extserverlinks', self.process_value(value))
            elif option in ('--d1', '--depth'):
                if self.check_value(value): self.set_option('control.depth', self.process_value(value))
            elif option in ('--d2', '--extdepth'):
                if self.check_value(value): self.set_option('control.extdepth', self.process_value(value))
            elif option in ('--R', '--rep'):
                if self.check_value(value): self.set_option('control.robots', self.process_value(value))
            elif option in ('-E', '--errorfile'):
                if self.check_value(value): self.set_option('files.errorfile', self.process_value(value))
            elif option in ('-L', '--logfile'):
                if self.check_value(value): self.set_option('files.logfile', self.process_value(value))
            elif option in ('--UL', '--urllistfile'):
                if self.check_value(value): self.set_option('files.urllistfile', self.process_value(value))
            elif option in ('-p', '--proxy'):
                if self.check_value(value): self.set_option('network.proxyserver', self.process_value(value))
            elif option in ('-u', '--puser'):
                if self.check_value(value): self.set_option('network.proxyuser', self.process_value(value))
            elif option in ('-w', '--ppasswd'):
                if self.check_value(value): self.set_option('network.proxypasswd', self.process_value(value))
            elif option in ('--pp', '--pport'):
                if self.check_value(value): self.set_option('network.proxyport', self.process_value(value))
            elif option in ('-k', '--cookies'):
                if self.check_value(value): self.set_option('download.cookies', self.process_value(value))
            elif option in ('--pc', '--pagecache'):
                if self.check_value(value): self.set_option('control.pagecache', self.process_value(value))
            elif option in ('--nc', '--connections'):
                if self.check_value(value): self.set_option('control.connections', self.process_value(value))
            elif option in ('--po', '--prjtimeout'):
                if self.check_value(value): self.set_option('control.projtimeout', self.process_value(value))
            elif option in ('--js', '--javascript'):
                if self.check_value(value): self.set_option('download.javascript', self.process_value(value))
            elif option in ('--ja', '--javaapplet'):
                if self.check_value(value): self.set_option('download.javaapplet', self.process_value(value))
            else:
                print 'Ignoring invalid option ', option

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
                           'version' : self.version }

    def print_version_info(self):
        """ Print version information """

        print 'Version: ', self.version

    def __fix(self):
        """ Fix errors in config variables """

        # Fix url error
        # Check for protocol strings
        # http://
        url = self.url

        # If null url, return
        if not url: return
        
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


        self.url = url

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
            return None

    def __setattr__(self, name, value):
        self[intern(name)] = value



