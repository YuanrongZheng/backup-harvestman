 # -- coding: latin-1
""" HarvestManUtils.py - Utility classes for harvestman
    program.

    Created: Anand B Pillai on Sep 25 2003.
    
    Author: Anand B Pillai (anandpillai at letterboxes dot org).    

    This contains a class for pickling using compressed data
    streams and another one for writing project files.

    Feb 10 2004   Anand   1.3.1 bug fix release.
    Jun 14 2004   Anand   1.3.9 release.
    Oct 4 2004    Anand   1.4 dev - Use cPickle instead
                          of pickle.
    Nov 19 2004   Anand   Fixed bugs in read/write of
                          project files.
    Aug 2 2005    Anand   Changed binary protocol from pickle
                          to marshal. However most functions
                          still retain the 'pickle tag :-) .
                          This was because the config object
                          was not getting pickled, but was getting
                          marshalled fine. This also fixes
                          the problem with reading project files.
  Jan 10 2006     Anand   Converted from dos to unix format (removed Ctrl-Ms).
                          
"""

import os
import cPickle, pickle
import marshal
import zlib
import shelve

from shutil import copy
from common import *

HARVESTMAN_XML_HEAD1="""<?xml version=\"1.0\" encoding=\"UTF-8\"?>"""
HARVESTMAN_XML_HEAD2="""<!DOCTYPE HarvestManProject SYSTEM \"HarvestManProject.dtd\">"""

#=====Start Browser page macro strings ================#
HARVESTMAN_SIG="Daddy Long Legs"

HARVESTMAN_PROJECTINFO="""\
<TR align=center>
    <TD>
    %(PROJECTNAME)s
    </TD>
    <TD>&middot;
    <!-- PROJECTPAGE --><A HREF=\"%(PROJECTSTARTPAGE)s\"><!-- END -->
    <!-- PROJECTURL -->%(PROJECTURL)s<!-- END -->
        </A>
    </TD>
</TR>"""

HARVESTMAN_BOAST="""HarvestMan is an easy-to-use website copying utility. It allows you to download a website in the World Wide Web from the Internet to a local directory. It retrieves html, images, and other files from the remote server to your computer. It builds the local directory structures recursively, and rebuilds links relatively so that you can browse the local site without again connecting to the internet. The robot allows you to customize it in a variety of ways, filtering files based on file extensions/websites/keywords. The robot is customizable by using a configuration file. The program is completely written in Python."""

HARVESTMAN_KEYWORDS="""HarvestMan, HARVESTMAN, HARVESTMan, offline browser, robot, web-spider, website mirror utility, aspirateur web, surf offline, web capture, www mirror utility, browse offline, local  site builder, website mirroring, aspirateur www, internet grabber, capture de site web, internet tool, hors connexion, windows, windows 95, windows 98, windows nt, windows 2000, python apps, python tools, python spider"""

HARVESTMAN_CREDITS="""\
&copy; 2004-2005, Anand B Pillai. """


HARVESTMAN_BROWSER_CSS="""\
body {
    margin: 0;
    padding: 1;
    margin-bottom: 15px;
    margin-top: 15px;
    background: #678;
}
body, td {
    font: 14px Arial, Times, sans-serif;
    }

#subTitle {
    background: #345;  color: #fff;  padding: 4px;  font-weight: bold;
    }

#siteNavigation a, #siteNavigation .current {
    font-weight: bold;  color: #448;
    }
#siteNavigation a:link    { text-decoration: none; }
#siteNavigation a:visited { text-decoration: none; }

#siteNavigation .current { background-color: #ccd; }

#siteNavigation a:hover   { text-decoration: none;  background-color: #fff;  color: #000; }
#siteNavigation a:active  { text-decoration: none;  background-color: #ccc; }


a:link    { text-decoration: underline;  color: #00f; }
a:visited { text-decoration: underline;  color: #000; }
a:hover   { text-decoration: underline;  color: #c00; }
a:active  { text-decoration: underline; }

#pageContent {
    clear: both;
    border-bottom: 6px solid #000;
    padding: 10px;  padding-top: 20px;
    line-height: 1.65em;
    background-image: url(backblue.gif);
    background-repeat: no-repeat;
    background-position: top right;
    }

#pageContent, #siteNavigation {
    background-color: #ccd;
    }


.imgLeft  { float: left;   margin-right: 10px;  margin-bottom: 10px; }
.imgRight { float: right;  margin-left: 10px;   margin-bottom: 10px; }

hr { height: 1px;  color: #000;  background-color: #000;  margin-bottom: 15px; }

h1 { margin: 0;  font: 14px \"Monotype Corsiva\", Times, Arial;
font-weight: bold;  font-size: 2em; }
h2 { margin: 0;  font-weight: bold;  font-size: 1.6em; }
h3 { margin: 0;  font-weight: bold;  font-size: 1.3em; }
h4 { margin: 0;  font-weight: bold;  font-size: 1.18em; }

.blak { background-color: #000; }
.hide { display: none; }
.tableWidth { min-width: 400px; }

.tblRegular       { border-collapse: collapse; }
.tblRegular td    { padding: 6px;  background-image: url(fade.gif);  border: 2px solid #99c; }
.tblHeaderColor, .tblHeaderColor td { background: #99c; }
.tblNoBorder td   { border: 0; }"""

HARVESTMAN_BROWSER_TABLE1="""\
<table width=\"76%\" border=\"0\" align=\"center\" cellspacing=\"0\" cellpadding=\"3\" class=\"tableWidth\">
    <tr>
    <td id=\"subTitle\">HARVESTMan Internet Spider - Website Copier</td>
    </tr>
</table>"""

HARVESTMAN_BROWSER_HEADER="Index of Downloaded Sites:"

HARVESTMAN_BROWSER_TABLE2= """\
<table width=\"76%(PER)s\" border=\"0\" align=\"center\" cellspacing=\"0\" cellpadding=\"0\" class=\"tableWidth\">
<tr class=\"blak\">
<td>
    <table width=\"100%(PER)s\" border=\"0\" align=\"center\" cellspacing=\"1\" cellpadding=\"0\">
    <tr>
    <td colspan=\"6\">
        <table width=\"100%(PER)s\" border=\"0\" align=\"center\" cellspacing=\"0\" cellpadding=\"10\">
        <tr>
        <td id=\"pageContent\">
<!-- ==================== End prologue ==================== -->

    <meta name=\"generator\" content=\"HARVESTMAN Internet Spider Version %(VERSION)s \">
    <TITLE>Local index - HarvestMan</TITLE>
</HEAD>
<h1 ALIGN=left><u>%(HEADER)s</i></h1>
    <TABLE BORDER=\"0\" WIDTH=\"100%(PER)s\" CELLSPACING=\"1\" CELLPADDING=\"0\">
    <BR>
        <TR align=center>
            <TD>
            %(PROJECTNAME)s
            </TD>
            <TD>&middot;
                <!-- PROJECTPAGE --><A HREF=\"%(PROJECTSTARTPAGE)s\"><!-- END -->
                    <!-- PROJECTURL -->%(PROJECTURL)s<!-- END -->
                </A>
            </TD>
        </TR>
    </TABLE>
    <BR>
    <BR>
    <BR>
    <H6 ALIGN=\"RIGHT\">
    <I>Mirror and index made by HarvestMan Web Crawler [ABP 2006]</I>
    </H6>
<!-- ==================== Start epilogue ==================== -->
    </td>
    </tr>
    </table>
    </td>
    </tr>
    </table>
</td>
</tr>
</table>"""

HARVESTMAN_BROWSER_TABLE3="""\
<table width=\"76%(PER)s\" border=\"0\" align=\"center\" valign=\"bottom\" cellspacing=\"0\" cellpadding=\"0\">
    <tr>
    <td id=\"footer\"><small>%(CREDITS)s </small></td>
    </tr>
</table>"""

HARVESTMAN_CACHE_README="""\
This directory contains important cache information for HarvestMan.
This information is used by HarvestMan to update the project files.
If you delete this directory or its contents, the project update/caching
mechanism wont work.

"""

#=====End Browser page macro strings ==============#


class HarvestManSerializerError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

def testdump():
    """ For timing the dump method. """

    global obj
    try:
        marshal.dump(obj, open('cache1.hmc','wb'))
    except Exception, e:
        print e
        
    return -1

class HarvestManSerializer(object):

    def __init__(self):
        pass

    def dump(self, obj, filename):
        """ dump method similar to pickle. The main difference is that
        this method accepts a filename string rather than a file
        stream as pickle does """

        try:
            marshal.dump(obj, open(filename,'wb'))
        except Exception, e:
            raise HarvestManSerializerError, str(e)
            return -1

        return 0

    def load(self, filename):
        """ load method similar to pickle. The main difference is that
        this method accepts a filename string rather than a file
        stream as pickle does """

        try:
            obj = marshal.load(open(filename,'rb'))
        except Exception, e:
            raise HarvestManSerializerError, str(e)            

        return obj

class HarvestManCacheManager(object):
    """ Utility class to read/write project cache files """

    def __init__(self, filename):
        self.__cachefilename = filename
        pass

    def read_project_cache(self):
        """ Try to read the project cache file """

        # Get cache filename
        if not os.path.exists(self.__cachefilename):
            moreinfo("Project cache not found")
            return None

        cfg = GetObject('config')
        if cfg.cachefileformat == 'pickled':
            return self.__read_pickled_cache_file()
        elif cfg.cachefileformat == 'dbm':
            return self.__read_dbm_cache_file()

    def __read_pickled_cache_file(self):

        cache_obj = None
        try:
            pickler = HarvestManSerializer()
            cache_obj = pickler.load(self.__cachefilename)
            for d in cache_obj.values():
                if 'data' in d and d['data']:
                    d['data']=zlib.decompress(d['data'])
            
        except HarvestManSerializerError, e:
            print e
            return None

        return cache_obj

    def __read_dbm_cache_file(self):

        cache_obj = shelve.open(self.__cachefilename)
        return cache_obj    

    def write_project_cache(self, cache_obj, format):

        cachedir = os.path.dirname(self.__cachefilename)
        try:
            if not os.path.isdir(cachedir):
                if not os.path.exists(cachedir):
                    os.makedirs(cachedir)
                    extrainfo('Created cache directory => ', cachedir)
        except OSError, e:
            debug('OS Exception ', e)
            return -1

        # If file already exists, shred it
        if os.path.exists(self.__cachefilename):
            try:
                os.remove(self.__cachefilename)
            except OSError, e:
                print e
                return -1

        # Copy a readme.txt file to the cache directory
        readmefile = os.path.join(cachedir, "Readme.txt")
        try:
            fs=open(readmefile, 'w')
            fs.write(HARVESTMAN_CACHE_README)
            fs.close()
        except Exception, e:
            debug(str(e))

        if format == 'pickled':
            return self.__write_pickled_cache_file(cache_obj)
        elif format == 'dbm':
            return self.__write_dbm_cache_file(cache_obj)

        return -1

    def __write_pickled_cache_file(self, cache_obj):

        try:
            for d in cache_obj.values():
                if 'data' in d and d['data']:
                    d['data']=zlib.compress(d['data'])

            pickler = HarvestManSerializer()
            pickler.dump( cache_obj, self.__cachefilename)
        except HarvestManSerializerError, e:
            print e
            return -1

        return 0

    def __write_dbm_cache_file(self, cacheobj):

        try:
            for d in cacheobj.values():
                if 'data' in d and d['data']:
                    d['data']=zlib.compress(d['data'])        
        
            shelf = shelve.open(self.__cachefilename)
            for url,values in cacheobj.items():
                shelf[url] = values

            shelf.close()

            return 0
        except Exception, e:
            print e
            return -1

class HarvestManProjectManager(object):
    """ Utility class to read/write project files """

    def __init__(self):
        pass

    def write_project(self, mode='pickled'):
        """ Write project files """

        moreinfo('Writing Project Files...')

        if mode == 'pickled':
            self.__write_pickled_project_file()
        elif mode == 'xml':
            self.__write_xml_project_file()

    def read_project(self):
        """ Load an existing HarvestMan project file and
        crete dictionary for the passed config object """

        projectfile = GetObject('config').projectfile
        return self.__read_pickled_project_file(projectfile)

    def __read_pickled_project_file(self, projectfile):

        config = GetObject('config')

        try:
            pickler = HarvestManSerializer()
            d = pickler.load(projectfile)
            # Bugfix: Set the values on
            # config dictionary
            for key in config.keys():
                try:
                    config[key] = d[key]
                except:
                    pass

            config.fromprojfile = True

            return 0
        except HarvestManSerializerError, e:
            print e
            return -1

    def __write_pickled_project_file(self):

        cfg = GetObject('config')

        pckfile = os.path.join(cfg.basedir, cfg.project + '.hbp')
        
        if os.path.exists(pckfile):
            try:
                os.remove(pckfile)
            except OSError, e:
                print e
                return -1

        try:
            pickler = HarvestManSerializer()
            pickler.dump( cfg, pckfile)
        except HarvestManSerializerError, e:
            print 'PROJECT ERROR:', str(e)
            return -1

        moreinfo('Done.')
        
        return 0

class HarvestManBrowser(object):
    """ Utility class to write the project browse pages """

    def __init__(self):
        tq = GetObject('trackerqueue')
        self._projectstartpage = os.path.abspath(tq.get_base_urlobject().get_full_filename())
        self._projectstartpage = 'file://' + self._projectstartpage.replace('\\', '/')
        self._cfg = GetObject('config')

    def make_project_browse_page(self):
        """ This creates an xhtml page for browsing the downloaded html pages """

        if self._cfg.browsepage == 0:
            return

        if self.__add_project_to_browse_page() == -1:
            self.__make_initial_browse_page()

        # Open the browser page in the user's webbrowser
        info('Opening project in browser...')
        import webbrowser

        browsefile=os.path.join(self._cfg.basedir, 'index.html')
        try:
            webbrowser.open(browsefile)
            moreinfo('Done.')
        except webbrowser.Error, e:
            print e
        return 

    def __add_project_to_browse_page(self):
        """ Append new project information to existing project browser page """

        browsefile=os.path.join(self._cfg.basedir, 'index.html')
        if not os.path.exists(browsefile): return -1

        # read contents of file
        contents=''
        try:
            f=open(browsefile, 'r')
            contents=f.read()
            f.close()
        except IOError, e:
            print e
            return -1
        except OSError, e:
            print e
            return -1

        if not contents: return -1

        # See if this is a proper browse file created by HARVESTMan
        index = contents.find("HARVESTMan SIG:")
        if index == -1: return -1
        sig=contents[(index+17):(index+32)].strip()
        if sig != HARVESTMAN_SIG: return -1
        # Locate position to insert project info
        index = contents.find(HARVESTMAN_BROWSER_HEADER)
        if index == -1: return -1
        # get project page
        index=contents.rfind('<!-- PROJECTPAGE -->', index)
        if index == -1: return -1
        newindex=contents.find('<!-- END -->', index)
        projpage=contents[(index+29):(newindex-2)]
        # get project url
        index=contents.find('<!-- PROJECTURL -->', newindex)
        if index == -1: return -1

        newindex=contents.find('<!-- END -->', index)
        prjurl=contents[(index+19):newindex]

        if prjurl and prjurl==self._cfg.url:
            debug('Duplicate project!')
            if projpage:
                newcontents=contents.replace(projpage,self._projectstartpage)
            if prjurl:
                newcontents=contents.replace(prjurl, self._cfg.url)
            try:
                f=open(browsefile, 'w')
                f.write(newcontents)
                f.close()
            except OSError, e:
                print e
                return -1
        else:
            # find location of </TR> from this index
            index = contents.find('</TR>', newindex)
            if index==-1: return -1
            newprojectinfo = HARVESTMAN_PROJECTINFO % {'PROJECTNAME': self._cfg.project,
                                                       'PROJECTSTARTPAGE': self._projectstartpage,
                                                       'PROJECTURL' : self._cfg.url }
            # insert this string
            newcontents = contents[:index] + '\n' + newprojectinfo + contents[index+5:]
            try:
                f=open(browsefile, 'w')
                f.write(newcontents)
                f.close()
            except OSError, e:
                print e
                return -1

    def __make_initial_browse_page(self):
        """ This creates an xhtml page for browsing the downloaded
        files similar to HTTrack copier """

        debug('Making fresh page...')

        cfg = GetObject('config')
        browsefile=os.path.join(self._cfg.basedir, 'index.html')

        f=open(browsefile, 'w')
        f.write("<html xmlns=\"http://www.w3.org/1999/xhtml\" lang=\"en\">\n\n")
        f.write("<head>\n")
        f.write("\t<meta http-equiv=\"Content-Type\" content=\"text/html; charset=iso-8859-1\" />\n")
        f.write("\t<meta name=\"description\" content=\"" + HARVESTMAN_BOAST + "\" />\n")
        f.write("\t<meta name=\"keywords\" content=\"" + HARVESTMAN_KEYWORDS + "\" />\n")
        f.write("\t<title>Local index - HARVESTMAN Internet Spider</title>\n")
        f.write("<!-- Mirror and index made by HARVESTMAN Internet Spider/" + cfg.version + " [ABP, NK '2003] -->\n")
        f.write("<style type=\"text/css\">\n")
        f.write("<!--\n\n")
        f.write(HARVESTMAN_BROWSER_CSS)
        f.write("\n\n")
        f.write("// -->\n")
        f.write("</style>\n")
        f.write("</head>\n")
        f.write(HARVESTMAN_BROWSER_TABLE1)
        s=HARVESTMAN_BROWSER_TABLE2 % {'PER'    : '%',
                                         'VERSION': cfg.version,
                                         'HEADER' : HARVESTMAN_BROWSER_HEADER,
                                         'PROJECTNAME': self._cfg.project,
                                         'PROJECTSTARTPAGE': self._projectstartpage,
                                         'PROJECTURL' : self._cfg.url}
        f.write(s)
        f.write("<BR><BR><BR><BR>\n")
        f.write("<HR width=76%>\n")
        s=HARVESTMAN_BROWSER_TABLE3 % {'PER'    : '%',
                                         'CREDITS': HARVESTMAN_CREDITS }
        f.write(s)
        f.write("</body>\n")

        # insert signature
        sigstr = "<!-- HARVESTMan SIG: <" + HARVESTMAN_SIG + "> -->\n"
        f.write(sigstr)
        f.write("</html>\n")


if __name__=="__main__":
    pass



