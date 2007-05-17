""" Simulator plugin for HarvestMan. This
plugin changes the behaviour of HarvestMan
to only simulate crawling without actually
downloading anything.

Created Feb 7 2007  Anand B Pillai <abpillai at gmail dot com>

Copyright (C) 2007 Anand B Pillai
   
"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

import hookswrapper
from common.common import *


def func(self):
    print 'Before running projects...'

def apply_plugin():
    """ All plugin modules need to define this method """

    # This method is expected to perform the following steps.
    # 1. Register the required hook function
    # 2. Get the config object and set/override any required settings
    # 3. Print any informational messages.

    # The first step is required, the last two are of course optional
    # depending upon the required application of the plugin.
    
    hookswrapper.register_pre_callback_method('harvestmanklass:run_projects_callback', func)

