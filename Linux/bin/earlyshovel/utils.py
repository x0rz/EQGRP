import random
import select
import struct
import sys

def u32ToBeU32String(val):
   tmp = chr((val >> 24) & 0xff) \
         + chr((val >> 16) & 0xff) \
         + chr((val >> 8) & 0xff) \
         + chr(val & 0xff)
   return tmp

def u32ToLeU32String(val):
   tmp = chr(val & 0xff) \
         + chr((val >> 8) & 0xff) \
         + chr((val >> 16) & 0xff) \
         + chr((val >> 24) & 0xff)
   return tmp

def u16ToBeU16String(val):
   tmp = chr((val >> 8) & 0xff) \
         + chr(val & 0xff)
   return tmp

def u16ToLeU16String(val):
   tmp = chr(val & 0xff) \
         + chr((val >> 8) & 0xff)
   return tmp

def beS32toS32(buf):
   tmp = struct.unpack(">i", buf)
   return tmp[0]

def leS32StringToS32(buf):
   tmp = struct.unpack("<i", buf)
   return tmp[0]

# builds a buffer of length len that doesn't have any of the bytes in badBytes
def buildBuffer(len, badBytes):
   buf = randomBase64(len, 0)
   while (bufHasBadBytes(buf, badBytes)):
      buf = randomBase64(len, 0)
   return buf

def buf2long(buf):
   length = len(buf)
   val = 0
   pos = 1
   for i in buf:
      val += long(ord(i)) << (8 * (length - pos))
      pos += 1
   return val

# checks the buffer buf for bytes in badBytes
def bufHasBadBytes(buf, badBytes):
   for i in buf:
      c = ord(i)
      if c in badBytes:
         return True
   return False

def dumpHex(buf):
   buflen = len(buf)
   for i in range(buflen):
      if (0 == (i % 16)):
         sys.stdout.write("   \"")
      sys.stdout.write("\\x%02x" % ord(buf[i]))
      if (i == (buflen - 1)):
         sys.stdout.write("\"\n")
      elif (15 == (i % 16)):
         sys.stdout.write("\"\\\n")

def intHasBadBytes(num, badBytes):
   for i in range(0, 32, 8):
      n = (num >> i) & 0xff
      if n in badBytes:
         return True
   return False

def interact(sd):
   print "An interactive shell awaits below despite the lack of a prompt."
   while 1:
      readable, writable, exceptional = select.select([sys.stdin, sd], [], [])
      if sys.stdin in readable:
         next = sys.stdin.readline()
         if not next:
            break
         sd.send(next)
      if sd in readable:
         next = sd.recv(1024)
         if not next:
            break
         sys.stdout.write(next)

def randomBase64(len, linelen):
   alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
   tmp = ''

   npos = linelen - 1
   rpos = linelen - 2
   for i in range(len):
      if (0 != linelen):
         pos = i % linelen
      else:
         pos = i

      if pos == rpos:
         tmp += '\r'
      elif pos == npos:
         tmp += '\n'
      else:
         n = random.randint(0, 63)
         tmp += alpha[n]

   return tmp

def randomSparcNOP(badRegs, badBytes):
   opcodes = ['000000',	#ADD
              '000001', #AND
              '000101', #ANDN
              '000010', #OR
              '000110', #ORN
              '000011', #XOR
              '000111', #XORN
              '000100'] #SUB
   nOpcodes = len(opcodes) - 1
   mask = (2 ** 19) - 1
   instruction = 0
   while (intHasBadBytes(instruction, badBytes)):
      rd = random.randint(0, 31)
      while rd in badRegs:
         rd = random.randint(0, 31)
      opcode = opcodes[random.randint(0, nOpcodes)]
      rest = random.randint(0, mask)
      instruction = (long(int('10', 2)) << 30) \
                    | (long(rd) << 25) \
                    | (long(int(opcode, 2)) << 19) \
                    | rest
   return instruction

def tmpnam():
   tmp = buildBuffer(6, [0x2b, 0x2f])
   return "/tmp/file" + tmp
