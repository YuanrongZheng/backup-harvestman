# -- coding: latin-1
""" strptime version 1.7, Time-stamp: <01/05/31 13:07:02 flognat>
               The reverse of strftime.

BTW This functionality seems to be in Python 2.1!

    Copyright (C) 2001 Andrew Markebo, flognat@fukt.hk-r.se

    This is free software; unrestricted redistribution is allowed under the
    terms of the LGPL.  For full details of the license conditions of this
    software, see the GNU LESSER GENERAL PUBLIC LICENSE
       http://www.gnu.org/copyleft/lesser.txt 

    And here comes the documentation:

    Throw a string and a format specification at strptime and if everything
    is ok you will get a tuple containing 9 items that are compatible with
    pythons time-module.

    interface:
       strptime(inputstring, formatstring)

       Little errorchecking... so you'd better now what you are doing.

    example:
       from strptime import *
       mktime(strptime('26/6 1973', '%d/%m %Y'))

    And voila you have the second when the author of this function was born.

    The supported format identifiers are:
        %a weekday in short text-form, e.g. Mon
    %A weekday in long text-form, e.g. Monday
    %b month in short text-form, e.g. Jul
    %B month in long text-form e.g. July
    %c the format specified by DateAndTimeRepresentation
    %d the day in month in numeric form, e.g. 24
    %H hour in 24 hour form
    %j julian day (day of year)
    %m month in numeric format
    %M minute
    %S second
    %T Time in '%H:%M:%S'-format
    %w weekday, 0=monday
    %x date in format represented by DateRepresentation
    %X time in format represented by TimeRepresentation
    %y year in short form
    %Y year in long form
    %% %-sign

    I have done some thinking here (*REALLY*) and it is possible to configure
    this module so it uses other languages by adding their names to the
    dictionaries first in the file, and setting the variable LANGUAGE.

    For your exercise I have inserted the swedish names ;-)

    The lfind, name, complex, numbers and parse functions are for internal
    use, called by strptime.

    Uh.. oh yeah.. if you want to get in touch with me.. I am reachable
    at flognat@fukt.hk-r.se, the newest version of this file can probably
    be found somewhere close to http://www.fukt.hk-r.se/~flognat

    Story:
      9th of October 2000, upgraded 1.3 to 1.4,
         changed license from GPL to LGPL, and updated
         my addresses.
      23rd of May 2001, updated 1.4 to 1.5,
        Additions by BroytMann, phd@phd.pp.ru.
        'I've added Russian language (koi8-r and windows-1251 encodings)'
      31st of May 2001, 1.5-1.6 OOps not Y2K compatible..
         long years became 1900, not 200 :-)
      25 Jul 2001 1.7 Some minor problems with the fix above
    """

import string
from time import *

LongDayNames={ 'English' : [ 'Monday', 'Tuesday', 'Wednesday',
                             'Thursday', 'Friday', 'Saturday', 'Sunday'],
               'Swedish' : [ 'Måndag', 'Tisdag', 'Onsdag', 'Torsdag',
                 'Fredag', 'Lördag', 'Söndag'],
               'Russian' : [ 'ðÏÎÅÄÅÌØÎÉË', '÷ÔÏÒÎÉË', 'óÒÅÄÁ', 'þÅÔ×ÅÒÇ',
                             'ðÑÔÎÉÃÁ', 'óÕÂÂÏÔÁ', '÷ÏÓËÒÅÓÅÎØÅ'],
               'Windows-1251' : [ 'Ïîíåäåëüíèê', 'Âòîðíèê', 'Ñðåäà', '×åòâåðã',
                             'Ïÿòíèöà', 'Ñóááîòà', 'Âîñêðåñåíüå']
}
                             
ShortDayNames={ 'English' : [ 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'Swedish' : [ 'Mån', 'Tis', 'Ons', 'Tor', 'Fre', 'Lör', 'Sön'],
                'Russian' : [ 'ðÎ', '÷Ô', 'óÒ', 'þÔ', 'ðÔ', 'óÂ', '÷ÓË'],
                'Windows-1251' : [ 'Ïí', 'Âò', 'Ñð', '×ò', 'Ïò', 'Ñá', 'Âñê']
}

LongMonthNames={ 'English' : ['none', 'January', 'February', 'March', 'April',
                  'May', 'June', 'July', 'August', 'September',
                  'October', 'November', 'December'],
         'Swedish' : ['none', 'Januari', 'Februari', 'Mars', 'April',
                  'Maj', 'Juni', 'Juli', 'Augusti','September',
                  'Oktober', 'November', 'December'],
                 'Russian' : ['ÎÅÔ', 'ñÎ×ÁÒØ', 'æÅ×ÒÁÌØ', 'íÁÒÔ', 'áÐÒÅÌØ',
                              'íÁÊ', 'éÀÎØ', 'éÀÌØ', 'á×ÇÕÓÔ', 'óÅÎÔÑÂÒØ',
                              'ïËÔÑÂÒØ', 'îÏÑÂÒØ', 'äÅËÁÂÒØ'],
                 'Windows-1251' : ['íåò', 'ßíâàðü', 'Ôåâðàëü', 'Ìàðò', 'Àïðåëü',
                              'Ìàé', 'Èþíü', 'Èþëü', 'Àâãóñò', 'Ñåíòÿáðü',
                              'Îêòÿáðü', 'Íîÿáðü', 'Äåêàáðü']
}

ShortMonthNames={ 'English' : ['none', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                  'Swedish' : ['none', 'Jan', 'Feb', 'Mar', 'Apr', 'Maj', 'Jun',
                               'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec'],
                  'Russian' : ['ÎÅÔ', 'ñÎ×', 'æ×Ò', 'íÁÒ', 'áÐÒ', 'íÁÊ',
                               'éÀÎ', 'éÀÌ', 'á×Ç', 'óÎÔ', 'ïËÔ', 'îÏÑ', 'äÅË'],
                  'Windows-1251' : ['íåò', 'ßíâ', 'Ôâð', 'Ìàð', 'Àïð', 'Ìàé',
                               'Èþí', 'Èþë', 'Àâã', 'Ñíò', 'Îêò', 'Íîÿ', 'Äåê']
}

DateAndTimeRepresentation={ 'English' : '%a %b %d %H:%m:%S %Y',
                'Swedish' : '%a %d %b %Y %H:%m:%S',
                            'Russian' : '%a %d %b %Y %H:%M:%S',
                            'Windows-1251' : '%a %d %b %Y %H:%M:%S'
}

DateRepresentation = { 'English' : '%m/%d/%y',
               'Swedish' : '%d/%m/%y',
                       'Russian' : '%d-%m-%y',
                       'Windows-1251' : '%d-%m-%y'
}

TimeRepresentation = { 'English' : '%H:%M:%S',
               'Swedish' : '%H:%M:%S',
                       'Russian' : '%H:%M:%S',
                       'Windows-1251' : '%H:%M:%S'
}

LANGUAGE='English'

BadFormatter='An illegal formatter was given'

#Check if string begins with substr
def lfind(str, substr):
   return string.lower(str[:len(substr)])==string.lower(substr)

#atoms consisting of other atoms
def complex(str, format, base):
   code=format[:1]
   if code=='c': 
      string=DateAndTimeRepresentation[LANGUAGE]
   elif code=='T':
      string='%H:%M:%S'
   elif code=='x':
      string=DateRepresentation[LANGUAGE]
   elif code=='X':
      string=TimeRepresentation[LANGUAGE]

   return parse(str, string, base)

#string based names
def names(str, format, base):
   code=format[:1]
   if code=='a':
      selection=ShortDayNames[LANGUAGE]
      result='weekd'
   elif code=='A':
      selection=LongDayNames[LANGUAGE]
      result='weekd'
   elif code=='b':
      selection=ShortMonthNames[LANGUAGE]
      result='month'
   elif code=='B':
      selection=LongMonthNames[LANGUAGE]
      result='month'
   
   match=None
   for i in selection:
      if lfind(str, i):
          match=i
          break

   base[result]=selection.index(match)
   return len(match)

#numeric stuff
def numeric(str, format, base):
   code=format[:1]
   if code=='d': result='day'
   elif code=='H': result='hour'
   elif code=='j': result='juliand'
   elif code=='m': result='month'
   elif code=='M': result='min'
   elif code=='S': result='sec'
   elif code=='w': result='weekd'
   elif code=='y': result='shortYear'
   elif code=='Y': result='year'

   i=0
   while str[i] in string.whitespace: i=i+1
   j=i
   if len(format)>1:
      while not str[j] in string.whitespace and str[j]!=format[1]: j=j+1
   else:
      try:
          while not str[j] in string.whitespace: j=j+1
      except IndexError:
          pass

   # hmm could check exception here, but what could I add?
   base[result] = int(str[i:j])
   
   return j

parseFuns={ 'a':names, 'A':names, 'b':names, 'B':names, 'c':complex, 'd':numeric,
        'H':numeric, 'j':numeric, 'm':numeric, 'M':numeric, 'S':numeric,
        'T':complex, 'w':numeric, 'x':complex, 'y':numeric, 'Y':numeric}

# Well split up in atoms, reason to why this is separated from atrptime
# is to be able to reparse complex atoms
def parse(str, format, base):
   atoms=string.split(format, '%')
   charCounter=0
   atomCounter=0

   # Hey I am laazy and think that the format is exactly what the string is!
   charCounter=charCounter+len(atoms[atomCounter])
   atomCounter=atomCounter+1

   while atomCounter < len(atoms) and charCounter < len(str):
      atom=atoms[atomCounter]

      if atom=='': # escaped
          charCounter=charCounter+1
          atomCounter=atomCounter+1
          charCounter=charCounter+len(atoms[atomCounter])
      else:
          try:
              parsefunction=parseFuns[atom[:1]]
          except KeyError:
              raise BadFormatter, atom[:1]
          
          grabbed=apply(parsefunction, (str[charCounter:], atom, base))
          charCounter=charCounter+grabbed+len(atom)-1
          atomCounter=atomCounter+1

   return charCounter

# Ok here we go, tadaaa --> STRPTIME <-- at last..
def strptime(str, format):
   """Converts str specified by format to tuple useable by the time module"""
   returnTime={}
   returnTime['year']=0
   returnTime['shortYear']=None
   returnTime['month']=0
   returnTime['day']=0
   returnTime['hour']=0
   returnTime['min']=0
   returnTime['sec']=0
   returnTime['weekd']=0
   returnTime['juliand']=0
   returnTime['dst']=0

   parse(str, format, returnTime)

   ########################
   # Preparation for more configurability
   # (Oops it wasn't Y2k compatible.. :-) LongYear was 1900 prefixed, not 2000
   # Now we decide on YEARSPLIT if it is 2000 or 1900
   # Will have to dig on this some, in the future
   
   # CENTURY=2000
   CENTURY=None
   YEARSPLIT=50

   if returnTime['shortYear']!=None:
       if CENTURY!=None:
           returnTime['year']=returnTime['shortYear']+CENTURY
       else:
           if returnTime['shortYear'] <= YEARSPLIT:
               returnTime['year']=returnTime['shortYear']+2000
           else:
               returnTime['year']=returnTime['shortYear']+1900


   return (returnTime['year'], returnTime['month'], returnTime['day'],
       returnTime['hour'], returnTime['min'], returnTime['sec'],
       returnTime['weekd'], returnTime['juliand'], returnTime['dst'])

# just for my convenience
def strpdebug():
   import pdb
   pdb.run('strptime("% Tue 3 Feb", "%% %a %d %b")')

def test():

   a=asctime(localtime(time()))
   print a
   b=strptime(a, '%a %b %d %H:%M:%S %Y')
   print b
   print asctime(b)

   print strptime("%% % Tue 3 Feb", "%%%% %% %a %d %b")
   print strptime('Thu, 12 Sep 1996 19:42:06 GMT', '%a, %d %b %Y %T GMT')
   try:
      print strptime('Thu, 12 Sep 1996 19:42:06 GMT', '%a, %d %b %Y %T')
   except ValueError:
      print "Error as expected.. unconverted data remains"
         
   print strptime('Thu, 12 Sep 1996 19:42:06', '%a, %d %b %Y %T')
   
if __name__ == '__main__':
   test()


