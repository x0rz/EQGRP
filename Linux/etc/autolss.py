#!/usr/bin/env python2.6
VERSION = '1.0.0.7'

import os
import re
import sys
import time
import fcntl
import shlex
import shutil
import socket
import hashlib
import os.path
import traceback
from optparse import OptionGroup

import autoutils
from autoutils import COLOR
from autoutils import OptParser

imported = True

class nopenlss:

    def __init__(self, nopen=None):

        if nopen == None:
            self.nopen = autoutils.autoutils()
        else:
            self.nopen = nopen

        self.stopfile = os.path.join(self.nopen.optmp, 'StopLSSnow')
        self.cksums_file = os.path.join(self.nopen.optmp, '%s.pylss.cksums' % self.nopen.nopen_rhostname)
        self.files_per_get = 25

        # create empty cksums file if not there
        if not os.path.exists(self.cksums_file):
            fd = open(self.cksums_file, 'w')
            fd.close()

        self.options = None
        self.version = VERSION
        self.parser = self.get_arg_parser()

        # for convenience
        self.doprint = self.nopen.doprint
        self.default_dl_dir = os.path.join(self.nopen.opdown, self.nopen.nopen_rhostname)
        self.default_ns_dir = os.path.join(self.nopen.opdown, 'NOSEND', self.nopen.nopen_rhostname)


    def get_arg_parser(self):

        epilog =  '\nNOTE: Use this local touch to stop all -lss -G sessions running\n'
        epilog += '      (after the current -get finishes, see -o above):\n\n'
        epilog += '  -lsh touch %s\n\n' % self.stopfile
        epilog += '-gs lss.py version %s\n' % VERSION

        parser = OptParser(usage='usage: -gs lss.py [options] REMOTEPATH [REMOTEPATH2 [MORE...]]', epilog=epilog)

        parser.add_option('-v', dest='v', action='store_true', help='Show version and exit.')

        group = OptionGroup(parser, '-ls OPTIONS')
        group.add_option('-c', dest='c', action='store_true', help='Show ctime (default is mtime).')
        group.add_option('-d', dest='d', action='store_true', help='Only show that inode, not its contents (even if it is a directory).')
        group.add_option('-R', dest='R', action='store_true', help='Recursive listing, showing all subdirectories.')
        group.add_option('-u', dest='u', action='store_true', help='Show atime (default is mtime).')
        group.add_option('--xm', dest='xm', metavar='MM-DD-YYYY', help='Show only files dated on/after this mtime date.')
        group.add_option('--xa', dest='xa', metavar='MM-DD-YYYY', help='Show only files dated on/after this atime date.')
        group.add_option('--xc', dest='xc', metavar='MM-DD-YYYY', help='Show only files dated on/after this ctime date.')
        parser.add_option_group(group)

        group = OptionGroup(parser, 'LSS OPTIONS')
        group.add_option('-f', dest='f', metavar='file', help='Save output to local file (still shown on stdout).')
        group.add_option('-F', dest='F', action='store_true', help='Show files only (no dirs or specials).')
        group.add_option('-g', dest='g', metavar='[I:]exps', help='ONLY show/download files whose -ls listing (to include permissions, ownership, datestamp) matches any of the ",," delimited perl regular expressions provided (unless -V excludes them). "I:" makes the match case insensitive. If "exps" is a local file, its content will be used as the list of regular expressions, one per line.')
        group.add_option('-m', dest='m', metavar='mix', help='Only show/download files of at least min bytes (implies -F).')
        group.add_option('-M', dest='M', metavar='max', help='Only show/download files of at most max bytes (implies -F).')
        group.add_option('-O', dest='O', metavar='file', help='Save -ls output using -cmdout (preserves all three timestamps).')
        group.add_option('-P', dest='P', action='store_true', help='Look in PATH directories for the target files, like "which" (implies -U).')
        group.add_option('-Q', dest='Q', action='store_true', help='Quiet mode, when nopenlss() is called from another function, this returns but does not show the final result.')
        group.add_option('-S', dest='S', metavar='MM-DD-YYYY', help='Only show/download files at most this old. Think of this as the STOP date (--xm date for -ls is the START date).')
        group.add_option('-U', dest='U', action='store_true', help='Do NOT re-use the target -ls of this/these PATHs if done before (otherwise, if the same PATHs are given later in the same order, the old -ls output will be re-used by default).')
        group.add_option('-V', dest='V', metavar='[I:]exps', help='DO NOT show/download files whose -ls listing (to include permissions, ownership, datestamp) matches any of the ",," delimited perl regular expressions provided. "I:" makes the match case insensitive. If "exps" is a local file, its content will be used as the list of regular expressions, one per line.')
        group.add_option('-w', dest='w', action='store_true', help='Looks for files beginning with the target strings (implies -P).')
        group.add_option('-W', dest='W', action='store_true', help='Looks for files containing the target strings (implies -P).')
        group.add_option('-z', dest='z', action='store_true', help='Provide sum of all file sizes.')
        group.add_option('-Z', dest='Z', action='store_true', help='Do not show/download empty files (implies -F).')
        parser.add_option_group(group)

        group = OptionGroup(parser, 'LSS GET OPTIONS (ignored without -G)')
        group.add_option('-0', dest='zero', action='store_true', help='(Zero) When using -K, skip making the local duplicate file (implies -K).')
        group.add_option('-8', dest='eight', action='store_true', help='In -G/get mode, we use -ls -n before and then -touch -t after files are pulled to preserve the original mtime and atime (implies -o).')
        group.add_option('-b', dest='b', metavar='head|tail', help='Get the "head" or "tail" -M max bytes of each file (implies -o).')
        group.add_option('-D', dest='D', action='store_true', help='After -ls is complete (even if you choose to -get nothing), offer to REMOVE THE REMOTE FILES just listed (and possibly retrieved). If target files are not in a hidden directory, you will have several layers of confirmation to get through.')
        group.add_option('-G', dest='G', action='store_true', help='After sorted -ls is shown, option to download (implies -F).')
        group.add_option('-k', dest='k', action='store_true', help='Keep original order (don\'t sort), useful to preserve priority with -l file.')
        group.add_option('-K', dest='K', action='store_true', help='Skip any file download where some previously -lss.py downloaded file is identical (uses target "cksum" binary once PER FILE) and instead make a local copy by that name (implies -o).')
        group.add_option('-l', dest='l', metavar='file', help='Use the local file--the files/paths in there become your PATH arguments. Each line can be output from a -ls or a find or a -get command--the path, starting with /, will be used, but IT MUST be the only or final field on the line. Further, if there is a -x[mac] MM-DD-YYYY or -[mac] MM-DD-YYYY timestamp prior to the path on the line, that timestamp is used as an -ls option with that path, (always with mtime by default). The earliest timestamp will be used if different times are found. Specifying --x[mac] in the -lss.py line will override any time given in the file.')
        group.add_option('-L', dest='L', metavar='DIR', help='Use -get -l to put the files into local DIR (with -lcd DIR). Either DIR must exist, or it can be "NOSEND" to indicate that behavior (making /current/down/NOSEND/$nopen_rhostname if needed). Appending a path to "NOSEND" (without spaces) will create and download to that relative path, for example "-L NOSEND/path/to /path/to/file" will download /path/to/file to /current/down/NOSEND/$nopen_rhostname/path/to/.')
        group.add_option('-N', dest='N', action='store_true', help='Skip prompts for deleting, but only if in hidden directory.')
        group.add_option('-o', dest='o', action='store_true', help='If getting files, get exactly one at a time. Otherwise, -gs lss.py will put several files on each command line. Using -o is a good idea if most the files are large and you are using -T.')
        group.add_option('-r', dest='r', action='store_true', help='Force duplicate -gets from previous target downloads or rsyncs (default will not pull file a second time).')
        group.add_option('-s', dest='s', metavar='N,M', help='Split the pull multiple ways, letting simultaneous and identical -lss.py commands share the load. M is ignored as any number of instances can jump in on the gets. N=1 implies the "master" instance that runs first and generates the list.')
        group.add_option('-T', dest='T', metavar='max', help='Stop pulling files when the bwmonitor reaches max Megabytes.')
        group.add_option('-Y', dest='Y', action='store_true', help='Eliminate prompt about download and just do it.')
        parser.add_option_group(group)

        return parser


    #
    # This does the filtering of the list (lines) returned from -ls based
    # on the arguments given. This uses yield() to be passed to list().
    # It yields a tuple of (perms, linkcnt, uid, gid, size, date, file, date_secs, islocal, localsize)
    #
    def filter_file_list(self, lines, filesonly, nonzero, minbytes, maxbytes, headtail,
                         greps, vgreps, stopdate, download_dir):

        for line in lines:
            line = line.strip()

            if len(line) == 0:
                continue

            parts = line.split(None, 5)
            datestr = parts[5][:17]
            filename = parts[5][18:]

            size = int(parts[4])

            if filesonly and parts[0][0] != '-':
                continue

            if nonzero and size == 0:
                continue

            if minbytes and size < minbytes:
                continue

            if not headtail:
                if maxbytes and size > maxbytes:
                    continue

            if len(greps) > 0:
                passgrep = False

                for r in greps:
                    if r[0].search(line):
                        passgrep = True
                        r[3] += 1
                        break

                if not passgrep:
                    continue

            if len(vgreps) > 0:
                passgrep = False

                for r in vgreps:
                    if r[0].search(line):
                        passgrep = True
                        r[3] += 1
                        break

                if passgrep:
                    continue

            secs = time.mktime(time.strptime(datestr, '%b %d %H:%M %Y'))

            if stopdate and secs > stopdate:
                continue

            ret = parts[:4]
            ret.append(int(parts[4]))
            ret.append(datestr)
            ret.append(filename)
            ret.append(secs)

            have_local = False
            filename = filename.strip('/')

            if download_dir:
                local_file = os.path.join(download_dir, os.path.basename(filename))
                have_local = self.have_local_file(local_file, size)

            if not have_local:
                local_file = os.path.join(self.default_dl_dir, filename)
                have_local = self.have_local_file(local_file, size)

            if not have_local:
                local_file = os.path.join(self.default_ns_dir, os.path.basename(filename))
                have_local = self.have_local_file(local_file, size)

            ret.append(have_local[0])
            ret.append(have_local[1])

            yield(tuple(ret))


    # Helper function to determine if a file exists locally and if
    # the size is the same.
    def have_local_file(self, path, size):

        if os.path.isfile(path):
            sz = os.stat(path).st_size
            if sz == size:
                return (True, sz)
            else:
                return (False, sz)

        return (False, 0)


    # Gets a list of n files from the list, getting the current index from
    # the file opened with idx_fd, and writing back the new index.
    def get_next_files(self, filelist, idx_fd, n):

        files = []

        fcntl.flock(idx_fd, fcntl.LOCK_EX)

        os.lseek(idx_fd, 0, os.SEEK_SET)

        data = os.read(idx_fd, 100)
        idx = int(data.strip())

        if idx < len(filelist):
            files = filelist[idx:idx+n]

        os.ftruncate(idx_fd, 0)
        os.lseek(idx_fd, 0, os.SEEK_SET)
        os.write(idx_fd, '%s\n' % (idx + n))
        os.fsync(idx_fd)

        fcntl.flock(idx_fd, fcntl.LOCK_UN)

        return files


    #
    # -get the files
    # returns a list of files collected
    #
    def get_files(self, filelist, idx_file, singlegets, local_dir, headtail, maxbytes, maxbw, cksums, nodups, preserve, loud=False):

        stopped_str1 = 'Force stop file (%s) now exists.\n' % self.stopfile
        stopped_str2 = 'Download aborted. Remove this file to allow future -lss.py ' + \
            '-G\'s this op:\n\n  -lsh  rm -f %s\n\n' % self.stopfile
        cksum_re = re.compile('^(\d+ \d+) (.+)$')
        got_files = []

        try:
            idx_fd = os.open(idx_file, os.O_RDWR | os.O_APPEND)
        except:
            self.doprint('could\'t open index file: %s' % idx_file)
            return []

        # make sure only getting files
        filelist = [x for x in filelist if x[0][0] == '-']

        quiet = ' -q'
        local = ''

        if loud:
            quiet = ''

        oldcwd = self.nopen.status['localcwd']
        if local_dir:
            self.nopen.doit('-lcd %s' % local_dir)
            local = ' -l'

        if singlegets:

            while True:
                # check current bw before each get
                if maxbw != None and maxbw > 0:
                    curr_rx = self.nopen.bwsofar()[0]
                    if curr_rx > maxbw:
                        self.doprint(COLOR['fail'], '\nMax download %dM has been exceeded (%.2fM).\n' % (maxbw, curr_rx))
                        break

                # check if need to stop
                if os.path.exists(self.stopfile):
                    self.doprint(COLOR['fail'], stopped_str1,
                                 COLOR['normal'], stopped_str2)
                    break

                files = self.get_next_files(filelist, idx_fd, 1)

                if len(files) == 0:
                    break

                cksum_match = False
                cksumsize = ''
                get = 'get'
                offset_args = ''
                if headtail:
                    get = 'oget'

                    if files[0][4] > maxbytes:
                        if headtail == 'head':
                            offset_args = ' -b 0 -e %d' % maxbytes
                        elif headtail == 'tail':
                            offset_args = ' -b %d' % (files[0][4] - maxbytes)

                filename =  re.sub(r'(\s)', r'\\\1', files[0][6]) # have to escape again

                # if checking cksums, check if have a local copy first
                # and don't do the get
                if cksums:
                    output, nout, outlines = self.nopen.doit('cksum %s' % filename)

                    r = cksum_re.search(output)
                    if r != None:
                        cksumsize = r.group(1)
                        res = autoutils.execute('egrep "%s" %s' % (cksumsize, self.cksums_file))
                        res = res.split('\n')

                        # get a version of the local matching file, which will
                        # be on the first line
                        r = cksum_re.search(res[0])
                        if r != None:
                            lfile = r.group(2)
                            cksum_match = True
                                
                # if have a local match, just do the copy and don't get, 
                # and continue with next file
                if cksum_match:
                    got_files.append(filename)

                    if not nodups and not files[0][8]:
                        # figure out local dest file
                        if local_dir:
                            destfile = os.path.join(local_dir, os.path.basename(filename))
                        else:
                            filename = filename.strip('/')
                            destfile = os.path.join(self.default_dl_dir, filename)

                        if os.path.exists(destfile):
                            self.nopen.preserveFiles(destfile, True)
                        else:
                            try:
                                os.makedirs(os.path.dirname(destfile))
                            except:
                                pass

                        self.doprint(COLOR['fail'], 'Duplicate target file already retrieved, making local copy:\n',
                                     '"%s" -- "%s"\n' % (lfile, destfile))
                        shutil.copyfile(lfile, destfile)
                    else:
                        # don't make a copy if the local file is the one we got or nodups was set
                        self.doprint(COLOR['fail'], 'Duplicate target file already retrieved, NOT making local copy.\n',
                                     '%s\n' % lfile)

                    continue

                # get timestamp if preversing times
                if preserve:
                    output, nout, outlines = self.nopen.doit('-ls -n %s' % filename)

                    if re.search('^-touch', output):
                        touch_cmd = output
                    else:
                        touch_cmd = ''

                # do the get
                output, nout, outlines = self.nopen.doit('-%s%s%s%s %s' % \
                    (get, offset_args, quiet, local, filename))

                if preserve and touch_cmd != '':
                    self.nopen.doit(touch_cmd)

                # this list will have the "file -- /current/down/<..>/file" line, and possibly 
                # a "file exists, renaming" line before it.
                output = [x for x in output.split('\n') if x != '']

                if len(output) == 0:
                    continue # -get didn't get the file

                got_files.append(filename)

                # get locally named file
                # TODO: maybe check number of " -- " in the string in case a file
                # contains those characters.
                lfile = output[-1].split(' -- ')[-1]

                # same cksum if needed
                if cksums:
                    with open(self.cksums_file, 'a') as fd:
                        fd.write('%s %s\n' % (cksumsize, lfile))
                        fd.write('%s %s\n' % (cksumsize, filename))

                # rename file if got partial
                if offset_args != '':
                    newfile = '%s.%s' % (lfile, headtail)

                    if os.path.exists(lfile):
                        self.nopen.preserveFiles(newfile, True)
                        os.rename(lfile, newfile)
                        self.doprint(COLOR['warn'], 'Partial file renamed to: %s' % newfile)

        else:
            while True:

                # check current bw before each get
                if maxbw != None and maxbw > 0:
                    curr_rx = self.nopen.bwsofar()[0]
                    if curr_rx > maxbw:
                        self.doprint(COLOR['fail'], '\nMax download %dM has been exceeded (%.2fM).\n' % (maxbw, curr_rx))
                        break

                # check if need to stop
                if os.path.exists(self.stopfile):
                    self.doprint(COLOR['fail'], stopped_str1,
                                 COLOR['normal'], stopped_str2)
                    break;

                files = self.get_next_files(filelist, idx_fd, self.files_per_get)
                if len(files) == 0:
                    break

                # get just filenames and escape each white space
                files = [re.sub(r'(\s)', r'\\\1', x[6]) for x in files]

                self.nopen.doit('-get%s%s %s' % (quiet, local, ' '.join(files)))

                got_files += files

        if local_dir:
            self.nopen.doit('-lcd %s' % oldcwd)

        os.close(idx_fd)

        return got_files


    #
    # Deletes the list of files from target
    #
    def delete_files(self, filelist):

        curdirs = [x for x in self.nopen.getcwd().split('/') if x]
        numup = len(curdirs)
        dirups = '/'.join(['..'] * numup)

        for i in xrange(0, len(filelist)):
            if filelist[i][0] == '/':
                filelist[i] = '%s%s' % (dirups, filelist[i])

        for chnks in autoutils.chunks(filelist, 25):
            self.nopen.doit('-rm %s' % ' '.join(chnks))

        return


    #
    # Returns the sum of all the file sizes.
    #
    def get_size_sum(self, lslist, headtail, htmax):

        tot = 0

        for x in lslist:
            if x[0][0] == '-':
                size = x[4]

                if headtail == None:
                    tot += size
                else:
                    if htmax > 0 and size > htmax:
                        tot += htmax
                    else:
                        tot += size

        return tot


    #
    # Returns a tuple, with list of paths from the given file,
    # the time to use, and the mac letter.
    #
    def get_list_from_file(self, filename):

        filelist = []
        mintime = 0
        mac = 'm'

        lines = autoutils.file_readlines(filename)

        file_re = re.compile('^[^/]*(/.*)$')
        time_re = re.compile('^[^/]*-x?([mac]?) (\d\d-\d\d-\d\d\d\d) .*$')

        for line in lines:
            r = file_re.search(line)
            if r != None:
                filename = r.group(1).strip('\n\r')

                if len(filename) > 0:
                    filelist.append(filename)

            r = time_re.search(line)
            if r != None:
                t = time.mktime(time.strptime(r.group(2), '%m-%d-%Y'))

                if mintime == 0 or t < mintime:
                    mintime = t

                    if r.group(1) != None:
                        mac = r.group(1)
                    

        if mintime != 0:
            mintime = time.strftime('%m-%d-%Y', time.localtime(mintime))

        return (filelist, mintime, mac)


    #
    # just show the version
    #
    def print_version(self, prog):

        script_name = os.path.basename(prog)

        if script_name.startswith('auto'):
            script_name = script_name.split('auto', 1)[1]

        self.doprint('-gs %s version %s' % (script_name, self.version))


    #
    # main routine
    #
    def main(self, argv):

        if imported:
            prog = sys.argv[0]
            
            if argv.__class__() == '':
                argv = shlex.split(argv)
        else:
            prog = argv[0]
            argv = argv[1:]

        opts, args = self.nopen.parseArgs(self.parser, argv)

        if not self.nopen.connected:
            self.nopen.connect()

        window_num = 1

        if opts.v:
            self.print_version(prog)
            return

        if opts.Z or opts.m or opts.M or opts.G:
            opts.F = True

        if opts.zero:
            opts.K = True

        if opts.eight:
            opts.o = True

        if opts.K:
            opts.o = True

        try:
            if opts.m: opts.m = int(opts.m)
            if opts.M: opts.M = int(opts.M)
        except ValueError:
            self.doprint(COLOR['fail'], '\n-m/-M options must be integers\n')
            return

        try:
            if opts.T: opts.T = int(opts.T)
        except ValueError:
            self.doprint(COLOR['fail'], '\n-T option must be an integer\n')
            return

        if opts.O:
            if os.path.exists(opts.O):
                if not os.path.isfile(opts.O) or opts.O[-1] == '/':
                    self.doprint(COLOR['fail'], '\n-O %s : must be a full path to a file\n' % opts.O)
                    return

                self.nopen.preserveFiles(opts.O, True)
                
            if not os.path.exists(os.path.dirname(opts.O)) or opts.O[-1] == '/':
                self.doprint(COLOR['fail'], '\n-O %s : must be a full path that already exists\n' % opts.O)
                return

        if opts.w or opts.W:
            opts.P = True

            if opts.w and opts.W:
                self.doprint(COLOR['fail'], 'only one of -w or -W can be specified')
                return

        # each element will be a list containing:
        #  [ re_object, re_string, is_case_insens, match_count ]
        greps = []
        vgreps = []

        # get the expressions to grep on
        if opts.g:
            flags = 0
            grep_arg = opts.g

            if grep_arg.startswith('I:'):
                flags = re.I
                grep_arg = grep_arg[2:]

            if os.path.exists(grep_arg):
                lines = autoutils.file_readlines(grep_arg)
                greps = [ [re.compile(x.strip('\n\r'), flags), x.strip('\n\r'), flags == re.I, 0] for x in lines ]
            else:
                greps = [ [re.compile(x, flags), x, flags == re.I, 0] for x in grep_arg.split(',,') ]

        # get the expressions to grepout on
        if opts.V:
            flags = 0
            vgrep_arg = opts.V

            if vgrep_arg.startswith('I:'):
                flags = re.I
                vgrep_arg = vgrep_arg[2:]

            if os.path.exists(vgrep_arg):
                lines = autoutils.file_readlines(vgrep_arg)
                vgreps = [ [re.compile(x.strip('\n\r'), flags), x.strip('\n\r'), flags == re.I, 0] for x in lines ]
            else:
                vgreps = [ [re.compile(x, flags), x, flags == re.I, 0] for x in vgrep_arg.split(',,') ]

        # parses the PATH and sets the dir list as the intersection of the
        # paths and given path arguments
        if opts.P:
            opts.U = True
            paths = []

            output, nopenlines, outputlines = self.nopen.doit('-getenv')

            for line in outputlines:
                rm = re.match('^PATH=(.*)$', line)
                if rm != None:
                    paths = rm.group(1).split(':')
                    break

            tmpargs = []

            if opts.w:
                for p in paths:
                    for a in args:
                        tmpargs.append('%s/%s*' % (p, a))
            elif opts.W:
                for p in paths:
                    for a in args:
                        tmpargs.append('%s/*%s*' % (p, a))
            else:
                for p in paths:
                    for a in args:
                        tmpargs.append('%s/%s' % (p, a))

            args = tmpargs

        # create the list of dirs
        dir_list_line = args
        dir_list_file = []

        # getting implies files only and getting the sums
        if opts.G:
            opts.F = True
            opts.z = True

        if opts.b:
            opts.o = True

            if not opts.M:
                self.doprint(COLOR['fail'], '-M must be specified with -b')
                return

            opts.b = opts.b.lower()

            if not opts.b in ['tail', 'head']:
                self.doprint(COLOR['fail'], '-b must be "head" or "tail"')
                return

        if opts.s:
            # allowing -s to be: "N" or "N,x", where x is ignored
            nm = opts.s.split(',')
            if len(nm) > 2:
                self.doprint(COLOR['fail'], 'invalid -s format')
                return

            try:
                window_num = int(nm[0])
            except ValueError:
                self.doprint(COLOR['fail'], 'invalid -s format: N must be an integer')
                return

        # determine the local dir for gets
        if opts.L:
            r = re.match('NOSEND(.*)', opts.L)

            if r != None:
                if r.group(1) != '':
                    download_dir = os.path.join(self.default_ns_dir, r.group(1).strip('/'))
                else:
                    download_dir = self.default_ns_dir

                if not os.path.exists(download_dir):
                    os.makedirs(download_dir)
            else:
                download_dir = opts.L

            if not os.path.isdir(download_dir):
                self.doprint(COLOR['fail'], '-L option must be a directory (%s)' % download_dir)
                return
        else:
            download_dir = None

        if opts.l:
            (tmplist, lstime, mac) = self.get_list_from_file(opts.l)
            dir_list_file = tmplist

            if lstime != 0:
                if mac == 'a':
                    opts.xa = lstime
                elif mac == 'c':
                    opts.xc = lstime
                else:
                    opts.xm = lstime

        # check the date format
        for d in [opts.xm, opts.xa, opts.xc, opts.S]:
            if d != None and not re.match('^((1[0-2])|(0[1-9]))-((0[1-9])|([12][0-9])|(3[01]))-\d\d\d\d$', d):
                self.doprint(COLOR['fail'], 'Invalid date (%s).' % d)
                return

        if opts.D:
            hidden_dirs = self.nopen.getHidden()

        # set the -ls options
        lsopts = ''
        if opts.c: lsopts += 'c'
        if opts.d: lsopts += 'd'
        if opts.R: lsopts += 'R'
        if opts.u: lsopts += 'u'
        if len(lsopts) > 0:
            lsopts = '-%s ' % lsopts
        if opts.xm: lsopts += '-xm %s' % opts.xm
        if opts.xa: lsopts += '-xa %s' % opts.xa
        if opts.xc: lsopts += '-xc %s' % opts.xc

        # get the lss options in a string for prettiness
        # also used for generating split-window pastables (-s)
        lssopts = ''
        if opts.D: lssopts += 'D'
        if opts.F: lssopts += 'F'
        if opts.G: lssopts += 'G'
        if opts.k: lssopts += 'k'
        if opts.K: lssopts += 'K'
        if opts.N: lssopts += 'N'
        if opts.o: lssopts += 'o'
        if opts.P: lssopts += 'P'
        if opts.Q: lssopts += 'Q'
        if opts.r: lssopts += 'r'
        if opts.U: lssopts += 'U'
        if opts.w: lssopts += 'w'
        if opts.W: lssopts += 'W'
        if opts.Y: lssopts += 'Y'
        if opts.z: lssopts += 'z'
        if opts.Z: lssopts += 'Z'
        if opts.eight: lssopts += '8'
        if opts.zero: lssopts += '0'
        if len(lssopts) > 0:
            lssopts = '-%s' % lssopts
        if opts.f: lssopts += ' -f %s' % opts.f
        if opts.m: lssopts += ' -m %d' % opts.m
        if opts.M: lssopts += ' -M %d' % opts.M
        if opts.O: lssopts += ' -O %s' % opts.O
        if opts.S: lssopts += ' -S %s' % opts.S
        if opts.g: lssopts += ' -g %s' % opts.g
        if opts.V: lssopts += ' -V %s' % opts.V
        if opts.b: lssopts += ' -b %s' % opts.b
        if opts.l: lssopts += ' -l %s' % opts.l
        if opts.L: lssopts += ' -L %s' % opts.L
        if opts.T: lssopts += ' -T %d' % opts.T

        dir_list = dir_list_line + dir_list_file
        dir_list = [re.sub(r'(\s)', r'\\\1', x) for x in dir_list] # escape spaces
        dir_list_str = ' '.join(dir_list)

        # specify the unique temporary file for -ls output
        cmdhash = hashlib.md5('%s %s' % (lsopts, dir_list_str)).hexdigest()
        master_ls_file = '%s.pylss.%s' % (self.nopen.nopen_rhostname, cmdhash)
        master_ls_file = re.sub(r'[ /\\]', '_', master_ls_file)
        master_ls_file = os.path.join(self.nopen.optmp, master_ls_file)
        master_get_file = master_ls_file + '.get'
        master_idx_file = master_ls_file + '.index'

        # if this is an additional window, the ls file will be the previously 
        # written master file
        if window_num > 1:
            master_ls_file = master_get_file
            opts.k = True # want to keep the order
            opts.Q = True # might want this
            #opts.Y = True # probably don't want this yet

        dols = False
        time_diff_mins = 0

        # determine if going to do a new -ls or reuse a previous one
        if os.path.exists(master_ls_file):
            if opts.U and window_num == 1:
                # don't care about what's there if updating
                os.unlink(master_ls_file)
                dols = True
            else:
                st = os.stat(master_ls_file)
                time_diff_mins = (time.time() - st.st_mtime) / 60
        elif window_num == 1:
            dols = True
        else:
            self.doprint(COLOR['fail'],
                'ERROR: can\'t find master file %s\n' % master_get_file,
                'Make sure to run the -lss.py with "-s 1,n" first')
            return

        # do the -ls or read from the previous master_ls_file
        if dols:
            if opts.O:
                self.nopen.doit('-cmdout %s' % opts.O)

            # split up files into groups so each listing is around 2k bytes long
            file_groups = []
            files_str = ''

            for f in dir_list:
                files_str = '%s %s' % (files_str, f)

                if len(files_str) > 2000:
                    file_groups.append(files_str)
                    files_str = ''

            if len(files_str) > 0:
                file_groups.append(files_str) # get the straglers

            outputlines = []

            # run the -ls on each group of files
            for fg in file_groups:
                output, nopenlines, tmpoutlines = self.nopen.doit('-ls %s %s >> T:%s' % \
                                                                      (lsopts, fg, master_ls_file))
                outputlines += tmpoutlines

            if opts.O:
                self.nopen.doit('-cmdout')
        else:
            if not opts.Q:
                if len(dir_list_str) > 100:
                    tmpstr = 'MULTIPLE_PATHS'
                else:
                    tmpstr = dir_list_str

                self.doprint(COLOR['fail'],
                             '\nReusing previous -ls of (%s) from %.2f minutes ago.\n' % (tmpstr, time_diff_mins),
                             'Use -U to disable this feature.\n')

            outputlines = autoutils.file_readlines(master_ls_file)

        orig_count = len(outputlines)

        if opts.S:
            stopdate = time.mktime(time.strptime(opts.S, '%m-%d-%Y')) + 86400
        else:
            stopdate = None

        # split the lines and convert to a tuple, removing newlines and empty strings
        filelist = list(self.filter_file_list(outputlines, opts.F, opts.Z, opts.m, opts.M, opts.b,
                                              greps, vgreps, stopdate, download_dir))

        # get a unique set of files 
        if not opts.k:
            # sort by time and filename
            filelist = sorted(set(filelist), key=lambda x: (x[7], x[6]))
        else:
            seen = set()
            filelist = [x for x in filelist if x[6] not in seen and not seen.add(x[6])]

        # create list of strings, one file per entry, to return
        finaloutput_list = ['%s %4s %-8s %-8s %10s %s %s' % \
                                (x[0], x[1], x[2], x[3], x[4], x[5], x[6]) for x in filelist]

        # write to additional file if -f was specified
        if opts.f:
            self.nopen.preserveFiles([opts.f], True)

            if not opts.Q:
                self.doprint(COLOR['note'], '\nWriting output to %s\n' % opts.f)

            outstr = '\n'.join(finaloutput_list)

            with open(opts.f, 'w') as fd:
                fd.write(outstr)
                fd.write('\n')

        # if doing gets, show previously pulled files and update list
        # to remove them if not doing regets.
        if opts.G:
            if not opts.Q:
                prev_files = [x for x in filelist if x[8] == True]
                outstrs = [ COLOR['fail'] ]

                if len(prev_files) > 0:
                    outstrs.append('Files pulled previously, ')

                    if opts.r:
                        outstrs.append('RE-PULLING them again:\n')
                    else:
                        outstrs.append('use -r to re-get them:\n\n')

                    outstrs += [ '%s %4s %-8s %-8s %10s %s %s\n' % \
                                     (x[0], x[1], x[2], x[3], x[4], x[5], x[6]) for x in prev_files ]

                    self.doprint(outstrs)

            # update list (only if this is the master get)
            if not opts.r and window_num == 1:
                filelist = [x for x in filelist if x[8] != True]

        # write the file list to a master list on disk
        # no more filtering should be done after this
        if opts.G and window_num == 1:
            with open(master_get_file, 'w') as fd:
                for f in filelist:
                    fd.write('%s %4s %-8s %-8s %10s %s %s\n' % (f[0], f[1], f[2], f[3], f[4], f[5], f[6]))

            with open(master_idx_file, 'w') as fd:
                fd.write('0\n')

        # get the total sum of the files
        if opts.G or opts.z:
            total_sum = self.get_size_sum(filelist, opts.b, opts.M)
            mword = ''

            if opts.b:
                mword = ', at most %d bytes per file' % opts.M

            total_sum_str = 'Cumulative total size (files only%s): %d bytes (%.2fM or %.2fG)\n' % \
                (mword, total_sum, total_sum / 1048576.0, total_sum / 1073741824.0)
            total_sum_str_G = 'Cumulative total size remaining (files only%s): %d bytes (%.2fM or %.2fG)\n' % \
                (mword, total_sum, total_sum / 1048576.0, total_sum / 1073741824.0)

        # show reformatted lines
        if not opts.Q:
            outstrs = [COLOR['note']]

            if len(dir_list_str) > 100:
                dir_list_str = 'MULTIPLE_PATHS'

            outstrs.append('\nAbove output reformatted by lss.py(%s %s %s):\n' % (lssopts, lsopts, dir_list_str))

            # rebuild listing with colors
            tmp_list = ['%s%s %4s %-8s %-8s %10s %s %s%s\n' % \
                            ((x[8] and COLOR['fail'] or ''), 
                             x[0], x[1], x[2], x[3], x[4], x[5], x[6], 
                             (x[8] and COLOR['normal'] or '')) for x in filelist]

            if len(tmp_list) > 0:
                outstrs.append(COLOR['normal'])
                outstrs += tmp_list
                outstrs.append(COLOR['note'])
            else:
                outstrs.append('\n# NO MATCHING FILES\n')

            if opts.g or opts.V:
                grep_note = ' (after filtering from %d)' % orig_count
            else:
                grep_note = ''

            if len(filelist) == 1:
                entry_word = 'entry'
            else:
                entry_word = 'entries'

            outstrs.append('\n# Above output, %d %s%s,\n' % (len(filelist), entry_word, grep_note))
            if opts.F:
                outstrs.append('#         files only,\n')
            if not opts.k:
                outstrs.append('#         was sorted from:\n')
            outstrs.append('#     -ls %s %s\n' % (lsopts, dir_list_str))

            have_locals = [x[8] for x in filelist]
            if True in have_locals:
                outstrs.append(COLOR['fail'])
                outstrs.append('# (files shown in red were pulled earlier)\n')
                outstrs.append(COLOR['note'])

            # show total bytes
            if opts.z:
                outstrs.append(total_sum_str)

            # show number of grep matches
            if len(greps) > 0:

                case_word = ''
                if greps[0][2] == True:
                    case_word = '(case insensitive) '

                outstrs.append('\nOutput also filtered to ONLY show those MATCHING %sany of:\n' % case_word)

                for r in greps:
                    outstrs.append('   r\'%-35s  %d hits\n' % (r[1] + '\'', r[3]))

                outstrs.append('\n')

            # show number of greoput matches
            if len(vgreps) > 0:
                if vgreps[0][2] == True:
                    case_word = '(case insensitive) '
                else:
                    case_word = ''

                outstrs.append('Output then filtered to NOT show those MATCHING %sany of:\n' % case_word)

                for r in vgreps:
                    outstrs.append('   r\'%-35s  %d hits\n' % (r[1] + '\'', r[3]))

                outstrs.append('\n')

            self.doprint(outstrs)

        got_files = []

        # show window pastables and prompt to continue with gets
        if opts.G:

            if len(filelist) > 0:
                outstrs = []

                # print out pastables for additional windows
                if opts.s and window_num == 1:
                    lsopts = re.sub(r'-x([mac])', r'--x\1', lsopts)

                    outstrs.append('OPTIONAL PASTABLE for other windows:\n\n')
                    outstrs.append('   -gs lss.py -s 2,n %s %s %s\n\n' % \
                        (lsopts, lssopts, ' '.join(dir_list_line)))

                # show bandwidth warning
                if opts.T and not opts.Q:
                    curr_rx = self.nopen.bwsofar()[0]

                    if (curr_rx + (total_sum / 1048576.0)) > opts.T:
                        outstrs += [ COLOR['fail'], 
                                     'NOTE: This amount plus your download so far (%.2fM) is more than your\n' % curr_rx,
                                     '      max download setting of %dM. Keep in mind that the size numbers\n' % opts.T,
                                     '      on target above are not compressed, but your download so far and max\n',
                                     '      download are.\n\n',
                                     COLOR['normal'] ]

                outstrs.append(total_sum_str_G)

                file_word = 'file'
                if len(filelist) > 1:
                    file_word += 's'

                ht_word = ''
                if opts.b:
                    ht_word = ' (only %s %d bytes)' % ((opts.b == 'tail') and 'last' or 'first', opts.M)

                if not opts.Y:
                    if window_num == 1:
                        prompt = '\nDo you want to get the %d %s shown above%s?' % \
                            (len(filelist), file_word, ht_word)
                    else:
                        prompt = '\nAdditional Get: Do you want to continue (%d %s)?' % \
                            (len(filelist), file_word)

                    outstrs.append(prompt)
                    ans = self.nopen.getInput(''.join(outstrs), 'N', COLOR['normal'])
                else:
                    ans = 'y'

                # do the get
                if ans.lower() in ['y', 'yes']:
                    got_files = self.get_files(filelist, master_idx_file, opts.o, download_dir,
                                               opts.b, opts.M, opts.T, opts.K, opts.zero, opts.eight)
            else:
                self.doprint(COLOR['fail'], 'There were no matching files not already pulled.\n')

        # Prompt for and do the deletions if requested
        if opts.D and len(got_files) > 0:

            skipprompt = opts.N
            showwarn = False
            dodelete = skipprompt

            # still prompt if any of the files are not in the hidden directory
            for f in got_files:
                matches = [f.startswith(x) for x in hidden_dirs]

                if not True in matches:
                    skipprompt = False
                    showwarn = True
                    dodelete = False

            # TODO: want to check if CWD is hidden dir so don't show warning
            #       for relative paths? (since this script doesn't prepend
            #       CWD paths to relative files)

            # create annoying prompts
            outstrs = [ '\n', COLOR['fail'] ]

            if showwarn:
                outstrs += [ 'WARNING!! ', COLOR['warn'],
                             'WARNING!!  WARNING!!  WARNING!!  WARNING!!',
                             COLOR['normal'], COLOR['fail'], ' WARNING!!\n\n' ]
            else:
                outstrs.append('DELETING THESE FILES:\n\n')

            outstrs.append('\n'.join(got_files))
            outstrs.append(COLOR['normal'])

            if showwarn:
                outstrs.append('\n\nThese %d files are not within our hidden directory,\n' % len(got_files))
                outstrs.append('and so deleteing them may be noticed by the system operators.\n')
                outstrs.append('Super secret tip for those who actually read these prompts:\n')
                outstrs.append('Enter "YESYES" here to avoid several are you sure prompts.\n\n')
                outstrs += [COLOR['fail'], 'Do you really want to delete them?']
            else:
                outstrs.append('\n\nYou can now DELETE THE FILES SHOWN ABOVE ON TARGET if desired.\n\n')
                outstrs.append('ALL of these are within our hidden directory, %s\n\n' % ' '.join(hidden_dirs))
                outstrs += ['Do you want to ', COLOR['fail'], 
                            'DELETE THESE %d TARGET FILES?' % len(got_files)]

            # ask to delete and do multiple times if need to
            if not skipprompt:
                ans = self.nopen.getInput(''.join(outstrs), 'N', COLOR['normal'])

                if ans.lower() in ['y', 'yes']:
                    if showwarn:
                        ans = self.nopen.getInput('\nReally?', 'N', COLOR['normal'])

                        if ans.lower() in ['y', 'yes']:
                            self.nopen.doit('-beep 3')
                            ans = self.nopen.getInput('\nSeriously, last chance. ARE YOU SURE?', 'N', COLOR['normal'])

                            if ans.lower() in ['y', 'yes']:
                                dodelete = True
                    else:
                        dodelete = True

                elif ans == 'YESYES':
                    dodelete = True

            # finally do the deletion if YES
            if dodelete:
                self.delete_files(got_files)
            else:
                self.doprint('\nNot deleting the files.\n')

        if not imported:
            return self.nopen.finish(finaloutput_list)
        else:
            return finaloutput_list


if __name__ == '__main__':

    imported = False

    try:
        # re-set the argv b/c NOPEN will do weird things with splitting args
        argv = shlex.split(' '.join(sys.argv))
        nopenlss().main(argv)
    except Exception, e:
        print '\n\n%sUnhandled python exception: %s%s\n\n' % \
            (COLOR['bad'], str(e), COLOR['normal'])
        print '%sStack trace:\n' % COLOR['fail']
        traceback.print_exc()
        print COLOR['normal']
