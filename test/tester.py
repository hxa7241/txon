
import txon


def test1( s, options=0 ) :
   o = txon.readTXON( s )
   w = txon.writeTXON( o, options )
   print "---string-------------"
   print s
   print "---object-------------"
   print o
   print "---serial-------------"
   print w

