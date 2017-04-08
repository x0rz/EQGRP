#!/usr/bin/env python

VERSION = "1.0.0.2"
# Fri Feb 22 13:07:39 EST 2013

import os, re, sys, time
import subprocess, shlex


#####################
##### VARIABLES #####
#####################

blacklist = ['exit','quit','get','put','vi','vim','emacs','gedit', 'reboot',
             'halt', 'shutdown']
current_dir = "/"
debug = 1
sock_file = ''
user = ''
current_loc_dir = '/current/down'


#####################
##### FUNCTIONS #####
#####################

def showhelp():
    print "There are only a few builtin functions to use:"
    print "    -h/-help: This help"
    print "    -get <file>:"
    print "            Gets a file and puts it in the proper %s directory" %current_loc_dir
    print "    -put <locFile> [<remFile>]:"
    print "            Puts a file and optionally names and places it in <remfile>"
    print "    -cd <dir>:"
    print "            This will remotely change your current directory"
    print "    -lsh <cmd>:"
    print "            This executes a command locally"
    print "    -log [-t] <cmd>:"
    print "            This logs any command in the targetcommands directory"
    print "            -t is optional and allows the logged command to also be printed to the screen"
    print "    -exit:"
    print "            This exits the pseudo shell."
    return

def remoteExec(execCmd, savelog):
    if execCmd.rfind("&&") > 0 and execCmd.find("ls") > 0:
        # We just want to keep track of what the ls command did.    One gotcha: if 'ls' is not the
        #        last command executed (i.e. w;ls -la;id), the directory will be appended to the chain of commands
        fullLocalCmd = "%s %s" % (execCmd[execCmd.rfind("&&")+3:], shlex.split(execCmd)[1])
    elif execCmd.rfind("&&") > 0:
        fullLocalCmd = execCmd[execCmd.rfind("&&")+3:]
    else:
        fullLocalCmd = execCmd
    fullLocalCmd = re.sub(r'\W','_',fullLocalCmd)
    fullLocalCmd = "%s_%s" % (fullLocalCmd, time.strftime('%Y%m%d-%H%M%S'))
    fullLocalCmdFile = os.path.join(current_loc_dir+"_targetcommands", fullLocalCmd)
    if savelog:
        execString = "ssh -S %s %s@127.0.0.1 \'%s\' > %s" % (sock_file, user, execCmd, fullLocalCmdFile)
    else:
        execString = "ssh -S %s %s@127.0.0.1 \'%s\'" % (sock_file, user, execCmd)
    if "pwd" in fullLocalCmd:
        results = subprocess.Popen(shlex.split(execString), stdout=subprocess.PIPE).communicate()[0][:-1]
    else:
        os.system(execString)
    if savelog:
        results = subprocess.Popen(shlex.split("cat %s" % fullLocalCmdFile), stdout=subprocess.PIPE).communicate()[0][:-1]
    if savelog and os.path.getsize(fullLocalCmdFile) == 0:
        os.system("rm %s" % fullLocalCmdFile)
        logit("LOC","Cleaned up empty file: %s" % fullLocalCmdFile)
    else:
        logit("CMD",execString)
    try:
        return results
    except:
        return ""

def remoteCheck(fileName):
    execCmd = "ls -la %s 2>/dev/null | wc -l" % fileName
    execString = "ssh -S %s %s@127.0.0.1 \'%s\'" % (sock_file, user, execCmd)
    logit("DBG","Checking to see if %s exists on target" % fileName)
    results = subprocess.Popen(shlex.split(execString), stdout=subprocess.PIPE).communicate()[0][:-1]
    if re.match('^\s*0\s*$', results) != None:
        return 0
    else:
        return 1

def localExec(execCmd):
    logit("DBG","Locally executing %s" % execCmd)
    if execCmd[0] == "cd":
        os.chdir(execCmd[1])
        return ""
    try:
        if execCmd.__class__() == []:
            execCmd = ' '.join(execCmd)
        results = subprocess.Popen(execCmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).communicate()[0][:-1]
    except OSError:
        return "Error: no such directory"
        logit("DBG","Error: no such directory")
    return results

def getMe(remFile, locFile, currentDir):
    locDir = current_loc_dir
    locFileFull = os.path.normpath(os.path.join(locDir, os.path.join(currentDir, remFile)[1:]))
    remoteExistence = remoteCheck(os.path.join(currentDir,remFile))
    if not remoteExistence:
        print "Error: that file doesn't exist on target."
        return
    if os.path.isfile(locFileFull):
        print "Moving the file aside..."
        ext_num = 0
        while os.path.exists('%s_%04d' % (locFileFull,ext_num)):
            ext_num += 1
        locFileFullNew = "%s_%04d" % (locFileFull,ext_num)
        print "Executing: mv %s %s" % (locFileFull,locFileFullNew)
        os.system("mv %s %s" % (locFileFull,locFileFullNew))
        logit("LOC","Moving %s aside to %s" % (locFileFull, locFileFullNew))
    execString = "ssh -S %s %s@127.0.0.1 \'cd %s && cat %s\' > %s; ls -la %s" % (sock_file, user, currentDir, remFile, locFileFull, locFileFull)
    try:
        os.makedirs(os.path.split(locFileFull)[0])
    except OSError:
        pass
    logit("GET", execString)
    os.system(execString)
    return

def putMe(locFile, remFile, currentDir):
    locFileFull = locFile
    if locFile.rfind("/") == -1: #Relative path, so get absolutepath
        locFileFull = os.path.join(localExec("pwd"),locFile)
    remFileFull = remFile
    if remFile.rfind("/") == -1: # Relative path for remote file, so get absolute path
        remFileFull = os.path.join(currentDir,remFile)
    if not os.path.isfile(locFileFull):
        print "Error: that file doesn't exist."
        logit("DBG","Error: that file doesn't exist.")
        return
    remFileExist = remoteCheck(remFileFull)
    if remFileExist:    # For right now, you can't clobber files
        print "Error: that file on target already exists!"
        logit("DBG","Error: that file on target already exists!")
        return
    execString = "cat %s | ssh -S %s %s@127.0.0.1 \'cat > %s && ls -la %s\'" % (locFileFull, sock_file, user, remFileFull, remFileFull)
    logit("PUT", execString)
    os.system(execString)
    return

def sanitizeDir(oldPath, newPath):
    return remoteExec("cd %s && pwd" % os.path.join(oldPath, newPath), 0)

def logit(theFunc, theCommand):
    if theFunc != "DBG" or debug == 1:
        logLine = "[%s %s] %s" % (time.strftime('%a %d %b %Y %H:%M:%S'), theFunc, theCommand)
        logLine = re.sub(r'\|','_',logLine)
        os.system("echo \"%s\" >> /current/down/%s.cmd_history" % (logLine,sys.argv[3]))


def usage(prog):
    print "Usage: %s sock_file user hostname.ip" % prog
    sys.exit(1)


def version(prog):
    print "%s version %s" % (os.path.basename(prog), VERSION)
    sys.exit(1)


def expandGlob(path):
    execCmd = "find %s -maxdepth 0 -type f 2>/dev/null" % path
    execString = "ssh -S %s %s@127.0.0.1 \'%s\'" % (sock_file, user, execCmd)
    logit("DBG","Expanding a globbed command: %s" % path)
    results = subprocess.Popen(shlex.split(execString), stdout=subprocess.PIPE).communicate()[0][:-1]
    return shlex.split(results)
    


#####################
####### MAIN ########
#####################

def main(argv):
    global sock_file
    global user
    global current_loc_dir

    if len(argv) > 1:
        if argv[1] == '-h':
            usage(argv[0])
        elif argv[1] == '-v':
            version(argv[0])

    if len(argv) != 4:
        usage(argv[0])

    sock_file = argv[1]
    user = argv[2]
    current_loc_dir = os.path.join('/current/down', argv[3])

    # Let's do some sanity checks first:
    if not os.path.exists(sock_file):
        sys.exit("Socket '%s' doesn't exist, is that the right socket?" % sock_file)
    if not os.path.isdir(current_loc_dir):
        response = raw_input("Directory '%s' doesn't exist, do you want it to be made? (yes, no)" % current_loc_dir)
                 
        if response.lower() == "yes" or response.lower() == "y":
            os.makedirs(current_loc_dir)
            os.makedirs(current_loc_dir + "_targetcommands")
        else:
            sys.exit("Directory was not made.")

    # Alright, we should be good, so let's start up the shell loop
    init_ssh = "ssh -S %s %s@127.0.0.1 \'pwd\'" % (sock_file, user)
    current_dir = subprocess.Popen(shlex.split(init_ssh), stdout=subprocess.PIPE).communicate()[0][:-1]

    while True:
        prompt = "%s$> " % current_dir
        command = raw_input(prompt)
        if not command:
            continue
        params = shlex.split(command)
        action = params[0]
        options = params[1:]
        logit("DBG","You entered '%s' with the following options: %s" % (action, options))
        print '[%s]' % command
        if action in blacklist:
            print "Action '%s' is blacklisted." % action
            continue
        if action == "-exit":
            break
        elif action == "-h" or action == "-help":
            showhelp()
            continue
        elif action == "-get":
            if len(options) == 1:
                if options[0].find("*")+1:
                    files_to_get = expandGlob(options[0])
                else:
                    files_to_get = [options[0]]
                for file in files_to_get:
                    print "Getting file %s" % (file)
                    getMe(file, os.path.split(file)[1], current_dir)
            else:
                print "-get <remote_file>"
        elif action == "-put":
            if len(options) == 1:
                print "Putting file %s" % (options[0])
                putMe(options[0], options[0], current_dir)
            elif len(options) == 2:
                print "Putting file %s as %s " % (options[0], options[1])
                putMe(options[0], options[1], current_dir)
            else:
                print "-put <local_file> <remote_file_name>"
        elif action == "-cd":
            if len(options) == 1:
                print "CDing to directory %s" % (options[0])
                current_dir = sanitizeDir(current_dir, options[0])
            else:
                print "-cd <directory>"
        elif action == "-lsh":
            print localExec(options)
        elif action == "-log":
            if options[0] == "-t":
                newcmd_string = ' '.join(options[1:])
                newcmd = "cd %s && %s" % (current_dir,newcmd_string)
                print remoteExec(newcmd, 1)
            else:
                newcmd_string = ' '.join(options)
                newcmd = "cd %s && %s" % (current_dir,newcmd_string)
                dummyVar = remoteExec(newcmd,1) #Save and throw away the output
        else:    #Execute the action
            newcmd = "cd %s && %s" % (current_dir,command)
            remoteExec(newcmd, 0)


if __name__ == '__main__':
    main(sys.argv)
