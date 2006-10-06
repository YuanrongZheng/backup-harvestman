"""Process urls - remove ampersand chars etc

Created - Anand B Pillai <abpillai@gmail.com> 28 Sep 06 """

import unicodedata

char_names = ['LESS-THAN SIGN',
              'GREATER-THAN SIGN',
              'AMPERSAND',
              'QUOTATION MARK',
              'SPACE',
              'LATIN CAPITAL LETTER C WITH CEDILLA',
              'LATIN SMALL LETTER C WITH CEDILLA',
              'LATIN CAPITAL LETTER N WITH TILDE',
              'LATIN SMALL LETTER N WITH TILDE',
              'LATIN CAPITAL LETTER THORN',
              'LATIN SMALL LETTER THORN',
              'LATIN CAPITAL LETTER Y WITH ACUTE',
              'LATIN SMALL LETTER Y WITH ACUTE',
              'LATIN SMALL LETTER Y WITH DIAERESIS',
              'LATIN SMALL LETTER SHARP S',
              'LATIN CAPITAL LETTER AE',
              'LATIN CAPITAL LETTER A WITH ACUTE',
              'LATIN CAPITAL LETTER A WITH CIRCUMFLEX',
              'LATIN CAPITAL LETTER A WITH GRAVE',
              'LATIN CAPITAL LETTER A WITH RING ABOVE',
              'LATIN CAPITAL LETTER A WITH TILDE',
              'LATIN CAPITAL LETTER A WITH DIAERESIS',
              'LATIN SMALL LETTER AE',
              'LATIN SMALL LETTER A WITH ACUTE',
              'LATIN SMALL LETTER A WITH CIRCUMFLEX',
              'LATIN SMALL LETTER A WITH GRAVE',
              'LATIN SMALL LETTER A WITH RING ABOVE',
              'LATIN SMALL LETTER A WITH TILDE',
              'LATIN SMALL LETTER A WITH DIAERESIS',
              'LATIN CAPITAL LETTER ETH',
              'LATIN CAPITAL LETTER E WITH ACUTE',
              'LATIN CAPITAL LETTER E WITH CIRCUMFLEX',
              'LATIN CAPITAL LETTER E WITH GRAVE',
              'LATIN CAPITAL LETTER E WITH DIAERESIS',
              'LATIN SMALL LETTER ETH',
              'LATIN SMALL LETTER E WITH ACUTE',
              'LATIN SMALL LETTER E WITH CIRCUMFLEX',
              'LATIN SMALL LETTER E WITH GRAVE',
              'LATIN SMALL LETTER E WITH DIAERESIS',
              'LATIN CAPITAL LETTER I WITH ACUTE',
              'LATIN CAPITAL LETTER I WITH CIRCUMFLEX',
              'LATIN CAPITAL LETTER I WITH GRAVE',
              'LATIN CAPITAL LETTER I WITH DIAERESIS',
              'LATIN SMALL LETTER I WITH ACUTE',
              'LATIN SMALL LETTER I WITH CIRCUMFLEX',
              'LATIN SMALL LETTER I WITH GRAVE',
              'LATIN SMALL LETTER I WITH DIAERESIS',
              'LATIN CAPITAL LETTER O WITH ACUTE',
              'LATIN CAPITAL LETTER O WITH CIRCUMFLEX',
              'LATIN CAPITAL LETTER O WITH GRAVE',
              'LATIN CAPITAL LETTER O WITH STROKE',
              'LATIN CAPITAL LETTER O WITH TILDE',
              'LATIN CAPITAL LETTER O WITH DIAERESIS',
              'LATIN SMALL LETTER O WITH ACUTE',
              'LATIN SMALL LETTER O WITH CIRCUMFLEX',
              'LATIN SMALL LETTER O WITH GRAVE',
              'LATIN SMALL LETTER O WITH STROKE',
              'LATIN SMALL LETTER O WITH TILDE',
              'LATIN SMALL LETTER O WITH DIAERESIS',
              'LATIN CAPITAL LETTER U WITH ACUTE',
              'LATIN CAPITAL LETTER U WITH CIRCUMFLEX',
              'LATIN CAPITAL LETTER U WITH GRAVE',
              'LATIN CAPITAL LETTER U WITH DIAERESIS',
              'LATIN SMALL LETTER U WITH ACUTE',
              'LATIN SMALL LETTER U WITH CIRCUMFLEX',
              'LATIN SMALL LETTER U WITH GRAVE',
              'LATIN SMALL LETTER U WITH DIAERESIS',
              'REGISTERED SIGN',
              'PLUS-MINUS SIGN',
              'MICRO SIGN',
              'PILCROW SIGN',
              'MIDDLE DOT',
              'CENT SIGN',
              'POUND SIGN',
              'YEN SIGN',
              'VULGAR FRACTION ONE QUARTER',
              'VULGAR FRACTION ONE HALF',
              'VULGAR FRACTION THREE QUARTERS',
              'SUPERSCRIPT ONE',
              'SUPERSCRIPT TWO',
              'SUPERSCRIPT THREE',
              'INVERTED QUESTION MARK',
              'DEGREE SIGN',
              'BROKEN BAR',
              'SECTION SIGN',
              'LEFT-POINTING DOUBLE ANGLE QUOTATION MARK',
              'RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK']

# Ampersand characters
ampersand_strings = ('&lt;','&gt;','&amp;','&quot;',
                     '&nbsp;','&Ccedil;','&ccdil;','&Ntilde;',
                     '&ntilde;','&THORN;','&thorn;','&Yacute;',
                     '&yacute;','&yuml;','&szlig;','&AElig;',
                     '&Aacute;','&Acirc;','&Agrave;','&Aring;',
                     '&Atilde;','&Auml;','&aelig;','&acirc;',
                     '&aacute;','&agrave;','&aring;','&atilde;',
                     '&auml;', '&ETH;','&Eacute;','&Ecirc;',
                     '&Egrave;','&Euml;','&eth;','&eacute;',
                     '&ecirc;','&egrave;','&euml;','&Iacute;',
                     '&Icirc;','&Igrave;','&Iuml;','&iacute;',
                     '&icirc;','&igrave;','&iuml;','&Oacute;',
                     '&Ocirc;','&Ograve;','&Oslash;','&Otilde;',
                     '&Ouml;','&oacute;','&ocirc;','&ograve;',
                     '&oslash;','&otilde;','&ouml;','&Uacute;',
                     '&Ucirc;','&Ugrave;','&Uuml;','&uacute;',
                     '&ucirc;','&ugrave;','&uuml;','&reg;',
                     '&plusmn;','&micro;','&para;','&middot;',
                     '&cent;','&pound;','&yen;','&frac14;',
                     '&frac12;','&frac34;','&sup1;','&sup2;',
                     '&sup3;','&iquest;','&deg;','&brvbar;',
                     '&sect;','&laquo;','&raquo;')
                         
                         
def modify_url(url):

    # Remove trailing wspace chars.
    url = url.rstrip()
    
    for ampersand_string, ucode_name in zip(ampersand_strings, char_names):
        if url.find(ampersand_string) != -1:
            ucode_char = unicodedata.lookup(ucode_name)
            url = url.replace(ampersand_string, ucode_char)

    return url

def main():
    url = 'http://www.nbb.be/pub/Home.htm?l=nl&amp;t=ho'
    print modify_url(url)

if __name__ == "__main__":
    main()
