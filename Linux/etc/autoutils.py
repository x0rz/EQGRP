#!/bin/env python

import os
import re
import sys
import time
import pickle
import random
import socket
import os.path
import traceback
import subprocess
from optparse import OptionParser

VERSION='1.1.0.7'

COLOR = {
    'success' : '\33[2;32m',    # Green
    'fail'    : '\033[2;31m',   # Red
    'bad'     : '\033[31;07m',  # Red Highlight
    'warn'    : '\033[3;43m',   # Yellow Highlight
    'normal'  : '\033[0;39m',   # Black
    'note'    : '\033[0;34m'    # NOPEN Blue
}

class autoutils:

    def __init__(self):

        # Set the Colors
        self.COLOR_SUCCESS    = COLOR['success']
        self.COLOR_FAILURE    = COLOR['fail']
        self.COLOR_BADFAILURE = COLOR['bad']
        self.COLOR_WARNING    = COLOR['warn']
        self.COLOR_NORMAL     = COLOR['normal']
        self.COLOR_NOTE       = COLOR['note']

        # Set directories
        self.opdir      = '/current'
        self.opup       = '%s/up' % self.opdir
        self.opbin      = '%s/bin' % self.opdir
        self.opetc      = '%s/etc' % self.opdir
        self.opdown     = '%s/down' % self.opdir
        self.optmp      = '%s/tmp' % self.opdir

        # Set Python module path
        sys.path = [self.opetc,self.optmp] + sys.path

        # must have this
        if not os.environ.has_key('NOPEN_AUTOPORT'):
            sys.stderr.write('Could not find NOPEN_AUTOPORT variable. ' +
                             'Must call from NOPEN -gs.\n')
            sys.exit(1)

        # Nopen ENV Variables

        self.nopen_autoport   = int(os.environ['NOPEN_AUTOPORT'])
        self.nopen_serverinfo = os.environ['NOPEN_SERVERINFO']
        self.nopen_clientver  = os.environ['NOPEN_CLIENTVER']
        self.nopen_mylog      = os.environ['NOPEN_MYLOG']
        self.nopen_rhostname  = os.environ['NOPEN_RHOSTNAME']
        self.nopen_nhome      = os.environ['NHOME']
        self.nopen_mypid      = os.environ['NOPEN_MYPID']

        self.optargetcommands = os.path.join(
            self.opdown, '%s_targetcommands' % self.nopen_rhostname)

        # This is the nopen autoport socket
        self.connected    = False
        self.nopen_socket = None
        self.nopen        = None

        self.pid = os.getpid()
        self.hidden_dir = ''
        self.status = {}
        self.statusFile = os.path.join(self.optmp, 
            '%s.%s_pystatus' % (self.nopen_rhostname, self.nopen_mypid))
        self.stateFile = os.path.join(self.optmp, '%s_pystate' % self.nopen_rhostname)
        self.state = {
            'linux': False,
            'solaris': False,
            'hpux': False,
            'hpux_it': False
            }

        self.tunnel = None

        self.perl_return = False
        self.perl_sock_file = ''

        return

    #
    # Saves self.state dictionary into a file
    #
    def saveState(self):

        f = open(self.stateFile, 'wb')
        pickle.dump(self.state, f)
        f.close()

    #
    # Loads a previously saved state
    #
    def loadState(self):

        if os.path.exists(self.stateFile):
            f = open(self.stateFile, 'rb')
            self.state = pickle.load(f)
            f.close()

    #
    # Yea...
    #
    def help(self, word):

        print '     ___     '
        print '  |_____ |   '
        print '  ||   | |   '
        print '  ||   | |   '
        print '  ||O O| |  Looks like you\'re trying to %s' % str(word).upper()
        print '  ||   | |  Want some help?'
        print '  || U | |   '
        print '  ||   | ||  '
        print '  ||   | ||  '
        print '  |||  | ||  '
        print '  |||  | ||  '
        print '  |||  | ||  '
        print '  |||  | ||  '
        print '  |||__| ||  '
        print '  ||_____||  '
        print '  |_______|  '

        return

    #
    # Takes out any autoutils stuff and then calls the parser's
    # parse_args() method.
    # args should be an array without the program name (sys.argv[1:])
    #
    def parseArgs(self, parser, args, values=None):

        if len(args) > 0:
            if args[0].startswith('perl:'):
                self.perl_return = True
                self.perl_sock_file = sys.argv[1].split(':', 1)[1]

                args = args[1:]

        return parser.parse_args(args, values)

    #
    # Makes the connection to the NOPEN autoport.
    # This takes care of the forking too.
    #
    def connect(self):

        os.close(sys.stdout.fileno())
        sys.stdout = sys.stderr

        if not self.connected:
            self.nopen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.nopen_socket.connect(('127.0.0.1', self.nopen_autoport)) 
            self.nopen = self.nopen_socket.makefile()

            self.connected = True

        pid = os.fork()

        if pid != 0:
            self.nopen.close()
            self.nopen_socket.close()
            sys.exit(0)

        self.pid = os.getpid()

        self.nopen.write('#NOGS\n')
        self.nopen.flush()

        # going to run -status every time because something could change
        # between runs and don't want to get caught with something bad.
        self.parsestatus()

        #if not os.path.exists(self.statusFile):
        #    self.parsestatus()
        #else:
        #    f = open(self.statusFile, 'rb')
        #    self.status = pickle.load(f)
        #    f.close()

        self.loadState()
        self.saveState()
        
        return self.nopen

    #
    # Does any final stuff with the output, like sending it to a calling
    # perl script, then returns back a string of the argument, or unchanged
    # if mkstr is False.
    #
    def finish(self, ret=None, mkstr=True):

        if self.connected:
            self.cleanup()

        if not ret:
            ret = ''

        if mkstr:
            if ret.__class__() == []:
                ret_str = '\n'.join(ret) + '\n'
            else:
                ret_str = str(ret)

            ret = ret_str

        if self.perl_return:
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM);
                sock.connect((self.perl_sock_file))
                sock.send(ret_str)
                sock.close()
            except:
                print 'Could not connect to %s' % self.perl_sock_file

        return ret

    #
    # Returns a list of any hidden directories found.
    #
    def getHidden(self, refresh=False):

        tmpfile_chrs = '[A-Za-z0-9_-]' * 6

        parent_dirs_old = [
            '/var/tmp',
            '/lib',
            '/dev',
            '/etc',
            '/',
            ]

        dirs_old = [
            '.%s' % ('[A-Fa-f0-9]' * 16),
            '.tmp%s' % tmpfile_chrs,
            ]

        dir_regexs = [
            '/var/spool/.cron%s.bak' % tmpfile_chrs,
            '/var/log/.fsck%s.bak' % tmpfile_chrs,
            '/lib/.security%s.lock' % tmpfile_chrs,
            '/dev/.usb%s.lock' % tmpfile_chrs,
            '/etc/.dev%s.save' % tmpfile_chrs,
            '/var/tmp/.%s-unix' % tmpfile_chrs,
            '/.opt%s.save' % tmpfile_chrs,
            ]

        for pd in parent_dirs_old:
            for d in dirs_old:
                dir_regexs.append(os.path.join(pd, d))

        parent_dirs = []

        for dr in dir_regexs:
            d = os.path.dirname(dr)

            if not d in parent_dirs:
                parent_dirs.append(d)

        lsfile = os.path.join(self.opdown,
                              'stoichunt.%s' % self.nopen_rhostname)

        if not os.path.exists(lsfile):
            refresh = True

        if refresh:
            self.preserveFiles(lsfile)

            output, nopenlines, outputlines = self.doit(
                '-ls %s > T:%s' % (' '.join(parent_dirs), lsfile))
        else:
            outputlines = file_readlines(lsfile)

        files = [x.strip('\n').split(None, 9)[-1] for x in outputlines]

        dirs = []

        for f in files:
            for r in dir_regexs:
                if re.match(r, f):
                    dirs.append((f, r))

        if not refresh:
            # do a listing of the specific dir's regex to confirm it's there,
            # only if it wasn't just done
            tolist = ' '.join([x[1] for x in dirs])

            if tolist:
                output, nopenlines, outputlines = self.doit('-ls -d %s' % tolist)
                dirs = [x.strip('\n').split(None, 9)[-1] for x in outputlines]
        else:
            dirs = [x[0] for x in dirs]

        return dirs


    #
    # Ask a question prompt and return the input.
    #
    def getInput(self, prompt, default=None, color=COLOR['fail']):

        if not prompt:
            return None
        
        if default:
            print '%s%s [%s]:%s' % (color, prompt, default, self.COLOR_NORMAL),
        else:
            print '%s%s:%s' % (color, prompt, self.COLOR_NORMAL),

        sys.stdout.flush()
        answer = raw_input().strip()

        if (not answer or answer == '') and default:
            return default

        return answer

    #
    # pause and wait for a <Return>.
    #
    def pause(self):
        print
        print '%sHit <Return> to continue.%s' % (COLOR['warn'],COLOR['normal'])
        sys.stdout.flush()
        answer = raw_input().strip()
        return

    #
    # Not sure what is is supposed to do yet
    #
    def callPerl(self, cmd):

        self.nopen.write("%s\n" % cmd)
        self.nopen.flush()

        return

    #
    # Return the current working directory.
    #
    def getcwd(self):

        return self.status['targetcwd']

    #
    # Parses the output of -status and sets the values dictionary.
    #
    def parsestatus(self):

        local = True
        values = { 'clientver': '', 
                   'histfile': '', 
                   'cmdoutfile': '', 
                   'localcwd': '', 
                   'nhome': '', 
                   'localpid': '', 
                   'serverver': '', 
                   'wdir': '', 
                   'targetos': '', 
                   'targetcwd': '', 
                   'targetpid': '', 
                   'targetppid': '', 
                   'targetport': '' }

        re_status = re.compile('(?P<name>.+[^\s]{1,})\s{2,}(?P<value>.+$)')

        output, nopenlines, lines = self.doit('-status')

        for line in lines:
            line = line.strip()

            if line == '[-status]' or not line: continue
            if line == 'Local' or line == 'Connection': continue
            if line == 'Remote':
                local = False
                continue

            match = re_status.search(line)
            if not match:
                continue

            name = match.group('name')
            value = match.group('value')

            if name == 'NOPEN client':
                values['clientver'] = value
            elif name == 'History':
                values['histfile'] = value
            elif name == 'Command Out':
                values['cmdoutfile'] = value
            elif name == 'CWD' and local is True:
                values['localcwd'] = value
            elif name == 'CWD' and local is False:
                values['targetcwd'] = value
            elif name == 'NHOME':
                values['nhome'] = value
            elif name == 'PID (PPID)' and local is True:
                values['localpid'] = value
            elif name.startswith('Remote'):
                port = value[value.rfind(':')+1:value.rfind('\)')]
                values['targetport'] = port
            elif name == 'PID (PPID)' and local is False:
                pid,ppid = value.split(' ')
                values['targetpid'] = pid[1:-1]
                values['targetppid'] = ppid[1:-2]
            elif name == 'OS':
                values['targetos'] = value
                if value.find('SunOS') != -1:
                    self.state['solaris'] = True
                elif value.find('Linux') != -1:
                    self.state['linux'] = True
                elif value.find('HP-UX') != -1:
                    self.state['hpux'] = True
                if value.find('ia64') != -1:
                    self.state['hpux_it'] = True
            elif name == 'NOPEN server':
                values['serverver'] = value
            elif name == 'WDIR':
                values['wdir'] = value

        self.status = values

        f = open(self.statusFile, 'wb')
        pickle.dump(self.status, f)
        f.close()

        return

    #
    # Prints output to the NOPEN window by writing to a local
    # file and "-lsh cat" that file.
    #
    def doprint(self, *msgs):

        whatout = os.path.join(self.optmp, '.whatout.%d' % self.pid)

        fd = open(whatout, 'w')
        for m in msgs:
            if m.__class__() == []:
                for m2 in m:
                    fd.write(m2)
            else:
                fd.write(m)

        fd.write('%s\n' % self.COLOR_NORMAL)
        fd.close()

        self.doit('-lsh cat %s' % whatout)

        return


    #
    # Runs "-lsh echo" with the string. Should probably use self.doprint()
    # instead to avoid dealing with escaping issues.
    #
    def dolocalecho(self, cmd):

        self.nopen.write('-lsh echo "%s"\n' % cmd)
        self.nopen.flush()

        return

    #
    # Runs a command through the NOPEN autoport.
    # Returns a 3-tuple of two strings and a list: (output, nopenoutput, outputlines)
    #   output - string of non-nopen lines
    #   nopenoutput - string of nopen lines
    #   outputlines - list of non-nopen lines
    #
    def doit(self, cmd):

        if not cmd.startswith('-put') and not cmd.startswith('mkdir'):
            cmd = '%s -nohist' % cmd

        first = True

        self.nopen.write('%s\n' % cmd)
        self.nopen.flush()

        nopenlines = []
        outputlines = []

        re_nopenline = re.compile('^\[.*\]$')

        while self.nopen:
            try:
                line = self.nopen.readline().strip('\n\r')
            except socket.error:
                continue

            if line.startswith('NO! '):
                nopenlines.append(line)
                break
            elif re_nopenline.match(line):
                nopenlines.append(line)
            else:
                outputlines.append(line)

        return ('\n'.join(outputlines), '\n'.join(nopenlines), outputlines)

    #
    # Runs the command and writes the output to a local file in opdown
    # (for builtins) or optargetcommands. Force to optargetcommands
    # with tgtcmd (execept builtins will ignore this).
    # Returns a 2-tuple of the output content and the output file name:
    #   (output, outfilename)
    #
    def doitwrite(self, cmd):

        (out, nout, outlines) = self.doit(cmd)

        # find the actual command in the nopen output and use that for 
        # creating a file name (unless it was redirected)

        realcmd = None
        noutlines = nout.split('\n')

        for line in noutlines:
            if re.search('Saving +output to', line) or \
                re.search('^\[.*\]\[.* -. .*\]$', line):
                continue
            else:
                r = re.search('\[(.*)\]', line)
                if r != None:
                    realcmd = r.group(1)
                    break

        if not realcmd:
            realcmd = cmd

        # cleanup the command string
        tmpcmd = realcmd.strip()
        tmpcmd = tmpcmd.replace('-nohist', '')

        r = re.search('^(.*)\s*[\.\>]+\s*(L:|T:).*', tmpcmd)
        if r != None:
            tmpcmd = r.group(1).strip()

        if tmpcmd[0] == '\\':
            tmpcmd = tmpcmd[1:]

        tmpcmd = re.sub('[\*\!\s/\\\$\&>\|]', '_', tmpcmd)
        tmpcmd = re.sub(';', '+', tmpcmd)

        if tmpcmd[0] in ['-', '=']:
            filename = os.path.join(
                self.opdown, '%s__%s' % (tmpcmd[1:], self.nopen_rhostname))
        elif realcmd.find('|') >= 0:
            filename = os.path.join(
                self.opdown, '%s__%s' % (tmpcmd, self.nopen_rhostname))
        else:
            filename = os.path.join(self.optargetcommands, tmpcmd)

        # truncate long files
        filename = filename[:2000]
        filename = '%s__%s' % (filename, timestamp())
        
        # just to be safe
        self.preserveFiles(filename)

        fd = open(filename, 'w')
        fd.write('# %s\n\n' % cmd)
        fd.write(out)
        fd.write('\n')
        fd.close()

        return (out, filename)


    #
    # Takes an existing file and renames it to "filename_###".
    # files can be a single filename or list of filenames.
    #
    def preserveFiles(self, files, loud=False):

        retarr = []

        if files.__class__() == '':
            files = [files]

        for f in files:
            if os.path.exists(f):
                ext_num = 0

                while os.path.exists('%s_%04d' % (f, ext_num)):
                    ext_num += 1

                newname = '%s_%04d' % (f, ext_num)

                if loud:
                    print '\n%s%s: File exists, renaming to %s%s\n' % \
                        (self.COLOR_WARNING, f, newname, self.COLOR_NORMAL)

                os.rename(f, newname)
                retarr.append(newname)

        return retarr

    #
    # Not sure if used yet...
    #
    def startTunnel(self, autoport=None):

        from control import control
        import random
    
        if not autoport:
            autoport = random.randint(20000,60000)


        self.callPerl("-tunnel %d tcp autoclose" % autoport)
    
        self.tunnel = control(int(autoport))
        self.tunnel.main()

    #
    # Not sure if used yet...
    #
    def stopTunnel(self):

        if self.tunnel:
            self.tunnel.s.send("c 1 2 3 4 5 6 7 8 9\n")
            time.sleep(1)
            self.tunnel.finish()

    #
    # Cleans up. Right now just closes the autoport socket.
    #
    def cleanup(self):

        self.nopen_socket.close()
        self.connected = False
        self.nopen = None

        return

    #
    # Returns 2-tuple (rx_MB, tx_MB), both floats.
    #
    def bwsofar(self):

        bwfile = os.path.join(self.opdown, 'bwmonitor.txt')

        if os.path.exists(bwfile):
            tx_re = None
            rx_re = None

            # try twice in case tail -2 fails for some reason
            for i in range(0, 2):
                tail = execute('tail -2 %s' % bwfile)
                lines = tail.strip().split('\n')

                if len(lines) != 2:
                    continue

                tx_re = re.search('^\s*TX\s+(\d+)', lines[0])
                rx_re = re.search('^\s*RX\s+(\d+)', lines[1])

                if tx_re != None and rx_re != None:
                    break

            if tx_re == None or rx_re == None:
                return (0, 0)

            return (int(rx_re.group(1)) / 1048576.0, int(tx_re.group(1)) / 1048576.0)
        else:
            # TODO: go through pcaps dir and calculate size?
            return (0, 0)

    #
    # Pops a window with custom text
    # - pillaged largely from doprint()
    #
    def textpopup(self, xargs, *msgs):

        whatout = os.path.join(self.optmp, '.whatout.%d.%d' % \
                                   (self.pid, random.randint(1,10000)))

        fd = open(whatout, 'w') 
        for m in msgs:
            if m.__class__() == []:
                for m2 in m:
                    fd.write(m2)
            else:
                fd.write(m)
        fd.close()

        if xargs == None:
            xargs = '-geometry 88x58 -bg white -fg blue'

        self.filepopup(whatout, xargs)

        return


    #
    # Pops an xterm with a provided file and geometry
    # - pillaged largely from execute()
    #
    def filepopup(self, file, xargs='-geometry 88x58 -bg white -fg blue'):

        if not os.path.exists(file):
            self.doprint(COLOR['fail'], 'Error: the file %s doesn\'t exist.' % file)
        else:
            pid = os.fork()

            if pid == 0:
                cmd = 'xterm %s -e view %s' % (xargs,file)
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, shell=True)
                os._exit(0)

        return

    #
    # Returns a name for a temporary file using the convention of
    # prefix and NOPEN pid, ensuring the file doesn't already exist.
    # Input is a directory and prefix concatenated, such as "/var/tmp/d"
    # or "/dev/shm/.tmp".
    #
    def tmpfilename(self, directoryprefix):
        number = int(self.nopen_mypid)
        output = "dummy"
        while output:
            output, nopenoutput, outputlines = self.doit("-lt %s.%d" % (directoryprefix, number))
            number += 1
        number -= 1
        return "%s.%d" % (directoryprefix, number)
        


###############################################################################

#
# Use this class when doing option parsing.
#
# By default, the epilog (to print additional help info) will strip off
# newlines, so this class overrides it and returns it as-is.
#
class OptParser(OptionParser):

    #
    # Don't do any formatting on the epilog.
    #
    def format_epilog(self, formatter):

        return self.epilog


###############################################################################
# Misc methods
###############################################################################

#
# Locally execute a command and return the stdout output,
# since os.system() does not return output.
#
def execute(cmd, indata=None):

    stdin = None

    if indata:
        stdin = subprocess.PIPE

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=stdin, 
                            stderr=subprocess.PIPE, shell=True)

    if indata:
        proc.stdin.write(indata)
        proc.stdin.close()

    output = proc.stdout.read()

    return output

#
# Split list l into n sized chunks.
#
def chunks(l, n):

    return list(chunks_h(l, n))

def chunks_h(l, n):

    for i in xrange(0, len(l), n):
        yield l[i:i+n]

#
# Returns readlines() output from a file
#
def file_readlines(filename):

    try:
        fd = open(filename, 'r')
        lines = fd.readlines()
        fd.close()
        return lines
    except:
        return []


#
# Returns timestamp in format of YYYYMMDD-HHMMSS
#
def timestamp():

    return time.strftime('%Y%m%d-%H%M%S', time.gmtime())


if __name__ == "__main__":

    print "Not to be called directly..."
    sys.exit(1)
