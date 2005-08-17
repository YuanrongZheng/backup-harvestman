# This module is part of the HarvestMan project and is Copyright 2004-2005
# Anand B Pillai (anandpillai at letterboxes dot org).

from distutils.core import setup
import os

def site_packages_dir():
    import site
    
    for p in site.sitedirs:
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

    if os.path.isdir("tidy"):
        # Create list for tidy files next
        tidydir = os.path.join(sitedir, "HarvestMan", "tidy")
        tidypath = "HarvestMan/tidy/"
        data_list = ["".join((tidypath, "cygtidy-0-99-0.dll"))]
        data_files.append((tidydir, data_list))
    
        tidydir = os.path.join(tidydir, "pvt_ctypes")
        data_list = ["".join((tidypath, "pvt_ctypes/README.ctypes")),
                     "".join((tidypath, "pvt_ctypes/_ctypes.pyd")),
                     "".join((tidypath, "pvt_ctypes/_ctypes.so")),
                     "".join((tidypath, "pvt_ctypes/ctypes.zip"))]
                 
        data_files.append((tidydir, data_list))
    
    return data_files
    
setup(name="HarvestMan",
      version="1.4.5 alpha1",
      description="HarvestMan - Multithreaded Offline Browser/Web Crawler",
      author="Anand B Pillai",
      author_email="abpillai_at_gmail_dot_com",
      url="http://harvestman.freezope.org/",
      license="GNU General Public License",
      packages = ['HarvestMan', 'HarvestMan.tools'],
      data_files=make_data_files(),
      )



