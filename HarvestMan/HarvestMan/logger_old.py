# -- coding: latin-1
""" logger.py - Logging functions for HarvestMan.
This file is part of the HarvestMan program.

Author: Anand B Pillai
Created: Jan 23 2005

"""
import sys

class HarvestManLogger(object):
    """ Logging class for HarvestMan """

    def __init__(self):
        
        self.logfile = ''
        self.stream = None
        self.verbosity = 2

    def setLogFile(self, logfile):

        self.logfile = logfile
 
        try:
            self.stream = open(self.logfile, 'w')
        except (OSError, IOError), e:
            print e
        except Exception, e:
            print e

    def close(self):
        """ Close the logging stream """

        
        try:
            if self.stream:
                self.stream.flush()
                self.stream.close()
        except (IOError, EOFError), e:
            print e

    # Common tracing function
    def trace(self, arg, *args):
        """ Write the variable argument list to stdout """

        # print args
        op=str(arg)
        if args:
            op = ''.join((op, ' ',''.join([str(item) + ' ' for item in args])))

        # Use the simple print
        print op

    # Common logging function
    def log(self, arg, *args):
        """ Logging function - This logs messages to a file """

        op=str(arg)
        if args:
            op = ''.join((op, ' ',''.join([str(item) + ' ' for item in args])))

        try:
            self.stream.write("".join((op,'\n')))
        except (AttributeError, IOError, OSError), e:
            print e
        except Exception, e:
            print e

    # Common function to both log & trace
    def logntrace(self, arg, *args):
        """ Log & trace function - This does both tracing & logging """
        
        self.trace(arg, *args)
        if self.stream:
            self.log(arg, *args)

    # Tracing functions at various levels        
    def trace1(self, arg, *args):
        """ Trace function - Level 1 """

        if self.verbosity>=1:
            self.trace(arg, *args)

    def trace2(self, arg, *args):
        """ Trace function - Level 2 """

        if self.verbosity>=2:
            self.trace(arg, *args)

    def trace3(self, arg, *args):
        """ Trace function - Level 3 """

        if self.verbosity>=3:
            self.trace(arg, *args)

    def trace4(self, arg, *args):
        """ Trace function - Level 4 """

        if self.verbosity>=4:
            self.trace(arg, *args)

    def trace5(self, arg, *args):
        """ Trace function - Level 5 """

        if self.verbosity>=5:
            self.trace(arg, *args)

    # Logging functions at various levels        
    def log1(self, arg, *args):
        """ Log function - Level 1 """

        if self.verbosity>=1:
            self.log(arg, *args)

    def log2(self, arg, *args):
        """ Log function - Level 2 """

        if self.verbosity>=2:
            self.log(arg, *args)

    def log3(self, arg, *args):
        """ Log function - Level 3 """

        if self.verbosity>=3:
            self.log(arg, *args)

    def log4(self, arg, *args):
        """ Log function - Level 4 """

        if self.verbosity>=4:
            self.log(arg, *args)

    def log5(self, arg, *args):
        """ Log function - Level 5 """

        if self.verbosity>=5:
            self.log(arg, *args)            

    # Trace & log functions at various levels
    def logntrace1(self, arg, *args):
        """ Log & trace function - Level 1 """

        if self.verbosity>=1:
            self.logntrace(arg, *args)

    def logntrace2(self, arg, *args):
        """ Log & trace function - Level 2 """

        if self.verbosity>=2:
            self.logntrace(arg, *args)

    def logntrace3(self, arg, *args):
        """ Log & trace function - Level 3 """

        if self.verbosity>=3:
            self.logntrace(arg, *args)

    def logntrace4(self, arg, *args):
        """ Log & trace function - Level 4 """

        if self.verbosity>=4:
            self.logntrace(arg, *args)

    def logntrace5(self, arg, *args):
        """ Log & trace function - Level 5 """

        if self.verbosity>=5:
            self.logntrace(arg, *args)


    # Trace & log functions at various levels
    def info(self, arg, *args):
        """ Log & trace function - Level 1 """

        if self.verbosity>=1:
            self.logntrace(arg, *args)

    def moreinfo(self, arg, *args):
        """ Log & trace function - Level 2 """

        if self.verbosity>=2:
            self.logntrace(arg, *args)

    def extrainfo(self, arg, *args):
        """ Log & trace function - Level 3 """

        if self.verbosity>=3:
            self.logntrace(arg, *args)

    def debug(self, arg, *args):
        """ Log & trace function - Level 4 """

        if self.verbosity>=4:
            self.logntrace(arg, *args)

    def moredebug(self, arg, *args):
        """ Log & trace function - Level 5 """

        if self.verbosity>=5:
            self.logntrace(arg, *args)                        
        
        
            

