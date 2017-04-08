#!/usr/bin/python
import iplanet_5_2
import iplanet_5_2hf0_8
import iplanet_5_2p1
import iplanet_5_2hf1_02
import iplanet_5_2hf1_16
import iplanet_5_2hf1_21
import iplanet_5_2hf1_25
import sunJava_6_2_3_04
import sunJava_6_2_4_03

targets = \
   [iplanet_5_2.iplanet_5_2,
    iplanet_5_2hf0_8.iplanet_5_2hf0_8,
    iplanet_5_2p1.iplanet_5_2p1,
    iplanet_5_2hf1_02.iplanet_5_2hf1_02,
    iplanet_5_2hf1_16.iplanet_5_2hf1_16,
    iplanet_5_2hf1_21.iplanet_5_2hf1_21,
    iplanet_5_2hf1_25.iplanet_5_2hf1_25]

def factory(version):
   for target in targets:
      if (target.version == version):
         return target()
   return None

def list():
   print "Supported versions:"
   for target in targets:
      print "   %s" % target.version

def main():
   list()

if __name__ == "__main__":
   main()
