#!/usr/bin/python
import solaris8
import solaris9

systems = \
   [solaris8.solaris8,
    solaris9.solaris9]

def factory(version, stackBase):
   for system in systems:
      if (system.version == version):
         if (None != stackBase):
            return system(stackBase)
         else:
            return system()
   return None

def list():
   print "Supported operating systems:"
   for system in systems:
      print "   %s" % system.version

def main():
   list()

def stackTouch(target, stackBase=None, bruteForce=False):
   for system in systems:
      if (None != stackBase):
         os = system(stackBase)
      else:
         os = system()
      retVal = os.stackTouch(target, bruteForce)
      if (0 == retVal):
         print "\nTarget appears to be running %s." % os.version
         target.os = os
         return 0
   return 1

if __name__ == "__main__":
   main()
