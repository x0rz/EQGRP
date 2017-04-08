from socket import *
import struct
import base
import crypto
import inet

class protocol(base.Protocol):
    def __init__(self):
        base.Protocol.__init__(self)
        self.sock = None

    def SendTo(self,data):
        data_cksum = inet.cksum( '\000\000\000\000' + \
                                 struct.pack("!L",0xffffff00L) + data)
        auth_0 = struct.pack("HH",0,data_cksum)
        auth_1 = struct.pack("!L",0xffffff00L)

        msg = auth_0 + auth_1 + data
        msg = self.implant.cipher.Encrypt(msg)
        self.sock.send(msg)

    def RecvFrom(self):
        stuff = self.sock.recv(1500)
        # Decrypt
        pt = self.implant.cipher.Decrypt(stuff)
        
        if inet.cksum(pt) != 0:
            print "Auth[0] checksum is incorrect"
            raise ValueError, pt

        if(struct.unpack("!L",pt[4:8])[0] & 0x000000FFL != 0x0L):
            print "Data received in the low order byte of auth[1]"
            raise ValueError, pt

        self.data = pt[8:]
        return self.data

base.RegisterProtocol("tcpstream",protocol)
