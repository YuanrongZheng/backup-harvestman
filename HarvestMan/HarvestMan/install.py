# py2exe install script for harvestman

from distutils.core import setup

import py2exe

setup(name="HarvestMan",
      scripts=["harvestman.py"],
)
