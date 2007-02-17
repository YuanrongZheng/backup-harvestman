#!/usr/bin/env python
# -- coding: latin-1

# convertconfig.py - Convert config files
# between xml & text formats.
# Author - Anand Pillai.
# Jan 9 2005 - Creation

def usage(prog):
    print '%s : Convert between HarvestMan text & xml config files.'  % prog
    print 'Usage: %s <config file>' % prog
    print ''
    print 'Conversion is done automatically by looking at the file extension.'
    print 'If the file is text, xml conversion is done and viceverza.'

def convert_config(configfile):
    """ Convert config file from text->xml or xml->text """

    import os
    from genconfig import GenConfig

    # Default conversion is txt->xml
    conv=1
    # Get extension
    extn = ((os.path.splitext(configfile))[1]).lower()
    if extn in ('.txt', '.text'):
        # To xml
        conv=1
    elif extn == '.xml':
        # To text
        conv=2

    # Make genconfig object
    gcfg = GenConfig()
    # Get cfg object from genconfig object
    cfg = gcfg.__dict__['cfg']
    # Parse config file
    cfg.configfile = configfile
    if not cfg.parse_config_file():
        sys.exit('Error parsing config file %s' % configfile)
    # Now cfg has all params contained
    # in config file. We can safely
    # do conversion.

    if conv==1:
        print 'Converting text config file to xml...'
        cfg.format='xml'
    elif conv==2:
        print 'Converting xml config file to text...'
        cfg.format = 'text'
    
    gcfg.GenConfigFile()

if __name__=="__main__":
    import sys
    
    if len(sys.argv)<2:
        usage(sys.argv[0])
        sys.exit(2)
        
    # Pick up modules from the
    # parent directory.
    sys.path.append("..")
    
    from common import *

    # Initialize globals
    Initialize()
    convert_config(sys.argv[1])
