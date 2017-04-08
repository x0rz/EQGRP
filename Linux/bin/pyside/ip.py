"""IP packets.
"""

# Copyright 1997, Corporation for National Research Initiatives
# written by Jeremy Hylton, jeremy@cnri.reston.va.us


import inet
import socket
import struct
import string
import os

IPVERSION = 4
IP_DF = 0x4000
IP_MF = 0x2000
IP_MAXPACKET = 65535
IPTOS_LOWDELAY = 0x10
IPTOS_THROUGHPUT = 0x08
IPTOS_RELIABILITY = 0x04
IPTOS_PREC_NETCONTROL = 0xe0
IPTOS_PREC_INTERNETCONTROL = 0xc0
IPTOS_PREC_CRITIC_ECP = 0xa0
IPTOS_PREC_FLASHOVERRIDE = 0x80
IPTOS_PREC_FLASH = 0x60
IPTOS_PREC_IMMEDIATE = 0x40
IPTOS_PREC_PRIORITY = 0x20
IPTOS_PREC_ROUTINE = 0x00
IPOPT_CONTROL = 0x00
IPOPT_RESERVED1 = 0x20
IPOPT_DEBMEAS = 0x40
IPOPT_RESERVED2 = 0x60
IPOPT_EOL = 0
IPOPT_NOP = 1
IPOPT_RR = 7
IPOPT_TS = 68
IPOPT_SECURITY = 130
IPOPT_LSRR = 131
IPOPT_SATID = 136
IPOPT_SSRR = 137
IPOPT_OPTVAL = 0
IPOPT_OLEN = 1
IPOPT_OFFSET = 2
IPOPT_MINOFF = 4
IPOPT_TS_TSONLY = 0
IPOPT_TS_TSANDADDR = 1
IPOPT_TS_PRESPEC = 2
IPOPT_SECUR_UNCLASS = 0x0000
IPOPT_SECUR_CONFID = 0xf135
IPOPT_SECUR_EFTO = 0x789a
IPOPT_SECUR_MMMM = 0xbc4d
IPOPT_SECUR_RESTR = 0xaf13
IPOPT_SECUR_SECRET = 0xd788
IPOPT_SECUR_TOPSECRET = 0x6bc5
MAXTTL = 255
IPFRAGTTL = 60
IPTTLDEC = 1
IP_MSS = 576

# Helper functions

import re
rx_addr = re.compile('([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)')
#import regex
#rx_addr = regex.compile('\([0-9]+\)\.\([0-9]+\)\.\([0-9]+\)\.\([0-9]+\)')

def dotted_to_int(s, rex=rx_addr):
    rx = rex.match(s)
    if rx == None:
	raise ValueError, "not a valid IP address"
    parts = map(lambda x:chr(x), map(string.atoi, rx.group(1, 2, 3, 4)))
    return string.joinfields(parts, '')

# The basic packet

#class Packet(inet.EncapsPacket):
class Packet:
    """An IP packet.

    Doesn't handle IP options yet (but you have the option of adding
    support).  
    """

    def __init__(self, packet=None, cksum=0):
	if packet:
	    self.__disassemble(packet, cksum)
	else:
	    self.v = IPVERSION
	    self.hl = 5        # this implement punts on options
	    self.tos = IPTOS_PREC_ROUTINE
	    self.len = 20      # begin with header length
	    self.id = 0
	    self.off = 0
	    self.ttl = 0
	    self.p = 0
	    self.sum = 0
	    self.src = os.uname()[1]
	    self.dst = None
	    self.data = ''

    def __repr__(self):
	begin = "<IPv%d id=%d proto=%d src=%s dst=%s datalen=%d " % \
	       (self.v, self.id, self.p, self.src, self.dst,
		self.len - self.hl * 4)
	if len(self.data) == 0:
	    rep = begin + "\'\'>"
	elif len(self.data) < 10:
	    rep = begin + "%s>" % repr(self.data)
	else:
	    rep = begin + "%s>" % repr(self.data[:10] + '...')
	return rep

    def assemble(self, cksum=0):
	"Get a packet suitable for sending over an IP socket."
	# make sure all the data is ready
	self.len = self.hl * 4 + len(self.data)
	self.__parse_addrs()
	# create the packet
	header =  struct.pack('cchhhcc',
			      chr((self.v & 0x0f) << 4 
				  | (self.hl & 0x0f)),    # 4bits each
			      chr(self.tos & 0xff),
			      self.len,
			      self.id,
			      self.off,     # what about flags?
			      chr(self.ttl & 0xff),
			      chr(self.p & 0xff))
	if cksum:
	    self.sum = inet.cksum(header + '\000\000' + self.__src +
				  self.__dst)
	    packet = header + struct.pack('h', self.sum) \
		     + self.__src + self.__dst
	else:
	    packet = header + '\000\000' + self.__src + self.__dst 
	packet = packet + self.data

	self.__packet = inet.iph2net(packet)
	return self.__packet

    def __parse_addrs(self):
	try:
	    self.__src = dotted_to_int(self.src)
	except ValueError:
	    try:
		self.__src = dotted_to_int(socket.gethostbyname(self.src))
	    except ValueError:
		raise ValueError, "invalid source address"
	try:
	    self.__dst = dotted_to_int(self.dst)
	except ValueError:
	    try:
		self.__dst = dotted_to_int(socket.gethostbyname(self.dst))
	    except ValueError:
		raise ValueError, "invalid source address"

    def __unparse_addrs(self):
	src = struct.unpack('cccc', self.src)
	self.src = string.joinfields(map(lambda x:str(ord(x)), src), '.')
	dst = struct.unpack('cccc', self.dst)
	self.dst = string.joinfields(map(lambda x:str(ord(x)), dst), '.')

    def __disassemble(self, raw_packet, cksum=0):
	# Ok, I didn't realize this. The kernel does the checksum for
	# you, even on a raw packet. Plus, the Python cksum code seems
	# to be buggy. It's different than the IP version by ...01010
	packet = inet.net2iph(raw_packet)
	b1 = ord(packet[0])
	self.v = (b1 >> 4) & 0x0f
	self.hl = b1 & 0x0f
	if self.v != IPVERSION:
	    raise ValueError, "cannot handle IPv%d packets" % self.v
	hl = self.hl * 4

	# verify the checksum
	self.sum = struct.unpack('h', packet[10:12])[0] & 0xffff
	if cksum:
	    our_cksum = inet.cksum(packet[:20])
	    if our_cksum != 0:
		raise ValueError, packet

	# unpack the fields
	elts = struct.unpack('cchhhcc', packet[:hl-10])
        # struct didn't do !<> when this was written
	self.tos = ord(elts[1]) 
	self.len = elts[2] & 0xffff
	self.id = elts[3] & 0xffff
	self.off = elts[4] & 0xffff
	self.ttl = ord(elts[5])
	self.p = ord(elts[6])
	self.data = packet[hl:]
	self.src = packet[hl-8:hl-4]
	self.dst = packet[hl-4:hl]
	self.__unparse_addrs()

