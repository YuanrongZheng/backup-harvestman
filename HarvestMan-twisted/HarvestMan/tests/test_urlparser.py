# -- coding: latin-1
""" Unit test for urlparser module

Created: Anand B Pillai <abpillai@gmail.com> Apr 17 2007

Copyright (C) 2007, Anand B Pillai.
"""

import test_base
import unittest
import sys, os

test_base.setUp()

class TestHarvestManUrlParser(unittest.TestCase):
    """ Unit test class for HarvestManUrlParser class """

    from urlparser import HarvestManUrlParser
    
    l = [ HarvestManUrlParser('http://www.yahoo.com/photos/my photo.gif'),
          HarvestManUrlParser('http://www.rediff.com:80/r/r/tn2/2003/jun/25usfed.htm'),
          HarvestManUrlParser('http://cwc2003.rediffblogs.com'),
          HarvestManUrlParser('/sports/2003/jun/25beck1.htm',
                              'generic', 0, 'http://www.rediff.com', ''),
          HarvestManUrlParser('ftp://ftp.gnu.org/pub/lpf.README'),
          HarvestManUrlParser('http://www.python.org/doc/2.3b2/'),
          HarvestManUrlParser('//images.sourceforge.net/div.png',
                              'image', 0, 'http://sourceforge.net', ''),
          HarvestManUrlParser('http://pyro.sourceforge.net/manual/LICENSE'),
          HarvestManUrlParser('python/test.htm', 'generic', 0,
                              'http://www.foo.com/bar/index.html', ''),
          HarvestManUrlParser('/python/test.css', 'generic',
                              0, 'http://www.foo.com/bar/vodka/test.htm', ''),
          HarvestManUrlParser('/visuals/standard.css', 'generic', 0,
                              'http://www.garshol.priv.no/download/text/perl.html'),
          HarvestManUrlParser('www.fnorb.org/index.html', 'generic',
                              0, 'http://pyro.sourceforge.net'),
          HarvestManUrlParser('http://profigure.sourceforge.net/index.html',
                              'generic', 0, 'http://pyro.sourceforge.net'),
          HarvestManUrlParser('#anchor', 'anchor', 0, 
                              'http://www.foo.com/bar/index.html'),
          HarvestManUrlParser('nltk_lite.contrib.fst.draw_graph.GraphEdgeWidget-class.html#__init__#index-after', 'anchor', 0, 'http://nltk.sourceforge.net/lite/doc/api/term-index.html'),              
          HarvestManUrlParser('../icons/up.png', 'image', 0,
                              'http://www.python.org/doc/current/tut/node2.html',
                              ''),
          HarvestManUrlParser('../eway/library/getmessage.asp?objectid=27015&moduleid=160',
                              'generic',0,'http://www.eidsvoll.kommune.no/eway/library/getmessage.asp?objectid=27015&moduleid=160'),
          HarvestManUrlParser('fileadmin/dz.gov.si/templates/../../../index.php',
                              'generic',0,'http://www.dz-rs.si'),
          HarvestManUrlParser('http://www.evvs.dk/index.php?cPath=26&osCsid=90207c4908a98db6503c0381b6b7aa70','form',True,'http://www.evvs.dk'),
          HarvestManUrlParser('http://arstechnica.com/reviews/os/macosx-10.4.ars'),
          HarvestManUrlParser('http://www.fylkesmannen.no/../fmt_hoved.asp',baseurl='http://www.fylkesmannen.no/osloogakershu')]
    
    def test_filename(self):
        d = os.path.abspath(os.curdir)
        
        assert(self.l[0].get_full_filename()==os.path.join(d, 'www.yahoo.com/photos/my photo.gif'))
        assert(self.l[1].get_full_filename()==os.path.join(d, 'www.rediff.com/r/r/tn2/2003/jun/25usfed.htm'))
        assert(self.l[2].get_full_filename()==os.path.join(d, 'cwc2003.rediffblogs.com/index.html'))
        assert(self.l[3].get_full_filename()==os.path.join(d, 'www.rediff.com/sports/2003/jun/25beck1.htm'))
        assert(self.l[4].get_full_filename()==os.path.join(d, 'ftp.gnu.org/pub/lpf.README'))
        assert(self.l[5].get_full_filename()==os.path.join(d, 'www.python.org/doc/2.3b2'))
        assert(self.l[6].get_full_filename()==os.path.join(d, 'images.sourceforge.net/div.png'))
        assert(self.l[7].get_full_filename()==os.path.join(d, 'pyro.sourceforge.net/manual/LICENSE'))
        assert(self.l[8].get_full_filename()==os.path.join(d, 'www.foo.com/bar/python/test.htm'))
        assert(self.l[9].get_full_filename()==os.path.join(d, 'www.foo.com/python/test.css'))
        assert(self.l[10].get_full_filename()==os.path.join(d, 'www.garshol.priv.no/visuals/standard.css'))
        assert(self.l[11].get_full_filename()==os.path.join(d, 'www.fnorb.org/index.html'))
        assert(self.l[12].get_full_filename()==os.path.join(d, 'profigure.sourceforge.net/index.html'))
        assert(self.l[13].get_full_filename()==os.path.join(d, 'www.foo.com/bar/index.html'))
        assert(self.l[14].get_full_filename()==os.path.join(d, 'nltk.sourceforge.net/lite/doc/api/nltk_lite.contrib.fst.draw_graph.GraphEdgeWidget-class.html'))
        assert(self.l[15].get_full_filename()==os.path.join(d, 'www.python.org/doc/current/icons/up.png'))
        assert(self.l[16].get_full_filename()==os.path.join(d, 'www.eidsvoll.kommune.no/eway/eway/library/getmessage.aspobjectid=27015&moduleid=160'))
        assert(self.l[17].get_full_filename()==os.path.join(d, 'www.dz-rs.si/index.php'))
        assert(self.l[18].get_full_filename()==os.path.join(d, 'www.evvs.dk/index.phpcPath=26&osCsid=90207c4908a98db6503c0381b6b7aa70'))
        assert(self.l[19].get_full_filename()==os.path.join(d, 'arstechnica.com/reviews/os/macosx-10.4.ars/index.html'))
        assert(self.l[20].get_full_filename()==os.path.join(d, 'www.fylkesmannen.no/fmt_hoved.asp'))
        
    def test_valid_filename(self):

        assert(self.l[0].validfilename=='my photo.gif')
        assert(self.l[1].validfilename=='25usfed.htm')
        assert(self.l[2].validfilename=='index.html')
        assert(self.l[3].validfilename=='25beck1.htm')
        assert(self.l[4].validfilename=='lpf.README')
        assert(self.l[5].validfilename=='2.3b2')
        assert(self.l[6].validfilename=='div.png')
        assert(self.l[7].validfilename=='LICENSE')
        assert(self.l[8].validfilename=='test.htm')
        assert(self.l[9].validfilename=='test.css')
        assert(self.l[10].validfilename=='standard.css')
        assert(self.l[11].validfilename=='index.html')
        assert(self.l[12].validfilename=='index.html')
        assert(self.l[13].validfilename=='index.html')
        assert(self.l[14].validfilename=='nltk_lite.contrib.fst.draw_graph.GraphEdgeWidget-class.html')
        assert(self.l[15].validfilename=='up.png')
        assert(self.l[16].validfilename=='getmessage.aspobjectid=27015&moduleid=160')
        assert(self.l[17].validfilename=='index.php')
        assert(self.l[18].validfilename=='index.phpcPath=26&osCsid=90207c4908a98db6503c0381b6b7aa70')
        assert(self.l[19].validfilename=='index.html')
        assert(self.l[20].validfilename=='fmt_hoved.asp')        

    def test_is_relative_path(self):

        assert(self.l[0].is_relative_path()==False)
        assert(self.l[1].is_relative_path()==False)
        assert(self.l[2].is_relative_path()==False)
        assert(self.l[3].is_relative_path()==True)
        assert(self.l[4].is_relative_path()==False)
        assert(self.l[5].is_relative_path()==False)
        assert(self.l[6].is_relative_path()==False)
        assert(self.l[7].is_relative_path()==False)
        assert(self.l[8].is_relative_path()==True)
        assert(self.l[9].is_relative_path()==True)
        assert(self.l[10].is_relative_path()==True)
        assert(self.l[11].is_relative_path()==False)
        assert(self.l[12].is_relative_path()==False)
        assert(self.l[13].is_relative_path()==False)
        assert(self.l[14].is_relative_path()==True)
        assert(self.l[15].is_relative_path()==True)
        assert(self.l[16].is_relative_path()==True)
        assert(self.l[17].is_relative_path()==True)
        assert(self.l[18].is_relative_path()==False)
        assert(self.l[19].is_relative_path()==False)
        assert(self.l[20].is_relative_path()==False)        
        
    def test_absolute_url(self):

        assert(self.l[0].get_full_url()=='http://www.yahoo.com/photos/my%20photo.gif')
        assert(self.l[1].get_full_url()=='http://www.rediff.com/r/r/tn2/2003/jun/25usfed.htm')
        assert(self.l[2].get_full_url()=='http://cwc2003.rediffblogs.com/')
        assert(self.l[3].get_full_url()=='http://www.rediff.com/sports/2003/jun/25beck1.htm')
        assert(self.l[4].get_full_url()=='ftp://ftp.gnu.org/pub/lpf.README')
        assert(self.l[5].get_full_url()=='http://www.python.org/doc/2.3b2')
        assert(self.l[6].get_full_url()=='http://images.sourceforge.net/div.png')
        assert(self.l[7].get_full_url()=='http://pyro.sourceforge.net/manual/LICENSE')
        assert(self.l[8].get_full_url()=='http://www.foo.com/bar/python/test.htm')
        assert(self.l[9].get_full_url()=='http://www.foo.com/python/test.css')
        assert(self.l[10].get_full_url()=='http://www.garshol.priv.no/visuals/standard.css')
        assert(self.l[11].get_full_url()=='http://www.fnorb.org/index.html')
        assert(self.l[12].get_full_url()=='http://profigure.sourceforge.net/index.html')
        assert(self.l[13].get_full_url()=='http://www.foo.com/bar/index.html')
        assert(self.l[14].get_full_url()=='http://nltk.sourceforge.net/lite/doc/api/nltk_lite.contrib.fst.draw_graph.GraphEdgeWidget-class.html')
        assert(self.l[15].get_full_url()=='http://www.python.org/doc/current/icons/up.png')
        assert(self.l[16].get_full_url()=='http://www.eidsvoll.kommune.no/eway/eway/library/getmessage.asp?objectid=27015&moduleid=160')
        assert(self.l[17].get_full_url()=='http://www.dz-rs.si/index.php')
        assert(self.l[18].get_full_url()=='http://www.evvs.dk/index.php?cPath=26&osCsid=90207c4908a98db6503c0381b6b7aa70')
        assert(self.l[19].get_full_url()=='http://arstechnica.com/reviews/os/macosx-10.4.ars/')
        assert(self.l[20].get_full_url()=='http://www.fylkesmannen.no/fmt_hoved.asp')

    
    def test_is_file_like(self):

        assert(self.l[0].filelike==True)
        assert(self.l[1].filelike==True)
        assert(self.l[2].filelike==False)
        assert(self.l[3].filelike==True)
        assert(self.l[4].filelike==True)
        assert(self.l[5].filelike==True)
        assert(self.l[6].filelike==True)
        assert(self.l[7].filelike==True)
        assert(self.l[8].filelike==True)
        assert(self.l[9].filelike==True)
        assert(self.l[10].filelike==True)
        assert(self.l[11].filelike==True)
        assert(self.l[12].filelike==True)
        assert(self.l[13].filelike==True)
        assert(self.l[14].filelike==True)
        assert(self.l[15].filelike==True)
        assert(self.l[16].filelike==True)
        assert(self.l[17].filelike==True)
        assert(self.l[18].filelike==True)
        assert(self.l[19].filelike==False)
        assert(self.l[20].filelike==True)                
        
    def test_anchor_tag(self):

        assert(self.l[0].get_anchor()=='')
        assert(self.l[1].get_anchor()=='')
        assert(self.l[2].get_anchor()=='')
        assert(self.l[3].get_anchor()=='')
        assert(self.l[4].get_anchor()=='')
        assert(self.l[5].get_anchor()=='')
        assert(self.l[6].get_anchor()=='')
        assert(self.l[7].get_anchor()=='')
        assert(self.l[8].get_anchor()=='')
        assert(self.l[9].get_anchor()=='')
        assert(self.l[10].get_anchor()=='')
        assert(self.l[11].get_anchor()=='')
        assert(self.l[12].get_anchor()=='')
        assert(self.l[13].get_anchor()=='#anchor')
        assert(self.l[14].get_anchor()=='#__init__#index-after')
        assert(self.l[15].get_anchor()=='')
        assert(self.l[16].get_anchor()=='')
        assert(self.l[17].get_anchor()=='')
        assert(self.l[18].get_anchor()=='')
        assert(self.l[19].get_anchor()=='')
        assert(self.l[20].get_anchor()=='')                
        
if __name__=="__main__":
    s = unittest.makeSuite(TestHarvestManUrlParser)
    unittest.TextTestRunner(verbosity=2).run(s)

    
    
