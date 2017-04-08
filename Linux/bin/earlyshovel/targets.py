#!/usr/bin/python
import asprh73
import rh70
import rh71
import rh72

targets = \
   [asprh73.asprh73,
    rh70.rh70,
    rh71.rh71,
    rh72.rh72]

def factory(version, badBytes):
   for target in targets:
      if (target.version == version):
         return target(badBytes)
   return None

def list():
   print "Supported targets:"
   for target in targets:
      print "   \"%s\": %s" % (target.version, target.details)

def main():
   list()

if __name__ == "__main__":
   main()
