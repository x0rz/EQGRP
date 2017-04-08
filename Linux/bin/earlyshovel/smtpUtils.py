# smtpUtils.py
# This module mimics the functionality of the smtplib module, but leaves
# the socket exposed so we can use it elsewhere.
import socket

class smtpError:
   def printMsg(self):
      print "Received \"%s\" from the target" % self.msg

class smtpRecipientRefused(smtpError):
   def __init__(self, msg):
      self.msg = msg
   def printMsg(self):
      smtpError.printMsg(self)
      print "Please specify a different recipient."

class smtpSenderRefused(smtpError):
   def __init__(self, msg):
      self.msg = msg
   def printMsg(self):
      smtpError.printMsg(self)
      print "Please specify a different sender."

class smtpServerCrashed(smtpError):
   def printMsg(self, msg):
      print "Target crashed%s." % msg

class smtpServerDisconnected(smtpError):
   def printMsg(self, msg):
      print "Target disconnected%s." % msg

def connect(host, port, wantBanner=False):
   sd = socket.socket()
   sd.connect((host, port))
   banner = sd.recv(1024)
   if (wantBanner):
      return sd, banner
   return sd

def data(sd):
   sd.send('data\r\n')
   sd.recv(1024)

def ehlo(sd):
   sd.send('ehlo\r\n')
   sd.recv(1024)

def helo(sd, address, validReply):
   if (None != address):
      sd.send('helo %s\r\n' % address)
   else:
      sd.send('helo\r\n')
   sd.recv(1024)
   
def mailFrom(sd, sender, validReply):
   sd.send('mail from: %s\r\n' % sender)
   response = sd.recv(1024)
   if (None != validReply):
      if (False == validReply(sender, response)):
         sd.send('quit\r\n')
         sd.close()
         raise smtpSenderRefused(response.strip())

def quit(sd):
   sd.send('quit\r\n')
   sd.close()

def rcptTo(sd, recipient, validReply):
   sd.send('rcpt to: %s\r\n' % recipient)
   response = sd.recv(1024)
   if (None != validReply):
      if (False == validReply(recipient, response)):
         sd.send('quit\r\n')
         sd.close()
         raise smtpRecipientRefused(response.strip())

def recvReply(sd, nBytes=1024):
   reply = sd.recv(nBytes)
   if (None == reply):
      sd.close()
      raise smtpServerDisconnected()
   elif (0 == len(reply)):
      sd.close()
      raise smtpServerCrashed()
   return reply

def sendMsg(sd, *lines):
   #sd.send("Content-Language: %s\r\n" % contentLang)
   # I would like to wait for an ack before sending the rest.
   # How can I do this reliably and w/o getting h
#   msg = ''
   for line in lines:
      sd.send("%s\r\n" % line)
   sd.send(".\r\n")

def startNewMsg(sd, sender, recipient):
   mailFrom(sd, sender)
   rcptTo(sd, recipient)
   data(sd)
