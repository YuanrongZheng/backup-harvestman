# -- coding: iso8859-1
""" HarvestManDataManager.py - Data manager module for HarvestMan.
    This software is part of the HarvestMan program.

    Author: Anand B Pillai (anandpillai at letterboxes dot org).
    
    Copyright (C) 2004-2005 Anand B Pillai.

    Created July 29 2003      Anand  Modifications for 1.1 release.
        (New module)

  Modification History

  Nov 30 2004        Anand       Many bug fixes in localizing links.
                                 1) Fix for replacing <base href="..."> links
                                    using regular expression.
                                 2) Modified links replacement to use regular
                                    expressions.
                                 3) Use url's type instead of checking is_image()
                                 to confirm image type.

"""
import os, sys
import time
import math
import binascii
import re

import threading as tg
# Utils
import utils

from urlthread import harvestManUrlThreadPool
from connector import *
from common import *

class harvestManDataManager(object):
    """ The data manager cum indexer class """

    def __init__(self):

        self._numfailed = 0
        self._projectcache = []
        self._downloaddict = { '_savedfiles': [],
                               '_deletedfiles': [],
                               '_failedurls' : [],
                               '_reposfiles' : [],
                               '_cachefiles': [],
                               '_invalidurls': [],
                               '_validurls' : [],
                             }
        # Config object
        self._cfg = GetObject('config')
        # Used for localizing links
        self._linksdict = {}
        # byte count
        self._bytes = 0L
        # Redownload flag
        self._redownload = False
        self._dataLock = tg.Condition(tg.RLock())        
        # Url thread group class for multithreaded downloads
        if self._cfg.usethreads:
            self._urlThreadPool = harvestManUrlThreadPool()
            self._urlThreadPool.spawn_threads()

    def get_proj_cache_filename(self):
        """ Return the cache filename for the current project """

        # Note that this function does not actually build the cache directory.
        # Get the cache file path
        cachedir = os.path.join(self._cfg.projdir, "hm-cache")
        cachefilename = os.path.join(cachedir, self._cfg.project + ".hmc")

        return cachefilename

    def get_links_dictionary(self):
        return self._linksdict

    def read_project_cache(self):
        """ Try to read the project cache file """

        # Get cache filename
        moreinfo('Reading Project Cache...')
        cachereader = utils.HarvestManCacheManager(self.get_proj_cache_filename())
        obj = cachereader.read_project_cache()

        if obj is not None:
            self._projectcache = obj

        return

    def write_file_from_cache(self, url):
        """ Write file from url cache. This
        works only if the cache dictionary of this
        url has a key named 'data' """

        # New feature in 1.4
        ok = False
        
        for x in self._projectcache:
            if x.has_key(intern('url')):
                if x[intern('url')] == url:
                    fileloc = x[intern('location')]
                    if not x.has_key(intern('data')):
                        break
                    else:
                        url_data = x[intern('data')]
                        if url_data:
                            # Write file
                            extrainfo("Updating file from cache=>", fileloc)
                            try:
                                f=open(fileloc, 'wb')
                                f.write(url_data)
                                f.close()
                                ok = True
                            except IOError, e:
                                debug('IO Exception', e)
                        break
                                
        return ok

    def is_url_cache_uptodate(self, url, filename, contentlen, urldata):
        """ Check with project cache and find out if the
        content needs update """

        # Sep 16 2003, fixed a bug in this, we need to check
        # the file existence also.

        # If page caching is not enabled, return False
        # straightaway!
        if not self._cfg.pagecache:
            return (False, False)

        # Return True if cache is uptodate(no update needed)
        # and Fals if cache is out-of-date(update needed)
        # NOTE: We are using an comparison of the md5 checksum of
        # the file's data with the md5 checksum of the cache file.
        if contentlen==0:
            return (False, False)

        # Look up the dictionary containing the url cache info
        import md5

        m1=md5.new()
        mdigest1=m1.update(urldata)
        digest1=m1.digest()

        # Assume that cache is not uptodate apriori
        uptodate=False
        keyfound = False
        fileverified=False

        # Reference to dictionary in the cache list
        cachekey = {}
        for x in self._projectcache:
            if x.has_key(intern('url')):
                if x[intern('url')] == url:
                    cachekey = x
                    keyfound = True
                    x[intern('updated')]=False

                    fileloc = x[intern('location')]
                    if os.path.exists(fileloc) and os.path.abspath(fileloc) == os.path.abspath(filename):
                        fileverified=True
			
                    if x.has_key(intern('checksum')):
                    	# This value is stored hex encrypted in the cache file
                   	 # (and hence the dictionary). In order to compare, we need
                    	# to decrypt it, (or we need to compare it with the encrypted
                    	# copy of the file digest, as we are doing now).

                    	cachemd5 = bin_decrypt(x[intern('checksum')])
                    	if binascii.hexlify(cachemd5) == binascii.hexlify(digest1) and fileverified:
                        	uptodate=True

                    	break
		    else:
			break

        # If cache is not updated, update all cache keys
        if not uptodate:
            cachekey[intern('checksum')] = bin_crypt(digest1)
            cachekey[intern('location')] = filename
            cachekey[intern('content-length')] = contentlen
            cachekey[intern('updated')] = True
            if self._cfg.datacache:
                cachekey['data'] = urldata

            # If key was not found, we need to create a new
            # entry and append it to the list, otherwise the
            # cache dictionary is modified in place.
            if not keyfound:
                cachekey[intern('url')] = url
                self._projectcache.append(cachekey)

        # If both checksums are equal, return True
        # else return False.
        # Modification (Oct 1 2004) - Combine
        # with fileverified boolean.
        return (uptodate, fileverified)

    def is_url_uptodate(self, url, filename, lmt, urldata):
        """ New function to check whether the url cache is out
        of date by comparing last modified time """

        # If page caching is not enabled, return False
        # straightaway!
        if not self._cfg.pagecache:
            return (False, False)

        # Assume that cache is not uptodate apriori
        uptodate=False
        keyfound = False
        fileverified=False

        # Reference to dictionary in the cache list
        cachekey = {}

        for x in self._projectcache:
            if x.has_key(intern('url')):
                if x['url'] == url:
                    cachekey = x
                    keyfound = True
                    x[intern('updated')]=False

                    fileloc = x[intern('location')]
                    if os.path.exists(fileloc) and os.path.abspath(fileloc) == os.path.abspath(filename):
                        fileverified=True

                    if x.has_key(intern('last-modified')):
                        # Get current modified time
                        cmt = x['last-modified']
                        # If the latest page has a modified time greater than this
                        # page is out of date, otherwise it is uptodate
                        if lmt<=cmt:
                            uptodate=True
                    else:
                        break

                    break

        # If cache is not updated, update all cache keys
        if not uptodate:
            cachekey[intern('location')] = filename
            cachekey[intern('last-modified')] = lmt
            cachekey[intern('updated')] = True
            if self._cfg.datacache:
                cachekey['data'] = urldata            
            # If key was not found, we need to create a new
            # entry and append it to the list, otherwise the
            # cache dictionary is modified in place.
            if not keyfound:
                cachekey[intern('url')] = url
                self._projectcache.append(cachekey)

        # If both checksums are equal, return True
        # else return False.
        # Modification (Oct 1 2004) - Combine
        # with fileverified boolean.        
        return (uptodate, fileverified)

    def conditional_cache_set(self):
        """ A utility function to conditionally enable/disable
        the cache mechanism """

        # If the cache file exists for this project, disable
        # cache, else enable it.
        cachefilename = self.get_proj_cache_filename()

        if os.path.exists(cachefilename) and os.path.getsize(cachefilename):
            self._cfg.pagecache = False
        else:
            self._cfg.pagecache = True

    def does_cache_need_update(self):
        """ Find out if project cache needs update """

        # If any of the dictionary entries has the key
        # value for 'updated' set to True, the cache needs
        # update, else not.
        needsupdate=False
        for x in self._projectcache:
            if x.has_key(intern('updated')):
                if x[intern('updated')]:
                    needsupdate=x[intern('updated')]
                    break

        return needsupdate

    def fill_project_cache(self, name, value, fileloc):
        """ This function fills the project cache from an
        existing project cache file """

        # if the tagname is 'location', add this entry to the list
        if name=='location':
            cachedict={}
            cachedict[intern(name)]=value
            self._projectcache.append(cachedict)
            return 0

        # Otherwise, lookup the location key in the list of dictionaries
        # and add this new name/value pair in the dictionary
        else:
            ok=False
            for x in self._projectcache:
                if x.has_key(intern('location')):
                    # We dont want to overwrite the key's value
                    if not x.has_key(intern(name)):
                        if x[intern('location')] == fileloc:
                            # Add the new key/value pair
                            ok=True
                            x[intern(name)]= value
                            break
        if ok:
            return 0
        else:
            return -1

    def post_download_setup(self):
        """ Actions to perform after project is complete """


        if self._cfg.retryfailed:
            self._numfailed = len(self._downloaddict['_failedurls'])
            moreinfo(' ')
            # try downloading again
            # mod: made this multithreaded
            if self._numfailed:
                moreinfo('Redownloading failed links...',)
                self._redownload=True

                for urlobj in self._downloaddict['_failedurls']:
                    self.download_url( urlobj )

        # bugfix: Moved the time calculation code here.
        if sys.platform == 'win32' or os.name=='nt':
            t2=time.clock()
        else:
            t2=time.time()

        self._cfg.endtime = t2

        # Write cache file
        if self._cfg.pagecache and self.does_cache_need_update():
            cachewriter = utils.HarvestManCacheManager( self.get_proj_cache_filename() )
            cachewriter.write_project_cache(self._projectcache)

        # localise downloaded file's links, dont do if jit localisation
        # is enabled.
        if self._cfg.localise and not self._cfg.jitlocalise:
            self.localise_links()

        #  Get handle to rules checker object
        ruleschecker = GetObject('ruleschecker')
        # dump downloaded urls to a text file
        if self._cfg.urlslistfile:
            # Get urls list file
            ruleschecker.dump_urls(self._cfg.urlslistfile)
        # dump url tree (dependency tree) to a file
        if self._cfg.urltreefile:
            self.dump_urltree(self._cfg.urltreefile)

        # print stats of the project
        nlinks, nservers, ndirs = ruleschecker.get_stats()
        nfailed = self._numfailed
        numstillfailed = len(self._downloaddict['_failedurls'])
        numfiles = len(self._downloaddict['_savedfiles'])
        numfilesinrepos = len(self._downloaddict['_reposfiles'])
        numfilesincache = len(self._downloaddict['_cachefiles'])

        numretried = self._numfailed  - numstillfailed
        fetchtime = float((math.modf((self._cfg.endtime-self._cfg.starttime)*100.0)[1])/100.0)

        statsd = { 'links' : nlinks,
                   'extservers' : nservers,
                   'extdirs' : ndirs,
                   'failed' : nfailed,
                   'fatal' : numstillfailed,
                   'files' : numfiles,
                   'filesinrepos' : numfilesinrepos,
                   'filesincache' : numfilesincache,
                   'retries' : numretried,
                   'fetchtime' : fetchtime,
                }

        self.print_project_info(statsd)

    def update_bytes(self, count):
        """ Update the global byte count """

        self._bytes += count

    def update_dead_links(self, url):
        """ Add this link to the 404 (dead links) database """

        try:
            self._downloaddict['_invalidurls'].index(url)
        except:
            self._downloaddict['_invalidurls'].append(url)

    def is_a_dead_link(self, url):
        """ Check whether the passed url is a dead (404) link """

        dead = False
        try:
            self._downloaddict['_invalidurls'].index( url )
            dead = True
        except:
            pass

        return dead

    def update_failed_files(self, urlObject):
        """ Add the passed information to the failed files list """

        if self._redownload: return -1

        try:
            self._downloaddict['_failedurls'].index(urlObject)
        except:
            self._downloaddict['_failedurls'].append(urlObject)

    def update_file_stats(self, urlObject, status):
        """ Add the passed information to the saved file list """

        if urlObject is None: return -1

        # Bug: we should be getting this url as rooturl and not
        # the base url of this url.
        filename, rooturl = urlObject.get_full_filename(), urlObject.get_full_url()

        ok=False

        # Status == 1 or 2 means look up in "_savedfiles"
        # Status == 3 means look up in "_reposfiles"
        # Status == 4 means look up in "_cachefiles"
        lookuplist=[]
        if status == 1 or status == 2:
            lookuplist = self._downloaddict['_savedfiles']
        elif status == 3:
            lookuplist = self._downloaddict['_reposfiles']
        elif status == 4:
            lookuplist = self._downloaddict['_cachefiles']            
        else:
            return -1

        for x in lookuplist:
            # Already added
            if x[0] == filename:
                ok=True
                break

        if not ok:
            lookuplist.append( filename )

    def update_links(self, filename, urlobj):
        """ Update the links dictionary for this html file """

        if self._linksdict.has_key(filename):
            links = self._linksdict[filename]
            try:
                links.index(urlobj)
            except:
                links.append(urlobj)
        else:
            l=[urlobj]
            self._linksdict[filename] = l

    def thread_download(self, urlObj):
        """ Download this url object in a separate thread """

        # Add this task to the url thread pool
        if self._cfg.usethreads:
            self._urlThreadPool.push( urlObj )

    def has_download_threads(self):
        """ Return true if there are any download sub-threads
        running, else return false """

        if self._cfg.usethreads:
            num_threads = self._urlThreadPool.has_busy_threads()
            if num_threads:
                return True

        return False

    def last_download_thread_report_time(self):
        """ Get the time stamp of the last completed
        download (sub) thread """

        if self._cfg.usethreads:
            return self._urlThreadPool.last_thread_report_time()
        else:
            return 0

    def kill_download_threads(self):
        """ Terminate all the download threads """

        if self._cfg.usethreads:
            self._urlThreadPool.end_all_threads()

    def create_local_directory(self, urlObj):
        """ Create the directories on the disk for downloading
        this url object """

        directory =  urlObj.get_local_directory()
        try:
            if not os.path.exists( directory ):
                os.makedirs( directory )
                extrainfo("Created => ", directory)
            return 0
        except OSError, e:
            moreinfo("OS Exception", e)
            return -1

        return 0

    def download_url(self, urlobj):

        try:
            data=""

            if not self._cfg.usethreads or urlobj.is_webpage():
                server = urlobj.get_domain()
                conn_factory = GetObject('connectorfactory')
                # This call will block if we exceed the number of connections
                conn = conn_factory.create_connector( server )

                res = conn.save_url( urlobj )
                
                conn_factory.remove_connector(server)

                # Return values for res
                # 0 => error, file not downloaded
                # 1 => file downloaded ok
                # 2 => file downloaded with filename modification
                # 3 => file was not downloaded because cache was uptodate
                # 4 => file was copied from cache, since cache was uptodate
                # but file was deleted.
                # 5 => Some rules related to file content/mime-type
                # prevented file download.
                filename = urlobj.get_full_filename()
                if res:
                    if res==2:
                        # There was a filename modification, so get the new filename
                        filename = GetObject('modfilename')
                    else:
                        filename = urlobj.get_full_filename()

                    if res==1:
                        moreinfo("Saved to ", filename)

                    self.update_file_stats( urlobj, res )

                    # Get the data fetched and return it
                    if urlobj.is_webpage():
                        data=conn.get_data()
                else:
                    fetchurl = urlobj.get_full_url()
                    extrainfo( "Failed to download url", fetchurl)
                    # We dont re-fetch fatal error urls
                    err = conn.get_error()

                    if not err['fatal']:
                        self.update_failed_files(urlobj)
            else:
                self.thread_download( urlobj )

            return data

        finally:
            pass

    def is_file_downloaded(self, filename):
        """ Find if the <filename> is present in the
        saved files list """

        try:
            self._downloaddict['_savedfiles'].index(filename)
            return True
        except ValueError:
            return False
        
    def localise_links(self):
        """ Localise all links (urls) of the downloaded html pages """

        info('Localising links of downloaded web pages...',)

        links_dict = self.get_links_dictionary()

        for filename in links_dict.keys():
            links = links_dict[filename]
            info('Localizing links for',filename)
            self.localise_file_links(filename, links)

        extrainfo('Localised links of',len(links_dict),'web pages.')

    def localise_file_links(self, filename, links):
        """ Localise links for this file """

        data=''
        try:
            fw=open(filename)
            data=fw.read()
            fw.close()
        except (OSError, IOError),e:
            return -1

        # MOD: Replace any <base href="..."> line
        basehrefre = re.compile(r'<base href=.*>', re.IGNORECASE)
        if basehrefre.search(data):
            data = re.sub(basehrefre, '', data)
        
        for u in links:
            if u is None: continue
            
            url_object = u
            typ = url_object.get_type()

            # MOD: Check type instead of
            # using 'is_image' method.
            if url_object.is_image():
                http_str="src"
            else:
                http_str="href"
            
            v = url_object.get_url()

            # bug fix, dont localize cgi links
            if typ != 'base':
                if url_object.is_cgi() or not url_object.is_filename_url():
                    continue
                
                fullfilename = os.path.abspath( url_object.get_full_filename() )
                urlfilename=''

                # Modification: localisation w.r.t relative pathnames
                if self._cfg.localise==2:
                    urlfilename = url_object.get_relative_filename()
                elif self._cfg.localise==1:
                    urlfilename = fullfilename

                try:
                    oldnewmappings = GetObject('oldnewmappings')
                    newfilename = oldnewmappings[fullfilename]
                    if self._cfg.localise==2:
                        urlfilename = (os.path.split(newfilename))[1]
                    elif self._cfg.localise==1:
                        urlfilename = os.path.abspath(newfilename)
                except KeyError:
                    urlfilename = urlfilename

                # replace '\\' with '/'
                urlfilename = urlfilename.replace('\\','/')

                newurl=''
                oldurl=''
            
                # If we cannot get the filenames, replace
                # relative url paths will full url paths so that
                # the user can connect to them.
                if not os.path.exists(fullfilename):
                    # for relative links, replace it with the
                    # full url path
                    fullurlpath = url_object.get_full_url_sans_port()
                    newurl = "href=\"" + fullurlpath + "\""
                else:
                    # replace url with urlfilename
                    if typ == 'anchor':
                        anchor_part = url_object.get_anchor()
                        urlfilename = "".join((urlfilename, anchor_part))
                        v = "".join((v, anchor_part))

                    if self._cfg.localise == 1:
                        newurl= "".join((http_str, "=\"", "file://", urlfilename, "\""))
                    else:
                        newurl= "".join((http_str, "=\"", urlfilename, "\""))

            else:
                newurl="".join((http_str,"=\"","\""))

            oldurl = "".join((http_str, "=\"", v, "\""))
            oldurlre = re.compile("".join((http_str,'=','\\"?',v,'\\"?')))

            # Get the location of the link in the file
            try:
                if oldurl != newurl:
                    data = re.sub(oldurlre, newurl, data)
            except:
                continue

        try:
            fw=open(filename, 'w')
        except IOError, e:
            debug('IOException: ', str(e))
            return -1

        fw.write(data)
        fw.close()

    def print_project_info(self, statsd):
        """ Print project information """

        nlinks = statsd['links']
        nservers = statsd['extservers'] + 1
        nfiles = statsd['files']
        ndirs = statsd['extdirs'] + 1
        numfailed = statsd['failed']
        nretried = statsd['retries']
        fatal = statsd['fatal']
        fetchtime = statsd['fetchtime']
        nfilesincache = statsd['filesincache']
        nfilesinrepos = statsd['filesinrepos']

        # Bug fix, download time to be calculated
        # precisely...

        dnldtime = fetchtime

        strings = [('link', nlinks), ('server', nservers),
                   ('file', nfiles), ('file', nfilesinrepos),
                   ('directory', ndirs), ('link', numfailed), ('link', fatal),
                   ('link', nretried), ('file', nfilesincache) ]

        fns = map(plural, strings)
        info(' ')

        if fetchtime and nfiles:
            fps = (float(nfiles/dnldtime))
            fps = float((math.modf(fps*100.0))[1]/100.0)
        else:
            fps=0.0

        bytes = self._bytes

        ratespec='KB/sec'
        if bytes and dnldtime:
            bps = (float(bytes/dnldtime))/100.0
            bps = float((math.modf(bps*100.0))[1]/1000.0)
            if bps<1.0:
                bps *= 1000.0
                ratespec='bytes/sec'
        else:
            bps = 0.0

        self._cfg = GetObject('config')

        info('HarvestMan mirror',self._cfg.project,'completed in',fetchtime,'seconds.')
        if nlinks: info(nlinks,fns[0],'scanned in',nservers,fns[1],'.')
        else: info('No links parsed.')
        if nfiles: info(nfiles,fns[2],'written.')
        else:info('No file written.')
        
        if nfilesinrepos:
            info(nfilesinrepos,fns[3],wasOrWere(nfilesinrepos),'already uptodate in the repository for this project and',wasOrWere(nfilesinrepos),'not updated.')
        if nfilesincache:
            info(nfilesincache,fns[8],wasOrWere(nfilesincache),'updated from the project cache.')
            
        if fatal: info(fatal,fns[6],'had fatal errors and failed to download.')
        if bytes: info(bytes,'bytes received at the rate of',bps,ratespec,'.\n')

        nlocked = GetObject('trackerqueue').get_locked_instances()

        # get current time stamp
        s=time.localtime()

        tz=(time.tzname)[0]

        format='%b %d %Y '+tz+' %H:%M:%S'
        tstamp=time.strftime(format, s)
        # Write stats to a stats file
        statsfile = self._cfg.project + '.hst'
        statsfile = os.path.abspath(os.path.join(self._cfg.projdir, statsfile))
        print 'Writing stats file ', statsfile , '...'
        # Append to files contents
        sf=open(statsfile, 'a')

        # Write url, file count, links count, time taken,
        # files per second, failed file count & time stamp
        infostr='url:'+self._cfg.url+','
        infostr +='files:'+str(nfiles)+','
        infostr +='links:'+str(nlinks)+','
        infostr +='dirs:'+str(ndirs)+','
        infostr +='failed:'+str(numfailed)+','
        infostr +='refetched:'+str(nretried)+','
        infostr +='fatal:'+str(fatal)+','
        infostr +='elapsed:'+str(fetchtime)+','
        infostr +='fps:'+str(fps)+','
        infostr +='bps:'+str(bps)+','
        infostr +='timestamp:'+tstamp
        infostr +='\n'

        sf.write(infostr)
        sf.close()

        print 'Done.'

    def dump_urltree(self, urlfile):
        """ Dump url tree to a file """

        # This function provides a little
        # more functionality than the plain
        # dump_urls in the rules module.
        # This creats an html file with
        # each url and its children below
        # it. Each url is a hyperlink to
        # itself on the net if the file
        # is an html file.

        try:
            if os.path.exists(urlfile):
                os.remove(urlfile)
        except OSError, e:
            print e

        moreinfo('Dumping url tree to file', urlfile)
        fextn = ((os.path.splitext(urlfile))[1]).lower()        
        
        try:
            f=open(urlfile, 'w')
            if fextn in ('', '.txt'):
                self.dump_urltree_textmode(f)
            elif fextn in ('.htm', '.html'):
                self.dump_urltree_htmlmode(f)
            f.close()
        except Exception, e:
            print e
            return -1

        debug("Done.")

    def dump_urltree_textmode(self, stream):
        """ Dump urls in text mode """

        linksdict = self.get_links_dictionary()
        
        for f in linksdict.keys ():
            idx = 0
            links = linksdict[f]
            
            for link in links:
                if not link: continue

                # Get base link, only for first
                # child url, since base url will
                # be same for all child urls.
                if idx==0:
                    base_url = link.get_base_urlobject().get_full_url()
                    stream.write(base_url + '\n')

                childurl = link.get_full_url()
                if childurl:
                    stream.write("".join(('\t',childurl,'\n')))

                idx += 1


    def dump_urltree_htmlmode(self, stream):
        """ Dump urls in html mode """

        linksdict = self.get_links_dictionary()

        # Write html header
        stream.write('<html>\n')
        stream.write('<head><title>')
        stream.write('Url tree generated by HarvestMan - Project %s'
                     % GetObject('config').project)
        stream.write('</title></head>\n')

        stream.write('<body>\n')

        stream.write('<p>\n')
        stream.write('<ol>\n')
        
        for f in linksdict.keys ():
            idx = 0
            links = linksdict[f]
            
            for link in links:
                if not link: continue

                # Get base link, only for first
                # child url, since base url will
                # be same for all child urls.
                if idx==0:
                    base_url = link.get_base_urlobject().get_full_url()
                    stream.write('<li>')                    
                    stream.write("".join(("<a href=\"",base_url,"\"/>",base_url,"</a>")))
                    stream.write('</li>\n')
                    stream.write('<p>\n')
                    stream.write('<ul>\n')
                                 
                childurl = link.get_full_url()
                if childurl:
                    stream.write('<li>')
                    stream.write("".join(("<a href=\"",childurl,"\"/>",childurl,"</a>")))
                    stream.write('</li>\n')                    

                idx += 1                


            # Close the child list
            stream.write('</ul>\n')
            stream.write('</p>\n')
            
        # Close top level list
        stream.write('</ol>\n')        
        stream.write('</p>\n')
        stream.write('</body>\n')
        stream.write('</html>\n')


class harvestManController(tg.Thread):
    """ A controller class for managing exceptional
    conditions such as file limits. Right now this
    is written with the sole aim of managing file
    & time limits, but could get extended in future
    releases. """

    # NOTE: This class's object does not get registered
    def __init__(self):
        self._dmgr = GetObject('datamanager')
        self._cfg = GetObject('config')
        self._exitflag = False
        tg.Thread.__init__(self, None, None, 'HarvestMan Control Class')

    def run(self):
        """ Run in a loop looking for
        exceptional conditions """

        while not self._exitflag:
            # Wake up every second and look
            # for exceptional conditions
            time.sleep(1.0)
            # self.__check_terminate_condition()
            self.__manage_time_limits()
            self.__manage_file_limits()

    def stop(self):
        """ Stop this thread """

        self._exitflag = True

    def terminator(self):
        """ This function terminates HarvestMan """
        
        # Get tracker queue object
        tq = GetObject('trackerqueue')
        tq.terminate_threads()
            
    def __check_terminate_condition(self):
        """ Check terminate condition on the config object """

        # If someone set the terminate flag in
        # config object, return true straight away.
        # This is the most easy way to signal program
        # exit.

        if self._cfg.terminate:
            self.terminator()
        
    def __manage_time_limits(self):
        """ Manage limits on time for the project """

        # If time limit is not set, return
        if self._cfg.timelimit == -1:
            return -1
        
        if sys.platform == 'win32' or os.name=='nt':
            t2=time.clock()
        else:
            t2=time.time()

        timediff = float((math.modf((t2-self._cfg.starttime)*100.0)[1])/100.0)
        timemax = self._cfg.timelimit
        
        if timediff >= timemax -1:
            moreinfo('Specified time limit of',timemax ,'seconds reached!')            
            self.terminator()

    def __manage_file_limits(self):
        """ Manage limits on maximum file count """

        ddict = self._dmgr._downloaddict
        
        lsaved = len(ddict['_savedfiles'])
        lmax = self._cfg.maxfiles

        if lsaved < lmax:
            return -1
        
        if lsaved == lmax:
            moreinfo('Specified file limit of',lmax ,'reached!')
            self.terminator()
            
        # see if some tracker still managed to download
        # files while we were killing, then delete them!
        if lsaved > lmax:
            diff = lsaved - lmax
            savedcopy = (ddict['_savedfiles'])[0:]

            for x in range(0, diff):
                # 2 bugs: fixed a bug where the deletion
                # was not controlled
                lastfile = savedcopy[lsaved - x -1]

                # sometimes files may not be there, attempt
                # to delete only if file is there (makes sense)
                if os.path.exists(lastfile):
                    try:
                        extrainfo('Deleting file ', lastfile)
                        os.remove(lastfile)
                        (ddict['_deletedfiles']).append(lastfile)
                        ddict['_savedfiles'].remove(lastfile)
                    except (OSError, IndexError, ValueError), e:
                        print e

        return 0

                    
                
    


