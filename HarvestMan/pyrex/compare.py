from urlparser import HarvestManUrlParser

def f1():
    hu =  HarvestManUrlParser('//images.sourceforge.net/div.png',
                                  'image', 0, 'http://sourceforge.net', '')
    
   ##  hulist = [HarvestManUrlParser('http://www.yahoo.com/photos/my photo.gif'),
##               HarvestManUrlParser('http://www.rediff.com:80/r/r/tn2/2003/jun/25usfed.htm'),
##               HarvestManUrlParser('http://cwc2003.rediffblogs.com'),
##               HarvestManUrlParser('/sports/2003/jun/25beck1.htm',
##                                   'normal', 0, 'http://www.rediff.com', ''),
##               HarvestManUrlParser('ftp://ftp.gnu.org/pub/lpf.README'),
##               HarvestManUrlParser('http://www.python.org/doc/2.3b2/'),
##               HarvestManUrlParser('//images.sourceforge.net/div.png',
##                                   'image', 0, 'http://sourceforge.net', ''),
##               HarvestManUrlParser('http://pyro.sourceforge.net/manual/LICENSE'),
##               HarvestManUrlParser('python/test.htm', 'normal', 0,
##                                   'http://www.foo.com/bar', ''),
##               HarvestManUrlParser('/python/test.css', 'normal',
##                                   0, 'http://www.foo.com/bar/vodka/test.htm', ''),
##               HarvestManUrlParser('/visuals/standard.css', 'normal', 0,
##                                   'http://www.garshol.priv.no/download/text/perl.html',
##                                   'd:/websites'),
##               HarvestManUrlParser('www.fnorb.org/index.html', 'normal',
##                                   0, 'http://pyro.sourceforge.net',
##                                   'd:/websites'),
##               HarvestManUrlParser('http://profigure.sourceforge.net/index.html',
##                                   'normal', 0, 'http://pyro.sourceforge.net',
##                                   'd:/websites'),
##               HarvestManUrlParser('#anchor', 'anchor', 0, 
##                                   'http://www.foo.com/bar/index.html',
##                                   'd:/websites'),
##               HarvestManUrlParser('../icons/up.png', 'image', 0,
##                                   'http://www.python.org/doc/current/tut/node2.html',
##                                   ''),
##               HarvestManUrlParser('../eway/library/getmessage.asp?objectid=27015&moduleid=160',
##                                   'normal',0,'http://www.eidsvoll.kommune.no/eway/library/getmessage.asp?objectid=27015&moduleid=160')
##               ]

    #for hu in hulist:
    hu.get_full_filename()
    hu.get_filename()
    hu.is_relative_path()
    hu.get_full_domain()
    hu.get_url_directory_sans_domain()
    hu.get_full_url()
    hu.get_full_url_sans_port()
    hu.get_local_directory()
    hu.get_relative_url()
    hu.get_port_number()
    hu.get_full_domain_with_port()
    hu.get_relative_filename()
    hu.get_anchor_url()
    hu.get_anchor()

if __name__=="__main__":
    import mytimeit
    import urlparser

    urlparser.__TEST__=1
    print mytimeit.Timeit(f1,number=10000)
    
