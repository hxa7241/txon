#
# TXON (Python 2.5)
# =================
#


# Harrison Ainsworth / HXA7241 : 2010
# http://www.hxa.name/txon/
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.



# Containing four parts:
#
#  * TXON Reader
#  * TXON Writer
#  * TXON-JSON Translator
#  * Command-line tool
#
# (The second two depending on the first two.)



# Possible improvements:
#
#  * writeTxon
#     * flatten lists ?:
#       -- terms that have: a key that is anonymous, and a value that is a list
#       containing all anonymous members
#       -- or flatten all lists?








# TXON Reader #################################################################


# The implementation is deliberately very basic and simple in order to be easy
# to translate -- the core is just string indexing, sub-string extraction, char
# comparisons, and loops.



# - public interface --------------------------------------------------------- #

def readTxon( text ) :
   """Construct native Python data from TXON embedded in text.

   Pass in a unicode or UTF-8 string, and the return is a dict or list
   containing the parsed TXON. Each value is either a unicode string, or dict
   or list containing further nested content. Dicts are the usual container,
   but dicts with all-anonymous items are replaced by lists.

   Values may be single or list -- since names are not required to be unique,
   each may have multiple values.

   :text:       ``unicode`` string (or UTF-8 str) containing TXON.
   :return:     ``dict`` or ``list`` containing the constructed data.
   :exceptions: none."""

   # check type preconditions
   if isinstance( text, (str, unicode) ) :
      if not isinstance( text, unicode ) :
         text = unicode( text, "utf8", "replace" )

      return constructFromTxon( text )
   else :
      return {}



# - implementation ----------------------------------------------------------- #

import string


def constructFromTxon( text, pos=0 ) :
   """Construct native Python data from TXON embedded in text.

   If called from outside (with no ``pos``), return a ``dict`` or ``list`` of
   all parsed TXON. Else, when called recursively, parse and construct the next
   TXON value (the part between open and close chars) returning either a
   ``dict`` or ``list``, or a ``string``.

   :text:       ``unicode`` string.
   :pos:        ``int`` position immediately after open (optional).
   :return:     when called externally: ``dict`` or ``list``; when called
                recursively: ``tuple`` of either ``unicode`` string or
                ``dict`` or ``list``, and next position.
   :exceptions: none."""

   # constants (as well as text)
   posStart    = pos
   isBaseLevel = posStart == 0

   # step through text, until close char or string end
   parsed   = {}
   posChunk = pos
   while (pos < len( text )) and \
         (isBaseLevel or not isClose( text, posStart, pos )) :

      # if start of a sub-term, parse and store and move past it
      if isOpen( text, posStart, pos ) :
         posChunk, pos = parseTerm( text, posChunk, pos, parsed )

      # else, increment text position
      else :
         pos += 1

   # replace dict containing all-anonymous items with list
   parsed = elideListStructure( parsed )

   if isBaseLevel :
      return parsed
   else :
      # if sub-terms were found, return them, otherwise the inspected string
      return (parsed or text[posStart:pos], pos + 1)


def isOpen( text, posStart, pos ) :
   """Test if previous chars match 'open' sequence."""

   return (pos > posStart) and (text[pos-1] == u":") and (text[pos] == u"`")


def isClose( text, posStart, pos ) :
   """Test if previous chars match 'close' sequence (and not escaped)."""

   return (text[pos] == u"`") and not isOpen( text, posStart, pos) and \
      not ((pos > posStart) and (text[pos-1] == u"\\"))


def findName( text, posChunk, pos ) :
   """Find start position of name token."""

   # step backwards until blank or last boundary (open or close)
   while (pos >= posChunk) and (text[pos] not in string.whitespace) :
      pos -= 1
   return pos + 1


def setOrAppend( obj, key, value ) :
   """Set value, or if already set make it a list and append to it, or if
   already a list just append to it."""

   if key not in obj :
      obj[key] = value
   else :
      if not isinstance( obj[key], list ) :
         obj[key] = [obj[key]]
      obj[key].append( value )


def parseTerm( text, posChunk, pos, parsed_o ) :
   """Parse and store sub-term, and advance positions."""

   # find start of name
   posName = findName( text, posChunk, pos )

   # store term, and move forwards past it
   key        = text[posName:pos-1]
   value, pos = constructFromTxon( text, pos + 1 )
   setOrAppend( parsed_o, key, value )
   posChunk   = pos

   return (posChunk, pos)


def elideListStructure( parsed ) :
   """If the dict contains only a single anonymous key, turn it into a list
   containing the anonymous sub-value."""

   if (len( parsed ) == 1) and (u"" in parsed) :
      innerValue = parsed[u""]
      parsed    = innerValue if isinstance( innerValue, list ) else [innerValue]
   return parsed








# TXON Writer #################################################################



# - public interface --------------------------------------------------------- #

# options: possible values
AUTO     = 0
LINEAR   = 1
INDENTED = 2


def writeTxon( obj, options=0 ) :
   """Serialise native Python data to a string of TXON.

   Pass in a JSON-form object, and the return is a string of TXON. Each item of
   the input object can be string-serialisable data, or a dict or list
   containing further nested items.

   The textual layout can be controlled with the options. Linear writes as a
   single line, and indented writes each value on a separated indented line.

   :obj:        ``dict`` or ``list`` containing the data.
   :options:    one of the layout option values (optional).
   :return:     ``unicode`` string containing TXON.
   :exceptions: none."""

   if isinstance( obj, (dict, list) ) :
      options = options if isinstance( options, int ) else AUTO
      return serialiseToTxon( obj, options )
   else:
      return u""



# - implementation ----------------------------------------------------------- #

def serialiseToTxon( obj, options=0, level=0 ) :
   """Serialise native Python data to a string of TXON.

   :obj:        ``dict`` or ``list`` containing the data.
   :options:    one of the layout option values (optional).
   :level:      ``int`` >= 0 (optional).
   :return:     ``unicode`` string.
   :exceptions: none."""

   # make key-vals from collection:
   # either: from dict
   if isinstance( obj, dict ) :
      # list sorted by key
      keyVals = sorted( obj.items(), key = lambda i: i[0].lower() )
   # or: from list
   else :
      # list of anonymous pairs (preserving order)
      keyVals = zip( [u""] * len(obj), obj )

   # make strings from key-vals
   strings = map( lambda kv: keyValueToString( kv, options, level ), keyVals )

   # define layout according to option:
   # either: separate terms from each other by a space
   if options == LINEAR :
      prefix = suffix = u" "
   # or: put each value on a separate line, and indent at each nesting
   else :   # options == INDENTED or AUTO:
      newlineIndent = lambda i : u"\n" + (u"  " * (level + i))
      prefix, suffix = newlineIndent( 0 ), newlineIndent( -1 )

   # assemble serialisation
   txonstring = prefix.join( strings )
   if level > 0 :
      txonstring = prefix + txonstring + suffix

   return txonstring


def keyValueToString( kv, options, level ) :
   """Map key-value to string surrounded by the syntax markers."""

   key, value = kv

   # condition key and add open marker
   s = u"_".join( unicode( key ).replace( u"`", u"" ).split() ) + u":`"

   # if sub-term, recurse to serialiseToTxon
   if isinstance( value, (dict, list) ) :
      s += serialiseToTxon( value, options, level + 1 )
   # else, convert to unicode string
   else :
      s += unicode( value ).replace( u"\`", u"`" ).replace( u"`", u"\`" )

   # add close marker
   s += u"`"

   return s








# TXON-JSON Translator #########################################################


# Dependent on:
#  * TXON Reader
#  * TXON Writer
#  * json (in Python 2.6+), or without that, simplejson


# The serialiseToJson implementation is deliberately quite basic and simple in
# order to be easy to translate -- mainly just iterational and conditional
# string concatenation.



# - public interface --------------------------------------------------------- #

def translateTxonToJson( text, options=0 ) :
   """Translate TXON (extracted from text) into JSON.

   :text:       ``unicode`` string (or UTF-8 str) containing TXON.
   :options:    one of the layout option values from TXON Writer (optional).
   :return:     ``unicode`` string of JSON.
   :exceptions: none."""

   return serialiseToJson( readTxon( text ), options )


def translateJsonToTxon( s, options=0 ) :
   """Translate JSON into TXON.

   :s:          ``unicode`` string of JSON.
   :options:    one of the layout option values from TXON Writer (optional).
   :return:     ``unicode`` string of TXON.
   :exceptions: as for json module."""

   try:
      import json
   except ImportError:
      import simplejson as json

   return writeTxon( json.loads( s ), options )



# - implementation ----------------------------------------------------------- #

def serialiseToJson( obj, options=0, level=0 ) :
   """Serialise native Python data, presumably from TXON, to a string of JSON.

   :obj:        ``dict`` or ``list`` containing the data.
   :options:    one of the layout option values (optional).
   :level:      ``int`` >= 0 (optional).
   :return:     ``unicode`` string.
   :exceptions: none."""

   # define layout according to options
   pairing, prefix, inter, suffix = defineLayout( obj, options, level )

   jsonString = u""

   # make key-vals list from collection
   keyVals = makeKeyVals( obj )
   # step through key-vals
   for (i, (key, value)) in enumerate( keyVals ) :

      # make strings
      keyString, ValString = serialiseKeyVal( key, value, options, level )
      joinString           = u"" if i == 0 else inter

      # accumulate strings to total
      p = pairing if keyString and isinstance( value, (dict, list) ) else u""
      jsonString += joinString + keyString + p + ValString

   return prefix + jsonString + suffix


def defineLayout( obj, options, level ) :
   """Define layout according to options and context."""

   brackets = u"{}" if isinstance( obj, dict ) else u"[]"

   # either: separate terms from each other by a space
   if options == LINEAR :
      pairing, prefix, inter, suffix = \
         u"", (brackets[0] + u" "), u", ", (u" " + brackets[1])

   # or: put each value on a separate line, and indent at each nesting
   else :   # options == INDENTED or AUTO:
      newlineIndent = lambda i : u"\n" + (u"  " * (level + i))
      pairing = newlineIndent( 1 )
      prefix  = brackets[0] + newlineIndent( 1 )
      inter   = u"," + newlineIndent( 1 )
      suffix  = newlineIndent( 0 ) + brackets[1]

   return (pairing, prefix, inter, suffix)


def makeKeyVals( obj ) :
   """Make list of key-vals from polymorphic collection."""

   # either: from dict
   if isinstance( obj, dict ) :
      # list sorted by key
      return sorted( obj.items(), key = lambda i: i[0].lower() )

   # or: from list
   else :
      # list with added anonymous keys
      return zip( [None] * len(obj), obj )


def convertString( s ) :
   """Prepare string for display."""

   # unescape then escape, and wrap
   return u"\"" + unicode( s ).replace( u"\\\"", u"\"" ).replace(
      u"\"", u"\\\"" ) + u"\""


def serialiseKeyVal( key, value, options, level ) :
   """Serialise a key-value pair to strings."""

   # convert key to string
   keyString = convertString( key ) + u":" if key != None else u""

   # get value string:
   # if sub-term, recurse to serialiseToJson
   if isinstance( value, (dict, list) ) :
      valString = serialiseToJson( value, options, level + 1 )
   # else, convert to unicode string
   else :
      valString = convertString( value )

   return (keyString, valString)








# Command-line tool ###########################################################


# Command-line UI for TXON-JSON Translator.

# Dependent on:
#  * TXON-JSON Translator



from sys import argv, stdin, stdout


if __name__ == "__main__" :

   # print help message
   if (len(argv) > 1) and ((argv[1] == "-?") or (argv[1] == "--help")) :

      print
      print "   TXON tool (Python 2.5)"
      print
      print "   Harrison Ainsworth / HXA7241 : 2010-05-28"
      print "   http://www.hxa.name/txon/"
      print
      print
      print "Command-line tool to translate TXON to and from JSON."
      print
      print "usage:"
      print "   txon [-tj|-jt] [input-filepathname [output-filepathname]]"
      print
      print "translation switch:"
      print " * -tj -- TXON -> JSON (default)"
      print " * -jt -- JSON -> TXON"
      print
      print "i/o source/target:"
      print " * if none, use stdin/stdout"
      print " * if input-name, open file, and output to input-name.out file"
      print " * else, use input and output names for files"
      print
      print "dependencies:"
      print " * json (in Python 2.6+), or simplejson -- for JSON -> TXON"
      print

   # execute
   else :

      # canonicalise args: start with switch, length 4
      args = argv if (len(argv) > 1) and (argv[1][0] == "-") else ["-"] + argv
      args = args + ([""] * (4 - len(args)))

      isJT = (args[1] == "-jt")

      try :
         # set in/out channels
         if args[2] :
            fileIn  = open( args[2], "r" )
            fileOut = open( args[3] or (args[2] + ".out"), "w" )
         else :
            fileIn  = stdin
            fileOut = stdout

         # read
         inString = fileIn.read()

         # translate
         options = 0
         if isJT :
            outString = translateJsonToTxon( inString, options )
         else :
            outString = translateTxonToJson( inString, options )

         # write
         fileOut.write( outString )
         fileOut.flush()

      finally:
         # close in/out channels
         if args[2] :
            if "fileOut" in locals() : fileOut.close()
            if "fileIn"  in locals() : fileIn.close()
