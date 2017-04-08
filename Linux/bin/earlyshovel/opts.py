import getopt
import sys

class opts:
   def __init__(self, name, options, *usage_thunks):
      self.name = name
      self.options = options
      self.usage_thunks = usage_thunks
      self.options['help'] = \
         {'shortOpt': '?',
          'longOpt': 'help',
          'type': 'help',
          'desc': "Print the usage message"}

   def getoptSetup(self):
      longOpts = []
      shortOpts = ""
      for v in self.options.itervalues():
         options = []
         if 'arg' in v:
            takesArg = True
         else:
            takesArg = False
         if 'shortOpt' in v:
            opt = v['shortOpt']
            options.append('-%s' % opt)
            if takesArg:
               opt += ':'
            shortOpts += opt
         if 'longOpt' in v:
            opt = v['longOpt']
            options.append('--%s' % opt)
            if takesArg:
               opt += '='
            longOpts.append(opt)
         v['options'] = options
      return shortOpts, longOpts

   def get(self, key, default=None):
      value = self.options[key].get('value')
      if (None == value):	# value not set, check for a default
         return self.options[key].get('default', default)
      return value

   def parseCommandLine(self, cmdLine):
      shortOpts, longOpts = self.getoptSetup()
      try:
         opts, args = getopt.getopt(cmdLine, shortOpts, longOpts)
      except getopt.GetoptError:
         self.usage()
         sys.exit(2)
      self.parseOpts(opts)
      return args

   def parseOpts(self, opts):
      for o,a in opts:
         for v in self.options.itervalues():
            if o in v['options']:
                if 'type' in v:
                   type = v['type']
                else:
                   type = str
                if type == 'help':
                   self.usage()
                   sys.exit()
                elif type == bool:
                   v['value'] = not v['value']
                elif type == float:
                   v['value'] = float(a)
                elif type == int:
                   v['value'] = int(a, 0)
                elif type == long:
                   v['value'] = long(a, 0)
                elif type == str:
                   v['value'] = a
                else:
                   raise TypeError(type)
                break

   def set(self, key, value):
      self.options[key]['value'] = value

   def usage(self):
      usage = "usage: %s [options]" % self.name
      blank = ' ' * len(usage)
      print usage
      print "options:"
      k = self.options.keys()
      k.sort()
      for key in k:
         v = self.options[key]
         print "   %s" % v['options'][0],
         for opt in v['options'][1:]:
            print "| %s" % opt,
         if 'arg' in v:
            print v['arg'],
            if 'default' in v:
               print "(default = %s)" % v['default']
            else:
               print
         else:
            print
         if 'desc' in v:
            print "      %s" % v['desc']
      for thunk in self.usage_thunks:
         thunk()
