##################################################################
# Project    : PYSIDE
# Date       : 8 Aug 2001
##################################################################
import struct
import time
import sha
import os
import hex

pool = [0x7205a72cL, 0x2e3d987aL, 0x23845daaL, 0xf28b4690L,
        0xb50c98a0L, 0xaf3098c3L, 0xd3cbeaefL, 0x9c8e4389L]
poolptr = 0

#
# The CRYPTO class is the base class for all cryptographic methods.
# This class sets up the interface that all other cryptographic
# modules will use.
#
class cipher:
    def __init__(self):
        self.key = 0
        self.num = 0

    #-------------------------------------------------------------------------
    # Name   : GetKey
    # Purpose: Return the current encryption key
    # Receive: << nothing >>
    # Return : the encryption key
    #-------------------------------------------------------------------------
    def GetKey(self):
        """ GetKey """
        
    #-------------------------------------------------------------------------
    # Name   : SetKey
    # Purpose: Set the encryption key
    # Receive: key - The key to use
    # Return : << nothing >>
    #-------------------------------------------------------------------------
    def SetKey(self, key):
        """ SetKey """
        
    #-------------------------------------------------------------------------
    # Name   : Encrypt
    # Purpose: Encrypt the data with the previously provided key
    # Receive: data - The plain text data to be encrypted
    # Return : The encrypted data
    #-------------------------------------------------------------------------
    def Encrypt(self, data):
        """ Encrypt """
        
    #-------------------------------------------------------------------------
    # Name   : Decrypt
    # Purpose: Decrypt the data and return the result
    # Receive: data - The cipher text data to be decrypted
    # Return : The unencrypted data
    #-------------------------------------------------------------------------
    def Decrypt(self, data):
        """ Decrypt """

############################################################################
#    RC6 Class
############################################################################
class rc6(cipher):
    def __init__(self):
        self.key = 0
        self.num = 2

    def rc6_expand(self,rcv):
        cv = [0x00000000L, 0x00000000L, 0x00000000L, 0x00000000L]
        s = [0x00000000L, 0x00000000L, 0x00000000L, 0x00000000L,
             0x00000000L, 0x00000000L, 0x00000000L, 0x00000000L,
             0x00000000L, 0x00000000L, 0x00000000L, 0x00000000L,
             0x00000000L, 0x00000000L, 0x00000000L, 0x00000000L,
             0x00000000L, 0x00000000L, 0x00000000L, 0x00000000L,
             0x00000000L, 0x00000000L, 0x00000000L, 0x00000000L,
             0x00000000L, 0x00000000L, 0x00000000L, 0x00000000L,
             0x00000000L, 0x00000000L, 0x00000000L, 0x00000000L,
             0x00000000L, 0x00000000L, 0x00000000L, 0x00000000L,
             0x00000000L, 0x00000000L, 0x00000000L, 0x00000000L,
             0x00000000L, 0x00000000L, 0x00000000L, 0x00000000L]
        l = [0x00000000L, 0x00000000L, 0x00000000L, 0x00000000L,
             0x00000000L, 0x00000000L, 0x00000000L, 0x00000000L]
        s[0] = 0xb7e15163L
        cv[0] = rcv[0]
        cv[1] = rcv[1]
        cv[2] = rcv[2]
        cv[3] = rcv[3]

        for k in range(1,44):
            s[k] = (s[k-1] + 0x9e3779b9L) & 0xffffffffL

        for k in range(4):
            l[k] = cv[k]
        #    l[k] = struct.unpack("L", struct.pack("!L", cv[k]))[0]
        
        t = 3
        a = b = 0L
        i = j = 0

        for k in range(132):
            #a = rotl((s[i] + a + b) & 0xffffffffL, 3)
            a = (((((s[i] + a + b) & 0xffffffffL) << ((3)&31L))&0xffffffffL) \
                 ^ (((s[i] + a + b) & 0xffffffffL) >> (32 - ((3)&31))))
            b = (b + a) & 0xffffffffL
            tmp = b&0x1fL
            #b = rotl((l[j]+b) & 0xffffffffL,tmp)
            b = (((((l[j]+b) & 0xffffffffL) << ((tmp)&31))&0xffffffffL) \
                 ^ (((l[j]+b) & 0xffffffffL) >> (32 - ((tmp)&31))))
            s[i] = a
            l[j] = b
            if i == 43:
                i = 0
            else:
                i = i+1

            if j == t:
                j = 0
            else:
                j = j+1
        #for i in range(44):
        #    print hex.str(s[i])
        return s

    def GetKey(self):
        return self.key

    def SetKey(self,key):
	self.key = key
        self.key_sched = self.rc6_expand(self.key)
        
    def rc6_enc(self,data):
        #temp = struct.unpack("LLLL", struct.pack("!LLLL",data[0],data[1],
        #                                          data[2],data[3]))
        temp = data
        data = [temp[0],temp[1],temp[2],temp[3]]
        data[1] = (data[1] + self.key_sched[0])&0xffffffffL
        data[3] = (data[3] + self.key_sched[1])&0xffffffffL

        for i in range(1,21):
            t = (data[1]*(2*data[1]+1))&0xffffffffL
            #t = rotl(t,5)
            t = ((((t) << ((5)&31))&0xffffffffL) \
                 ^ (((t)&0xffffffffL) >> (32 - ((5)&31))))

            u = (data[3]*(2*data[3]+1))&0xffffffffL
            #u = rotl(u,5)
            u = ((((u) << ((5)&31))&0xffffffffL) \
                 ^ (((u)&0xffffffffL) >> (32 - ((5)&31))))
            
            data[0] = data[0] ^ t
            #data[0] = rotl(data[0],u)
            data[0] = ((((data[0]) << ((u)&31))&0xffffffffL) \
                 ^ (((data[0])&0xffffffffL) >> (32 - ((u)&31))))
            data[0] = (data[0] + self.key_sched[2*i])&0xffffffffL

            data[2] = data[2] ^ u
            #data[2] = rotl(data[2],t)
            data[2] = ((((data[2]) << ((t)&31))&0xffffffffL) \
                 ^ (((data[2])&0xffffffffL) >> (32 - ((t)&31))))
            data[2] = (data[2] + self.key_sched[2*i+1])&0xffffffffL

            tmp_int = data[0]
            data[0] = data[1]
            data[1] = data[2]
            data[2] = data[3]
            data[3] = tmp_int

        data[0] = (data[0] + self.key_sched[42])&0xffffffffL
        data[2] = (data[2] + self.key_sched[43])&0xffffffffL
        #return struct.unpack(">LLLL", struct.pack("<LLLL",data[0],data[1],
        #                                          data[2],data[3]))
        return (data[0],data[1],data[2],data[3])

    def rc6_dec(self,data):
        #tmp = struct.unpack("<LLLL", struct.pack(">LLLL",data[0],data[1],
        #                                          data[2],data[3]))
        tmp = data
        data = [tmp[0],tmp[1],tmp[2],tmp[3]]
        if data[2] >= self.key_sched[43]:
            data[2] = (data[2] - self.key_sched[43])
        else:
            data[2] = 0x100000000L - (self.key_sched[43] - data[2])
        if data[0] >= self.key_sched[42]:
            data[0] = (data[0] - self.key_sched[42])
        else:
            data[0] = 0x100000000L - (self.key_sched[42] - data[0])

        i = 20
        while i >= 1:
            tmp_int = data[3]
            data[3] = data[2]
            data[2] = data[1]
            data[1] = data[0]
            data[0] = tmp_int
            t = (data[1]*(2*data[1]+1))&0xffffffffL
            #t = rotl(t,5)
            t = ((((t) << ((5)&31))&0xffffffffL) \
                 ^ (((t)&0xffffffffL) >> (32 - ((5)&31))))
            
            u = (data[3]*(2*data[3]+1))&0xffffffffL
            #u = rotl(u,5)
            u =((((u) << ((5)&31))&0xffffffffL) \
                 ^ (((u)&0xffffffffL) >> (32 - ((5)&31))))

            if data[2] >= self.key_sched[2*i+1]:
                data[2] = (data[2] - self.key_sched[2*i+1])
            else:
                data[2] = 0x100000000L - (self.key_sched[2*i+1] - data[2])
            #data[2] = rotr(data[2],t)
            data[2] = ((((data[2])&0xffffffffL) >> (((t) & 0x1f))) \
                       | (((data[2]) << (((32 - ((t) & 0x1f)))))&0xffffffffL))
            data[2] = data[2] ^ u

            if data[0] >= self.key_sched[2*i]:
                data[0] = (data[0] - self.key_sched[2*i])
            else:
                data[0] = 0x100000000L - (self.key_sched[2*i] - data[0])
            #data[0] = rotr(data[0],u)
            data[0] = ((((data[0])&0xffffffffL) >> (((u) & 0x1f))) \
                       | (((data[0]) << (((32 - ((u) & 0x1f)))))&0xffffffffL))
            data[0] = data[0] ^ t
            
            i = i - 1

        if data[3] >= self.key_sched[1]:
            data[3] = (data[3] - self.key_sched[1])
        else:
            data[3] = 0x100000000L - (self.key_sched[1] - data[3])
        if data[1] >= self.key_sched[0]:
            data[1] = (data[1] - self.key_sched[0])
        else:
            data[1] = 0x100000000L - (self.key_sched[0] - data[1])
        #return struct.unpack(">LLLL", struct.pack("<LLLL",data[0],data[1],
        #                                          data[2],data[3]))
        return (data[0],data[1],data[2],data[3])

    def Encrypt(self,pt):
        iv = struct.unpack("!LLLL", pt[:16])
        ct = self.rc6_enc(iv)
        pt = struct.pack("!LLLL",ct[0],ct[1],ct[2],ct[3]) + pt[16:]

        data_size = len(pt)
        i = 16
        mi = [0L,0L,0L,0L]
        # Handle the bulk of the data
        while i < (data_size & 0xfffffff0L):
            tmp = struct.unpack("!LLLL", pt[i:i+16])
            mi[0] = tmp[0] ^ ct[0]
            mi[1] = tmp[1] ^ ct[1]
            mi[2] = tmp[2] ^ ct[2]
            mi[3] = tmp[3] ^ ct[3]
            ct = self.rc6_enc(mi)
            pt = pt[0:i] + struct.pack("!LLLL",ct[0],ct[1],ct[2],ct[3]) + pt[i+16:]
            i = i + 16

        # Handle non-full block
        if data_size & 0xfL:
            t = struct.pack("LLLL",0,0,0,0)
            t = pt[i:] + t[data_size-i:]
            ct = self.rc6_enc(ct)
            tmp = struct.unpack("!LLLL",t)
            t = struct.pack("!LLLL",tmp[0] ^ ct[0], tmp[1] ^ ct[1],
                            tmp[2] ^ ct[2], tmp[3] ^ ct[3])
            pt = pt[0:i] + t[0:data_size-i]
        return pt

    def Decrypt(self,ct):
        data_size = len(ct)
        i = data_size & 0x7ffffff0
        pt = struct.unpack("!LLLL",ct[i-16:i])
                           
        # Handle the non-full block
        if data_size & 0xfL:
            t = struct.pack("LLLL",0,0,0,0)
            t = ct[i:data_size] + t[data_size-i:]
            tmp = self.rc6_enc(pt)
            t = struct.unpack("!LLLL",t)
            t = struct.pack("!LLLL",t[0] ^ tmp[0], t[1] ^ tmp[1],
                            t[2] ^ tmp[2], t[3] ^ tmp[3])
            ct = ct[0:i] + t[0:data_size-i]
        
        # Handle the bulk of the data
        while i > 16:
            i = i - 16
            tmp = self.rc6_dec(pt)
            pt = struct.unpack("!LLLL",ct[i-16:i])
            ct = ct[0:i] + struct.pack("!LLLL",tmp[0] ^ pt[0], tmp[1] ^ pt[1],
                                       tmp[2] ^ pt[2], tmp[3] ^ pt[3]) \
                                       + ct[i+16:]

        tmp = self.rc6_dec(pt)
        ct = struct.pack("!LLLL",tmp[0],tmp[1],tmp[2],tmp[3]) + ct[16:]
        return ct
   
        
        
############################################################################
#    RC5 Class
############################################################################
class rc5(cipher):
    def __init__(self):
        self.RC5_B = 12
        self.RC5_R = 24
        self.RC5_P = 0xb7e15163L
        self.RC5_Q = 0x9e3779b9L
        self.RC5_SLEN = 2*(self.RC5_R+1)
        self.key = 0
        self.num = 1

    #-------------------------------------------------------------------------
    # Name   : rc5_expand
    # Purpose: Expand the 96bit key to form the key schedule
    # Receive: rcv - The 96bit key
    # Return : << nothing >>
    #-------------------------------------------------------------------------
    def rc5_expand(self, rcv):
        cv = [0x00000000L, 0x00000000L, 0x00000000L]
        s =  [0x00000000L, 0x00000000L, 0x00000000L,
              0x00000000L, 0x00000000L, 0x00000000L,
              0x00000000L, 0x00000000L, 0x00000000L,
              0x00000000L, 0x00000000L, 0x00000000L,
              0x00000000L, 0x00000000L, 0x00000000L,
              0x00000000L, 0x00000000L, 0x00000000L,
              0x00000000L, 0x00000000L, 0x00000000L,
              0x00000000L, 0x00000000L, 0x00000000L,
              0x00000000L, 0x00000000L, 0x00000000L,
              0x00000000L, 0x00000000L, 0x00000000L,
              0x00000000L, 0x00000000L, 0x00000000L,
              0x00000000L, 0x00000000L, 0x00000000L,
              0x00000000L, 0x00000000L, 0x00000000L,
              0x00000000L, 0x00000000L, 0x00000000L,
              0x00000000L, 0x00000000L, 0x00000000L,
              0x00000000L, 0x00000000L, 0x00000000L,
              0x00000000L, 0x00000000L]
        cv[0] = rcv[0]
        cv[1] = rcv[1]
        cv[2] = rcv[2]
        
        s[0] = self.RC5_P
        
        i = 1
        while i<self.RC5_SLEN:
            s[i] = s[i-1] + self.RC5_Q
            i = i + 1

        i=0
        j=0
        a=0x0L
        b=0x0L
        h=0
        while h<3*self.RC5_SLEN:
            s[i] = ((((s[i]+a+b)&0xffffffffL)<<((3)&0x1fL))\
                    |(((s[i]+a+b)&0xffffffffL)>>((32-(3))&0x1fL))) \
                    & 0xffffffffL
            a = s[i]
            cv[j] = ((((cv[j]+a+b)&0xffffffffL)<<((a+b)&0x1fL))\
                     |(((cv[j]+a+b)&0xffffffffL)>>((32-(a+b))&0x1fL))) \
                     & 0xffffffffL
            b = cv[j]
            i = (i+1)%self.RC5_SLEN
            j = (j+1)%(self.RC5_B/4)
            h = h + 1
        return s

    #-------------------------------------------------------------------------
    # Name   : GetKey
    # Purpose: Return the current encryption key
    # Receive: << nothing >>
    # Return : the encryption key
    #-------------------------------------------------------------------------
    def GetKey(self):
        return self.key

    #-------------------------------------------------------------------------
    # Name   : SetKey
    # Purpose: Set the encryption key
    # Receive: key - The key to use
    # Return : << nothing >>
    #-------------------------------------------------------------------------
    def SetKey(self,key):
	self.key = key
        self.key_sched = self.rc5_expand(self.key)
    
    #-------------------------------------------------------------------------
    # Name   : rc5_enc
    # Purpose: Perform rc5 encryption
    # Receive: a - The first 32bit word to be encrypted
    #          b - The second 32bit word to be encrypted
    # Return : The encrypted values for a and b
    #-------------------------------------------------------------------------
    def rc5_enc(self, a, b):
        zzz = 1
        a = (a + self.key_sched[0])&0xffffffffL
        b = (b + self.key_sched[1])&0xffffffffL
        while zzz <= self.RC5_R:
            a = (((((a^b)&0xffffffffL) << (b&0x1fL))&0xffffffffL | \
                  (((a^b)&0xffffffffL) >> ((32-(b))&0x1fL))) + \
                 self.key_sched[2*zzz])&0xffffffffL
            b = (((((a^b)&0xffffffffL) << (a&0x1fL))&0xffffffffL | \
                  (((a^b)&0xffffffffL) >> ((32-(a))&0x1fL))) + \
                 self.key_sched[2*zzz+1])&0xffffffffL
            zzz = zzz + 1
        return (a, b)

    #-------------------------------------------------------------------------
    # Name   : rc5_dec
    # Purpose: Perform rc5 decryption
    # Receive: a - The first 32bit word to be decrypted
    #          b - The second 32bit word to be decrypted
    # Return : The plain-text values for a and b
    #-------------------------------------------------------------------------
    def rc5_dec(self, a, b):
        zzz = self.RC5_R
        while zzz >= 1:
            b = (((((b-self.key_sched[2*zzz+1])&0xffffffffL) >> (a&0x1fL)) |\
                  (((b-self.key_sched[2*zzz+1])&0xffffffffL) << \
                   ((32-a)&0x1fL))&0xffffffffL) ^ a)&0xffffffffL
            a = (((((a-self.key_sched[2*zzz])&0xffffffffL) >> (b&0x1fL)) | \
                  (((a-self.key_sched[2*zzz])&0xffffffffL) << \
                   ((32-b)&0x1fL))&0xffffffffL) ^b )&0xffffffffL
            zzz = zzz - 1
        b = (b - self.key_sched[1])&0xffffffffL
        a = (a - self.key_sched[0])&0xffffffffL
        return (a, b)

    #-------------------------------------------------------------------------
    # Name   : Encrypt
    # Purpose: Encrypt the data with the previously provided key
    # Receive: data - The plain text data to be encrypted
    # Return : The encrypted data
    #-------------------------------------------------------------------------
    def Encrypt(self, pt):
        auth_0 = (struct.unpack("!L", pt[0:4]))[0]
        auth_1 = (struct.unpack("!L", pt[4:8]))[0]
        ct = self.rc5_enc(auth_0, auth_1)
        pt = struct.pack("!LL", ct[0], ct[1]) + pt[8:len(pt)]

        data_size = len(pt) - 8
        i = 0
        # Handle the bulk of the data
        while i < (data_size & 0xfffffff8L):
            mia = (struct.unpack("!L", pt[i:i+4]))[0]
            mib = (struct.unpack("!L", pt[i+4:i+8]))[0]
            ct = self.rc5_enc(mia, mib)
            newXor1 = (struct.unpack("L", pt[i+8:i+12]))[0]
            newXor1 = newXor1 ^ (struct.unpack("L", struct.pack("!L", ct[0])))[0]
            newXor2 = (struct.unpack("L", pt[i+12:i+16]))[0]
            newXor2 = newXor2 ^ (struct.unpack("L", struct.pack("!L", ct[1])))[0]
            pt = pt[0:i+8] + struct.pack("LL", newXor1, newXor2) + pt[i+16:len(pt)]
            i = i + 2*4
        
        # Handle non-full block
        if data_size & 0x7L:
            t = struct.pack("LL",0,0)
            i = int(data_size & 0xfffffff8L)
            mia = (struct.unpack("!L", pt[i:i+4]))[0]
            mib = (struct.unpack("!L", pt[i+4:i+8]))[0]
            t = pt[i+8:i+8+(data_size-i)] + t[(data_size-i):8]
            ct = self.rc5_enc(mia, mib)
            ta = struct.pack("L", (struct.unpack("L", t[0:4]))[0] ^ \
                             (struct.unpack("!L", struct.pack("L", ct[0])))[0])
            t = ta + struct.pack("L", (struct.unpack("L", t[4:8]))[0] ^ \
                                 (struct.unpack("!L",struct.pack("L",ct[1])))[0])
            pt = pt[0:i+8] + t[0:data_size-i]
        return pt

    #-------------------------------------------------------------------------
    # Name   : Decrypt
    # Purpose: Decrypt the data and return the result
    # Receive: data - The cipher text data to be decrypted
    # Return : The unencrypted data
    #-------------------------------------------------------------------------
    def Decrypt(self, ct):
        data_size = len(ct) - 8

        # Handle non-full block
        if data_size & 0x7L:
            t = struct.pack("LL",0,0)
            i = int(data_size & 0xfffffff8L)
            mia = (struct.unpack("!L", ct[i:i+4]))[0]
            mib = (struct.unpack("!L", ct[i+4:i+8]))[0]
            t = ct[i+8:i+8+(data_size-i)] + t[(data_size-i):8]
            pt = self.rc5_enc(mia, mib)
            ta = struct.pack("L", (struct.unpack("L", t[0:4]))[0] ^ \
                             (struct.unpack("!L", struct.pack("L", pt[0])))[0])
            t = ta + struct.pack("L", (struct.unpack("L", t[4:8]))[0] ^ \
                                 (struct.unpack("!L",struct.pack("L",pt[1])))[0])
            ct = ct[0:i+8] + t[0:data_size-i]

        # Handle the bulk of the data
        i = ((data_size - 8) & 0xfffffff8)
        while i >= 0:
            mia = (struct.unpack("!L", ct[i:i+4]))[0]
            mib = (struct.unpack("!L", ct[i+4:i+8]))[0]
            pt = self.rc5_enc(mia, mib)
            newXor1 = (struct.unpack("L", ct[i+8:i+12]))[0]
            newXor1 = newXor1 ^ (struct.unpack("L", struct.pack("!L", pt[0])))[0]
            newXor2 = (struct.unpack("L", ct[i+12:i+16]))[0]
            newXor2 = newXor2 ^ (struct.unpack("L", struct.pack("!L", pt[1])))[0]
            ct = ct[0:i+8] + struct.pack("LL", newXor1, newXor2) + ct[i+16:len(ct)]
            i = i - 2*4

        auth_0 = (struct.unpack("!L", ct[0:4]))[0]
        auth_1 = (struct.unpack("!L", ct[4:8]))[0]
        pt = self.rc5_dec(auth_0, auth_1)
        ct = struct.pack("!LL", pt[0], pt[1]) + ct[8:len(ct)]
        return ct

############################################################################
#    Random Stuff
############################################################################
def AddSeed(sample):
    global pool
    global poolptr
    ind = {}
    out = {}
    i=0
    
    while i < len(sample)-1:
        ind[0] = (sample[i] + pool[poolptr]) & 0xffffffffL
        ind[1] = (sample[i+1] + pool[(poolptr+1)%8]) & 0xffffffffL
        sha1 = sha.new(struct.pack("LL",ind[0], ind[1]))
        out = struct.unpack("LLLLL",sha1.digest())
        pool[poolptr] = pool[poolptr] ^ out[0]
        poolptr = poolptr + 1
        if poolptr >= 8:
            poolptr = 0
        pool[poolptr] = pool[poolptr] ^ out[1]
        i = i + 2

def GetRandom():
    global pool
    global poolptr
    sample = {}
    ret = ''
    cmds = ["cat /etc/passwd `find /proc -name usage 2>/dev/null`",
            "ps laxww 2>/dev/null",
            "ls -alni /tmp/. 2>/dev/null",
            "w 2>/dev/null",
            "netstat -an 2>/dev/null",
            "dd if=/dev/urandom bs=128 count=2 2>/dev/null"]

    curr = time.time()
    
    sample[0] = long(os.getpid())
    sample[1] = long(curr - (float(long(curr))*1000000))
    AddSeed(sample)

    for i in range(len(cmds)):
        #print "Running '",cmds[i],"' to get random data"
        f = os.popen(cmds[i])
        d = f.read()
        f = None
        for j in range(len(d)/4):
            sample[j] = (struct.unpack("L",d[j*4:j*4+4]))[0]
        #print len(sample)
        AddSeed(sample)
        sample = {}

    return struct.pack("LLLLLLLL",pool[0],pool[1],pool[2],
                       pool[3],pool[4],pool[5],pool[6],pool[7])
