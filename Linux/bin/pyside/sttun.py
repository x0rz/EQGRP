import base
import time

class STTUN(base.Implant):
    def __init__(self, session, proto):
        base.Implant.__init__(self,session,proto)
        self.name = 'STTUN'
        self.newCV = None
        
    def RegisterCommands(self):
        self.AddCommand("rediradd",  STCMD_REDIRADD)
        self.AddCommand("redirlist", STCMD_REDIRLIST)
        self.AddCommand("redirrm",   STCMD_REDIRRM)

class STCMD_REDIRADD(base.Command):
    def __init__(self):
        base.Command.__init__(self)
        self.name = "rediradd"
        self.usage = "rediradd"
        self.info = "This does nothing...no not use"
        self.redir = None

    def run(self,protocol,attacker,target,
            opt0=None,opt1=None,opt2=None,opt3=None,opt4=None,opt5=None,
            opt6=None,opt7=None,opt8=None,opt9=None,first=1):
        return(1,"all good", 0)

class STCMD_REDIRLIST(base.Command):
    def __init__(self):
        base.Command.__init__(self)
        self.name = "redirlist"
        self.usage = "redirlist"
        self.info = "Lists all local redirect rules"
        self.redir = None

    def ConvertToDot(self, ip):
        if type(ip) == type('a'):
            ip = struct.unpack("!L",ip)[0]
        return "%d.%d.%d.%d" % ((int)(ip / 16777216) & 0xFFL,\
                                (int)(ip / 65536) & 0xFFL,\
                                (int)(ip / 256) & 0xFFL,\
                                ip & 0xFFL)

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

    def parseReturn(self):
        self.rule      = self.data[0]
        self.longevity = time.ctime(self.data[1])[4:]
        self.connto    = self.TimeConvert(self.data[2])
        self.redirip   = self.ConvertToDot(self.data[3])
        self.targetip  = self.ConvertToDot(self.data[4])
        self.flags     = self.data[5]
        self.srcport   = self.data[6]
        self.dstport   = self.data[7]
        self.protocol  = self.data[8]

        if self.flags & 0x40L:
            self.protocol = "ALL"
        else:
            if self.protocol == 6:
                self.protocol = "TCP"
            elif self.protocol == 17:
                self.protocol = "UDP"
            elif self.protocol == 1:
                self.protocol = "ICMP"
            else:
                self.protocol = "%d" %(self.protocol)

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
        if not (self.flags & 0x30L):
            self.opts = self.opts + '-nocrypto '
            
    def displayCurrent(self):
        if self.protocol == "ALL":
            res = "%d %s %s <=> %s %s\nConnTimeout: %s  Expires %s\n\n" %\
                  (self.rule,self.active,self.redirip,self.targetip,self.opts,\
                   self.connto,self.longevity)
        else:
            res = "%d %s %s:%d <=> %s:%d %s\nConnTimeout: %s  Expires %s\n\n" %\
                  (self.rule,self.active,self.redirip,self.srcport,\
                   self.targetip,self.dstport,self.opts,\
                   self.connto,self.longevity)
        return res

    def run(self):
        res = ""
        self.more = 1
        last = 0L
        while self.more:
            self.data = base.redir.redirlist(last)
            if self.data != None:
                self.parseReturn()
                res = res + self.displayCurrent()
                last = self.rule
            else:
                self.more = 0
                
        return(1,res)

class STCMD_REDIRRM(base.Command):
    def __init__(self):
        base.Command.__init__(self)
        self.name = "redirrm"
        self.usage = "redirrm <rule>"
        self.info = "Remove a local redirect rule"
        self.redir = None

    def run(self,rulenum):
        if base.redir.delete(rulenum) == 0:
            return(1,"Local rule removed")
        else:
            return(0,"Error removing rule")
    
base.RegisterImplant('STTUN', STTUN)
