# This module is part of the HarvestMan project and is Copyright 2004-2005
# Anand B Pillai (abpillai at gmail dot com)

# Fixed a bug in function site_packages_dir - Use sys.path instead of
# site.sitedirs since latter is not there in Python 2.4 - Anand 09/09/05

from distutils.core import setup
import os, sys

def site_packages_dir():
    
    for p in sys.path:
        if p.find('site-packages') != -1:
            return p
    
def make_data_files():
    data_files = []
    # Get the install directory
    sitedir = site_packages_dir()
    data_list = []
    
    # Create list for doc directory first.
    # harvestman doc dir
    if os.path.isdir("doc"):
        hdir = os.path.join(sitedir, "HarvestMan", "doc")
        for f in os.listdir("doc"):
            data_list.append("".join(("doc/",f)))
        data_files.append((hdir, data_list))

    return data_files
    
setup(name="HarvestMan",
      version="1.5 b1",
      description="HarvestMan - Extensible multithreaded Offline Browser/Web Crawler",
      author="Anand B Pillai",
      author_email="abpillai_at_gmail_dot_com",
      url="http://harvestman.freezope.org/",
      license="GNU General Public License",
      packages = ['HarvestMan', 'HarvestMan.tools'],
      data_files=make_data_files(),
      )



