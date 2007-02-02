# -- coding: latin-1
""" pageparser.py - Module to parse an html page and
    extract its links. This software is part of the
    HarvestMan program.

    Author: Anand B Pillai (anandpillai at letterboxes dot org).
    
    For licensing information see the file LICENSE.txt that
    is included in this distribution.

    Dependency
    ==========

    Jun 14 2004       Anand          1.3.9 release.
    May 14 2005       Anand          1.4.1 - Replaced parser
                                     with one derived from SGMLParser
                                     instead of htmlparser. Discontinued
                                     usage of HTML tidy.

                                     [Original code of SGMLParser derived
                                     parser, courtesy Leonardo of BeautifulSoup
                                     module]

   Sep 1 2005       Anand            Made _handled, skip_re and query_re
                                     as class level members to optimize their
                                     usage.
   Jan 4 2006       Anand            Fixed a bug in duplicate links for anchor
                                     type links as part of EIAO ticket #74
                                     changes (random walk fix).
   Jan 8 2006       Anand            Updated this file from EIAO repository
                                     to get a few bug-fixes. Removed EIAO
                                     specific code.
   Jan 10 2006      John             Bugfix by John Kleven for query forms
                                     variable (changed skipqueryforms to getqueryforms
                                     and fixed filter_link method).
   Jan 10 2006      Anand            1. Converted from dos to unix format (removed
                                     Ctrl-Ms).
                                     2. Bugfix for 'link' type tags - Type should not
                                     be empty; set to 'normal'. Also added a
                                     'handled_rel_types' variable to hold the types
                                     handled inside <link.. type of tags. This bug
                                     was causing a number of web-page links to be
                                     reported as non-webpage links.

   Sep 26 2006    Anand              Fixed EIAO ticket #194 - added support for
                                     <area...> tags.
   Sep 29 2006    Anand              Partial fix for EIAO ticket #193 by adding support for
                                     META REFRESH tag - lack of this was causing
                                     www.um.lublin.pl to fail.

   Jan 2007       Anand              Complete support for META robot tags implemented.
                                     Requested by jim sloan of MCHS.
                                     
"""

from sgmllib import SGMLParser
from HTMLParser import HTMLParser

from common import *
import re

class CaselessDict(dict):

    def has_key(self, key):
        if key in self or key.lower() in self:
            return True
        return False
    
class harvestManSimpleParser(SGMLParser):
    """ An HTML/XHTML parser derived from SGMLParser """

    # Optimizations - put some of the data as
    # class level members.
    query_re = re.compile(r'[-.:_a-zA-Z0-9]*\?[-.:_a-zA-Z0-9]*=[-.a:_-zA-Z0-9]*')
    skip_re = re.compile(r'(javascript:)|(mailto:)|(news:)|(\?m=a)|(\?n=d)|(\?s=a)|(\?d=a)')

    handled = { 'a' : (('href', 'normal'), ('href', 'anchor')),
                'base': (('href', 'base'),),
                'frame': (('src', 'normal'),),
                'img' : (('src', 'image'),),
                'form' : (('action', 'form'),),
                'link' : (('href', 'normal'),),
                'body' : (('background', 'image'),),
                'script' : (('src', 'javascript'),),
                'applet' : (('codebase', 'appletcodebase'), ('code', 'javaapplet')),
                'area' : (('href', 'normal'),),
                'meta' : (('CONTENT','normal'),('content','normal'))
                }

    # Valid 'rel' values - Added Jan 10 06 -Anand
    handled_rel_types = ( 'stylesheet', )
    
    def __init__(self):
        self.links = []
        self.linkpos = {}
        self.images = []
        # Fix for <base href="..."> links
        self.base_href = False
        # Base url for above
        self.base = None
        # anchor links flag
        self._anchors = True
        # For META robots tag
        self.can_index = True
        self.can_follow = True
        SGMLParser.__init__(self)
        
    def save_anchors(self, value):
        """ Set the save anchor links flag """

        # Warning: If you set this to true, anchor links on
        # webpages will be saved as separate files.
        self._anchors = value

    def filter_link(self, link):
        """ Function to filter links, we decide here whether
        to handle certain kinds of links """

        if not link: return

        # ignore javascript links (From 1.2 version javascript
        # links of the form .js are fetched, but we still ignore
        # the actual javascript actions since there is no
        # javascript engine.)
        llink = link.lower()

        # Skip javascript, mailto, news and directory special tags.
        if self.skip_re.match(llink):
            return 1

        cfg = GetObject('config')

        # Check if we're accepting query style URLs
        if not cfg.getqueryforms and self.query_re.search(llink):
            return 1

        return 0

    def handle_anchor_links(self, link):
        """ Handle links of the form html#..."""

        # if anchor tag, then get rid of anchor #...
        # and only add the webpage link
        if not link: return

        # Need to do this here also
        self.check_add_link('anchor', link)

        # No point in getting #anchor sort of links
        # since they point to anchors in the same page

        # Jan 4 06: Fixed a bug here - This routine
        # was adding a lot of duplicate links. Made
        # it to call check_add_link instead of
        # adding directly.
        
        index = link.rfind('.html#')
        if index != -1:
            newhref = link[:(index + 5)]
            self.check_add_link('webpage', newhref)
            return 0
        else:
            index = link.rfind('.htm#')
            if index != -1:
                newhref = link[:(index + 4)]
                self.check_add_link('webpage', newhref)
            return 0

        return 1

    def unknown_starttag(self, tag, attrs):
        """ This method gives you the tag in the html
        page along with its attributes as a list of
        tuples """

        # We handle the following tags
        # a => hypertext links
        # img => image links
        # link => css/icon etc
        # form => cgi forms
        # body => for background images
        # frame => for redirects

        if not attrs: return
        isBaseTag = not self.base and tag == 'base'

        if tag in self.handled:

            d = CaselessDict(attrs)
            _values = (self.handled[tag])
            #print 'd', d, d.line, d.column

            link = ''

            for v in _values:
                key = v[0]
                typ = v[1]

                # If there is a <base href="..."> tag
                # set self.base_href
                if isBaseTag and key=='href':
                    self.base_href = True
                    try:
                        self.base = d[key]
                    except:
                        self.base_href = False
                        continue
                
                # if the link already has a value, skip
                # (except for applet tags)
                if tag != 'applet':
                    if link: continue

                if tag == 'link':
                    try:
                        # Fix - only reset typ if it is one
                        # of the valid handled rel types.
                        foundtyp = d['rel'].lower()
                        if foundtyp in self.handled_rel_types:
                            typ = foundtyp
                    except KeyError:
                        pass

                try:
                    if tag == 'meta':
                        # print 'D=>',d
                        # Handle meta tag for refresh
                        foundtyp = d.get('http-equiv','').lower()
                        if foundtyp.lower() == 'refresh':
                            link = d.get(key,'')
                            if not link: continue
                            # This will be of the form of either
                            # a time-gap (CONTENT="600") or a time-gap
                            # with a URL (CONTENT="0; URL=<url>")
                            items = link.split(';')
                            if len(items)==1:
                                # Only a time-gap, skip it
                                continue
                            elif len(items)==2:
                                # Second one should be a URL
                                reqd = items[1]
                                if (reqd.find('URL') != -1 or reqd.find('url') != -1) and reqd.find('=') != -1:
                                    link = reqd.split('=')[1].strip()
                                else:
                                    continue
                        else:
                            # Handle robots meta tag
                            name = d.get('name','').lower()
                            if name=='robots':
                                robots = d.get('content','').lower()
                                # Split to ','
                                contents = [item.strip() for item in robots.split(',')]
                                # Check for nofollow
                                self.can_follow = not ('nofollow' in contents)
                                # Check for noindex
                                self.can_index = not ('noindex' in contents)
                            else:
                                continue

                    elif tag != 'applet':
                        link = d[key]
                    else:
                        link += d[key]
                        if key == 'codebase':
                            if link:
                                if link[-1] != '/':
                                    link += '/'
                            continue                                
                except KeyError:
                    continue

                # see if this link is to be filtered
                if self.filter_link(link):
                    continue

                # anchor links in a page should not be saved        
                index = link.find('#')
                if index != -1:
                    self.handle_anchor_links(link)
                else:
                    # append to private list of links
                    self.check_add_link(typ, link)

    def check_add_link(self, typ, link):
        """ To avoid adding duplicate links """

        f = False

        if typ == 'image':
            if not (typ, link) in self.images:
                # moredebug('Adding image ', link, typ)
                # print 'Adding image ', link, typ
                self.images.append((typ, link))
        elif not (typ, link) in self.links:
                # moredebug('Adding link ', link, typ)
                # print 'Adding link ', link, typ
                pos = self.getpos()
                self.links.append((typ, link))
                self.linkpos[(typ,link)] = (pos[0],pos[1])
                

    def add_tag_info(self, taginfo):
        """ Add new tag information to this object.
        This can be used to change the behavior of this class
        at runtime by adding new tags """

        # The taginfo object should be a dictionary
        # of the form { tagtype : (elementname, elementype) }

        # egs: { 'body' : ('background', 'img) }
        if type(taginfo) != dict:
            raise AttributeError, "Attribute type mismatch, taginfo should be a dictionary!"

        # get the key of the dictionary
        key = (taginfo.keys())[0]
        if len(taginfo[key]) != 2:
            raise ValueError, 'Value mismatch, size of tag tuple should be 2'

        # get the value tuple
        tagelname, tageltype = taginfo[key]

        # see if this is an already existing tagtype
        if key in self.handled.keys:
            _values = self.handled[key]

            f=0
            for index in xrange(len(_values)):
                # if the elementname is also
                # the same, just replace it.
                v = _values[index]

                elname, eltype = v
                if elname == tagelname:
                    f=1
                    _values[index] = (tagelname, tageltype)
                    break

            # new element, add it to list
            if f==0: _values.append((tagelname, tageltype))
            return 0

        else:
            # new key, directly modify dictionary
            elements = []
            elements.append((tagelname, tageltype))
            self.handled[key] = elements 

    def reset(self):
        SGMLParser.reset(self)

        self.base = None
        self.links = []
        self.images = []
        self.base_href = False
        self.base_url = ''
        self.can_index = True
        self.can_follow = True
        
    def base_url_defined(self):
        """ Return whether this url had a
        base url of the form <base href='...'>
        defined """

        return self.base_href

    def get_base_url(self):
        return self.base

class harvestManComplexParser(HTMLParser, harvestManSimpleParser):

    def handle_starttag(self, tag, attrs):
        harvestManSimpleParser.unknown_starttag(tag, attrs)


if __name__=="__main__":
    import os
    
    Initialize()

    cfg = GetObject('config')
    cfg.verbosity = 5
    cfg.forms = True
    
    p = harvestManComplexParser()
    urls = ['http://xerces.apache.org/xerces-j/apiDocs/index.html']

    for url in urls:
       if os.system('wget %s -O index.html' % url ) == 0:
           p.feed(open('index.html').read())
           #print p.links
           #p.reset()
           pass
                                   




