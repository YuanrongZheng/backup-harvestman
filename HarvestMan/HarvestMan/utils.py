# -- coding: iso8859-1
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
"""

import os
import cPickle

from common import *

HARVESTMAN_XML_HEAD1="""<?xml version=\"1.0\" encoding=\"UTF-8\"?>"""
HARVESTMAN_XML_HEAD2="""<!DOCTYPE HarvestManProject SYSTEM \"HarvestManProject.dtd\">"""


class HarvestManPicklerError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class HarvestManPickler(object):

    def __init__(self):
        pass

    def dump(self, obj, filename, binary = False):
        """ dump method similar to pickle. The main difference is that
        this method accepts a filename string rather than a file
        stream as pickle does """

        import zlib

        # use zlib to compress pickled data before writing it
        # to the file.
        try:
            cstr = zlib.compress(cPickle.dumps(obj, binary))
            stream = open(filename, 'wb')
            stream.write(cstr)
            stream.close()
        except Exception, e:
            raise HarvestManPicklerError, str(e)
            return -1

        return 0

    def load(self, filename):
        """ load method similar to pickle. The main difference is that
        this method accepts a filename string rather than a file
        stream as pickle does """

        import zlib

        cstr=''
        try:
            stream  = open(os.path.abspath(filename), 'rb')
            cstr = stream.read()
            stream.close()
        except Exception, e:
            raise HarvestManPicklerError, str(e)
            return -1

        # use zlib to decompress the data before unpickling it.
        obj = None

        try:
            s = zlib.decompress(cstr)
            obj = cPickle.loads(s)
        except Exception, e:
            raise HarvestManPicklerError, str(e)            

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
            return

        cfg = GetObject('config')
        if cfg.cachefileformat == 'pickled':
            return self.__read_pickled_cache_file()
        elif cfg.cachefileformat == 'xml': # not supported
            return -1

        return None

    def __read_pickled_cache_file(self):

        cache_obj = None
        try:
            pickler = HarvestManPickler()
            cache_obj = pickler.load(self.__cachefilename)
        except HarvestManPicklerError, e:
            print e
            return None

        return cache_obj

    def write_project_cache(self, cache_obj, format='pickled'):

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
        elif format == 'xml':
            return self.__write_xml_cache_file(cache_obj)

        return -1

    def __write_pickled_cache_file(self, cache_obj):

        try:
            pickler = HarvestManPickler()
            pickler.dump( cache_obj, self.__cachefilename, False)
        except HarvestManPicklerError, e:
            print e
            return -1

        return 0

    def __write_xml_cache_file(self, cache_obj):

        cachedir = os.path.dirname(self.__cachefilename)
        # Copy the HarvestMan DTD from the installation
        dtdfile = os.path.join(cachedir, "HarvestManCache.dtd")

        configobj = GetObject('config')

        if not os.path.exists(dtdfile):
            try:
                import shutil
                shutil.copy("./HarvestManCache.dtd", dtdfile)
            except Exception, e:  # Catch all exceptions
                debug(str(e))

        try:
            fs = file(self.__cachefilename, 'w')
            fs.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            fs.write("<!DOCTYPE HarvestManCache SYSTEM \"HarvestManCache.dtd\">\n")        
            fs.write("<PROJECT Name=\"" + configobj.project + "\"" + " Starturl=\"" + configobj.url + "\">\n")
            # Write cache information for every file

            index = 0

            for d in cache_obj:
                filename = d['location']
                url = d['url']
                contentlen = d['content-length']
                # encrypt the checksum and write it in hex format
                # otherwise the xml file will look like garbage!
                md5checksum = d['checksum']

                # increment index
                index += 1
                fs.write("\t<file location=\"" + filename + "\"" + " index=\"" + str(index) + "\">\n")
                fs.write("\t<url>" + url + "</url>\n")
                fs.write("\t<content-length>" + str(contentlen) + "</content-length>\n")
                fs.write("\t<checksum>" + str(md5checksum) + "</checksum>\n")           
                fs.write("\t</file>\n")

            fs.write("</PROJECT>\n")
            fs.close()
        except Exception, e:
            print e
            return -1

        return 0

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

        # Find out if it is an XML project file
        # Read the first line and look for the xml specification
        try:
            pf = open( projectfile )
        except Exception, e:
            print e
            return -1

        line1, line2 = '', ''
        try:
            line1 = pf.readline().strip()
            line2 = pf.readline().strip()
            pf.close()
        except Exception, e:
            print e
            return -1

        isxml = False

        # Verify line1
        if line1 == HARVESTMAN_XML_HEAD1:
            # Verify line2
            if line2 == HARVESTMAN_XML_HEAD2:
                isxml = True

        if isxml:
            # XML parsing code
            return self.__read_xml_project_file()
        else:
            return self.__read_pickled_project_file(projectfile)

        return -1

    def __read_xml_project_file(self):

        from HarvestManXMLParser import harvestManXMLParser

        parser = harvestManXMLParser()

        if parser.ParseProjectFile(GetObject('config').projectfile) != -1:
            return 0

        return -1

    def __read_pickled_project_file(self, projectfile):

        config = GetObject('config')

        try:
            pickler = HarvestManPickler()
            d = pickler.load(projectfile)
            # Bugfix: Set the values on
            # config dictionary
            for key in config.keys():
                config[key] = d[key]
                
            return 0
        except HarvestManPicklerError, e:
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
            # Bugfix: Pickling was not working since
            # pickle was not able to process config object
            # So convert it to a dictionary and dump it.
            d = dict(cfg)
            pickler = HarvestManPickler()
            pickler.dump( d, pckfile, True)
        except HarvestManPicklerError, e:
            print e
            return -1

        moreinfo('Done.')
        return 0

    def __write_xml_project_file(self):

        cfg = GetObject('config')

        # The project file is written directly to the basedir
        projfilename = os.path.join(cfg.basedir, cfg.project + '.hmp')

        # If file already exists, shred it
        if os.path.exists(projfilename):
            try:
                os.remove(projfilename)
            except OSError, e:
                print e
                return -1

        # Copy the HarvestMan DTD from the installation
        dtdfile = os.path.join(cfg.basedir, "HarvestManProject.dtd")
        if not os.path.exists(dtdfile):
            try:
                copy("./HarvestManProject.dtd", dtdfile)
            except:  # Catch all exceptions
                return -1

        extrainfo('Writing HarvestMan XML project file', projfilename, '...')
        # Write the xml project file

        try:
            fs=file(projfilename, 'w')
            fs.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            fs.write("<!DOCTYPE HarvestManProject SYSTEM \"HarvestManProject.dtd\">\n")
            fs.write("<PROJECT Name=\"" + cfg.project + "\">\n")
            fs.write("\t<URL Location=\"" + cfg.url + "\" />\n")
            fs.write("\t<BASEDIR Location=\"" + cfg.basedir + "\" />\n")

            for option in cfg.Options().keys():
                # We are writing the project file using old style config variables
                if option.find('.') != -1: continue
                # Skip URL, BASEDIR, PROJECT
                # Also skip any proxy password because of security reasons
                if option in ('URL', 'PROJECT', 'BASEDIR', 'PROXYPASSWD'): continue
                # For file type variables attribute name is Name, otherwise Value
                attrib=""
                if option in ('LOGFILE', 'URLSLISTFILE', 'ERRORFILE'):
                    attrib="Name"
                else:
                    attrib="Value"
                # Write the element and its attribute and its value
                if option == 'URLFILTER': value = cfg.urlfilter
                elif option == 'SERVERFILTER': value = cfg.serverfilter
                else: value = cfg.getVariable(option)
                fs.write("\t<" + option + " " + attrib + "=\"" + str(value) + "\" />\n")

                fs.write("</PROJECT>\n")
                fs.close()
                extrainfo('Done.')
        except Exception, e:
            extrainfo(e)
            return -1

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
        str=HARVESTMAN_BROWSER_TABLE2 % {'PER'    : '%',
                                         'VERSION': cfg.version,
                                         'HEADER' : HARVESTMAN_BROWSER_HEADER,
                                         'PROJECTNAME': self._cfg.project,
                                         'PROJECTSTARTPAGE': self._projectstartpage,
                                         'PROJECTURL' : self._cfg.url}
        f.write(str)
        f.write("<BR><BR><BR><BR>\n")
        f.write("<HR width=76%>\n")
        str=HARVESTMAN_BROWSER_TABLE3 % {'PER'    : '%',
                                         'CREDITS': HARVESTMAN_CREDITS }
        f.write(str)
        f.write("</body>\n")

        # insert signature
        sigstr = "<!-- HARVESTMan SIG: <" + HARVESTMAN_SIG + "> -->\n"
        f.write(sigstr)
        f.write("</html>\n")







