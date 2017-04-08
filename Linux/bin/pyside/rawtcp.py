from socket import *
import crypto
import struct
import string

class MyPacket:
    def __init__(self):
        self.saddr = 0x00000000L
        self.daddr = 0x00000000L
        self.sport = 0x0000L
        self.dport = 0x0000L
        self.syn   = 0x0L

    def ConvertIP(self, ip):
        if( type(ip) == type('') ):
            ipParts = string.splitfields(ip,'.')
            if len(ipParts) == 4:
                ipStr = chr(eval(ipParts[0]))
                ipStr = ipStr+chr(eval(ipParts[1]))
                ipStr = ipStr+chr(eval(ipParts[2]))
                ipStr = ipStr+chr(eval(ipParts[3]))
            else:
                #ipStr = ip
                raise ValueError, ip
        else:
            ipStr = struct.pack("!L",ip)
        return ipStr

    def setLocalAddr(self, remoteAddr):
        sock       = socket(AF_INET, SOCK_RAW, IPPROTO_UDP)
        sock.connect((remoteAddr, 500))
        name       = sock.getsockname()
        self.saddr = self.ConvertIP(name[0])

    def setRemoteAddr(self, remoteAddr):
        self.daddr = self.ConvertIP(remoteAddr)
        self.setLocalAddr(remoteAddr)

    def createPacket(self, daddr, dport, flags):
        rand  = crypto.GetRandom()

        # Set the source port
        if self.sport == 0:
            self.sport = struct.unpack("H", rand[:2])[0]
            if self.sport < 10000:
                self.sport = self.sport + 10000
        
        # Set the ack
        if flags != 2:
            ack = struct.unpack("L", rand[2:6])[0]
            self.syn = self.syn + 1L
        else:
            ack = 0

        self.setRemoteAddr(daddr)
        
        # Create the IP header first
        ipHdr = struct.pack("!BBHHHBBH", \
                            0x45, 0, 60, \
                            0, 0, \
                            128, 6, 0)
        ipHdr = ipHdr + self.saddr + self.daddr

        # Next, the TCP header
        tcp = struct.pack("!HHLLBBHHH", \
                          self.sport, dport, \
                          self.syn, \
                          ack, \
                          0xa0, flags, 4096, \
                          0, 0)
        ipHdr = ipHdr + tcp

        # Next, the TCP options
        opt = struct.pack("!BBHBBBBLLBBBB",
                          2, 4, 0x05b4, \
                          4, 2, \
                          8, 10, 0, 0, \
                          1, \
                          3, 3, 0)
        ipHdr = ipHdr + opt
        return ipHdr
    
                          
                            
    

def sendFakeConnection(ipAddr, tcpPort):
    sock = socket(AF_INET, SOCK_RAW, IPPROTO_TCP)
    sock.setsockopt(SOL_IP, IP_HDRINCL, 1)

    # send syn
    pkt = MyPacket()
    syn = pkt.createPacket(ipAddr,tcpPort, 2)
    sock.sendto(syn, (ipAddr,tcpPort))

    # send ack
    ack = pkt.createPacket(ipAddr, tcpPort, 16)
    sock.sendto(ack, (ipAddr,tcpPort))
    
    sock.close()
    
