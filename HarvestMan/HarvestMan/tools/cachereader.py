# -- coding: iso8859-1
"""Utility to print a human readable version
of HarvestMan cache file

Author: Anand B Pillai
Copyright (C) 2004 - 2005: Anand B Pillai

This file is part of HarvestMan package.
"""

import zlib

def uncompresscache(cachefile):
    return zlib.decompress(open(cachefile, 'rb').read())

if __name__=="__main__":
    import sys
    if len(sys.argv)<2:
        sys.exit("Usage: cachereader.py <harvestman cache file>")
        
    print uncompresscache(sys.argv[1])
