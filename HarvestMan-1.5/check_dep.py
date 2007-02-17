#!/usr/bin/env python
# -- coding: latin-1

# Dependency checker version 1
# Author: Anand B Pillai

if __name__=="__main__":
    import sys

    app = 'HarvestMan'
    py = 'Python'

    err=0
    
    print 'x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x'
    print '* Welcome to %s dependency checker*' % app
    print 'x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x\n'

    ver = sys.version_info
    
    if (ver[0] == 2 and ver[1] < 2) or (ver[0] < 2):
        err=1
        print 'Dependency failed: You need %s 2.2 or higher to run %s.' % (py, app)
    elif (ver[0] == 2 and ver[1] == 2):
        err=2
        print '%s version 2.2 detected, the following features will be disabled:'
        print '\t1.Tar Archival feature'
    elif (ver[0] == 2 and ver[1] == 3):
        print '%s 2.3 version detected' % py
    elif (ver[0] == 2 and ver[1] == 4):
        print '%s 2.4 version detected' % py        

    if err==1:
        print '%s will not run' % app
    elif err==2:
        print '%s will run, but with limited features' % app
    elif err==0:
        print '%s will run without problems.' % app

