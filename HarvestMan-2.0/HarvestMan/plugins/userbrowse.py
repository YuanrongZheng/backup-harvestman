""" User browse plugin. Simulate a scenario of a user
browsing a web-page.

(Requested by Roy Cheeran)

Author: Anand B Pillai <anand at harvestmanontheweb.com>

Created  Aug 13 2007     Anand B Pillai <abpillai at gmail dot com>

Copyright (C) 2007 Anand B Pillai

"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

import hookswrapper
from common.common import *

def apply_plugin():
    """ Apply the plugin - overrideable method """

    # This method is expected to perform the following steps.
    # 1. Register the required hook/plugin function
    # 2. Get the config object and set/override any required settings
    # 3. Print any informational messages.

    # The first step is required, the last two are of course optional
    # depending upon the required application of the plugin.

    cfg = GetObject('config')
    # Set depth to 0
    cfg.depth = 0
    # Set fetchlevel to 2
    cfg.fetchlevel = 2
    # Images & stylesheets will skip rules
    cfg.skipruletypes = ['image','stylesheet']
    # One might have to set robots to 0
    # sometimes to fetch images - uncomment this
    # in such a case.
    # cfg.robots = 0
