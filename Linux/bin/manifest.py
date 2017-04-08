#!/usr/local/bin/python3.3

import platform
import argparse
import base64
import configparser
import os
import re
import shlex
import shutil
import subprocess
import zipfile

try:
    import menu
except ImportError:
    try:
        import scrub
    except ImportError:
        print("I cannot find menu.py, please place it in my path and try again")
        raise SystemExit

host_lin_dir = '/mnt/hgfs/host/'
local_lin_dir = '/home/black/tmp/fg/'
host_win_dir = 'X:\\'
local_win_dir = 'D:\\fg\\'


def str2lst(str2conv):
    """ Convert a comma-separated string from type str to type list """
    
    str2conv = str(str2conv)
    if type(str2conv) is str:
        output = []
        str2conv = str2conv.strip("[]")
        str2conv = str2conv.split(",")
        for item in str2conv:
            item = item.strip("' ")
            output.append(item)    
    return output


def check(state):
    """ Check if the Manifest file has already been pulled this Op """
    
    if state.check("Manifest_File") is True:
        return True
    else:
        return False


def process(opname):
    """ Determine the Operating System and execute the appropriate check """
    
    opsys = platform.system()
    manifest = ''
    user_id = None
    disks = None
    preps = None
    op_id = None
    fg_tcpass = None
    
    if opsys == 'Windows':
        (manifest, user_id, disks, preps, op_id, fg_tcpass) = wincheck(opname)
    elif opsys == 'Linux':
        manifest = lincheck(opname)
    else:
        print("\nWRONG OS!!!\n")
        raise SystemExit(1)
    
    #print(manifest, user_id, disks, preps, op_id)
    return(manifest, user_id, disks, preps, op_id, fg_tcpass)


def unzip(manifestdir, manifestzip):
    """ Unzip the MANIFEST archive """
    
    try:
        cur_dir = os.getcwd()
        os.chdir(manifestdir)
        if zipfile.is_zipfile(manifestzip):
            with zipfile.ZipFile(manifestzip) as zip:
                zipfile.ZipFile.extractall(zip)
        os.chdir(cur_dir)
    except zipfile.BadZipFile:
        pass
		

def manifest_list(manifestdir):
    """ Obtain a list of all MANIFEST files and present for selection """

    manifests = []
    dirlist = []
    newdirlist = []
    selection = None
    
    # Populate the list of potential MANIFESTS
    dirlist = os.listdir(manifestdir)

    # Search the manifest directory for potential MANIFEST archives, unzip
    # them, and then add the MANIFEST files to the list
    for file in dirlist:
        if re.search('.+MANIFEST.+', file):
            unzip(manifestdir, file)

    newdirlist = os.listdir(manifestdir)
    for item in newdirlist:
        if re.search('\.MANIFEST$', item):
            manifests.append(manifestdir+item)
    
    # If no candidates are found, do nothing.  If one candidate is found,
    # assume it is the correct one, as all old ones should have been 
    # purged by now.  If multiple candidates are found, present a list 
    # for the user to pick from.
    if len(manifests) == 0:
        print("NONE FOUND")
        
    elif len(manifests) == 1:
        print("Copied and Unzipped to {}\n".format(manifests[0]))
        selection = manifests[0]

    else:
        print("MULTIPLE MANIFESTS found, which should I use: ")
        try:
            mame = scrub.menu.Menu()
        except NameError:
            mame = menu.Menu()
        for item in manifests:
            mame.add_option(item)
        selection = mame.execute(menuloop = False)
        selection = selection['option']
   
    return (selection)
 

def manifest_copy(opname, src_dir, dst_dir):
    """ Copy manifest zips from the host directory to the local directory """

    try:
        dirlist = os.listdir(src_dir)
        if src_dir == host_lin_dir:
            for file in dirlist:
                if re.search('.+MANIFEST.+', file):
                    if str(opname.upper()) in file:
                        shutil.copy(src_dir + file, local_lin_dir)
        elif src_dir == host_win_dir:
            for file in dirlist:
                if re.search('.+MANIFEST.+', file):
                    if str(opname.upper()) in file:
                        shutil.copy(src_dir + file, local_win_dir)
    except:
        print("Error copying MANIFEST from host...")
        
 
def lincheck(opname):
    """ Check for a MANIFEST file and return its pathname """

    selection = None

    # Copy MANIFESTS to the correct directory first
    manifest_copy(opname, host_lin_dir, local_lin_dir)
    
    # Generate a list and save the chosen one
    selection = manifest_list(local_lin_dir)
    
    # In case we could not find a MANIFEST file after checking all 
    # potential locations, don't bother parsing
    if selection == 'Exit' or selection is None:
        pass
    else:
        linparse(selection)


def linparse(manifest):
    """ Parse the MANIFEST and return all required parameters """

    user_id = None
    disks = None
    opname = None
    op_id = None
    fg_tcpass = None
    conn_ip = None
    conn_mask = None
    conn_gw = None
    conn_dns = None

    config = configparser.ConfigParser()

    try:
        config.read(manifest)
        user_id = config.get('op', 'userid')
        disks = config.get('op', 'disks')
        opname = config.get('op', 'project')
        op_id = config.get('op', 'schedid')
        fg_tcpass = config.get('op', 'shdata')
        conn_ip = config.get('connection', 'ip')
        conn_mask = config.get('connection', 'netmask')
        conn_gw = config.get('connection', 'gateway')
        conn_dns = config.get('connection', 'dns')

    except Exception as error:
        print("An error occurred while parsing the MANIFEST file --> {}".
              format(error))

    # Make sure we have everything we need first before proceeding
    if not user_id:
        user_id = input("Please enter your 5-digit user id: ")
    if not disks:
        disks = input("Please enter the desired Opsdisk(s) (comma-separated): ")
    if not opname:
        opname = input("Please enter the Op name: ")
    if not op_id:
        op_id = input("Please enter your 14-digit Op ID: ")
    if not conn_ip:
        conn_ip = input("Please enter your connection IP: ")
    if not conn_mask:
        conn_mask = input("Please enter your connection netmask: ")
    if not conn_gw:
        conn_gw = input("Please enter your connection gateway: ")
    if not conn_dns:
        conn_dns = input("Please enter your connection DNS server IP: ")

    if fg_tcpass:
        try:
            fg_tcpass = base64.b64decode('{}'.format(fg_tcpass))
            fg_tcpass = fg_tcpass.decode('utf-8')
        except Exception:
            pass

    # Pull out the relevant disk(s) from the list and convert to a usable string
    dsk_lst = []
    dsk_lst = str2lst(disks)
    nix_disks = []
    nix_regex = re.compile('nix|rtr|fw', re.IGNORECASE)
    for disk in dsk_lst:
         if re.search(nix_regex, disk):
             nix_disks.append(disk)
    disks = ','.join(nix_disks)

    # Extract the Op name
    op_namelst = []
    op_namelst = str2lst(opname)
    opname = op_namelst[0]

    # Generate the mz line
    mz_line = ''
    mz_line = ('findzip -d {} -s -S {} -I {} -P {} -n {} {}/{}/{}'.
               format(disks, op_id, user_id, opname, conn_dns, 
                      conn_ip, conn_mask, conn_gw))
    print("--- Prepping Ops Station ---\n")
    print("({})".format(mz_line))

    try:
        # Prompt the user to run the self-generated command, enter a new
        # one, or quit
        print()
        answer = input("Would you like me to run the above command? "
                       "(CTRL+C here will exit completely) ([Y]/n): ")
        if re.match('^[Nn]', answer):
            mz_line = input("Please enter the correct mz (findzip) line: ")
        if fg_tcpass:
            print("-"*61)
            print("Here's a hint --> {}".format(fg_tcpass))
            print("-"*61)
    except KeyboardInterrupt:
        raise SystemExit

    # Set the FGTCPASS environment variable and start prepping...
    os.environ['FGTCPASS'] = str(fg_tcpass)
    args = shlex.split(mz_line)
    mz_proc = subprocess.Popen(args).communicate()


def wincheck(opname):
    """ Check for a MANIFEST file, prompting for a manual selection if > 1 """
    
    manifest = ''
    selection = None
    user_id = None
    disks = None
    preps = None
    op_id = None
    fg_tcpass = None
    
    # Copy MANIFESTS to the correct directory first
    manifest_copy(opname, host_win_dir, local_win_dir)
    
    # Generate a list and save the chosen one
    selection = manifest_list(local_win_dir)

    if selection == 'Exit' or selection == None:
        pass
    else:
        (manifest, user_id, disks, preps, 
         op_id, fg_tcpass) = winparse(selection)

    return(manifest, user_id, disks, preps, op_id, fg_tcpass)


def winparse(manifest):
    """ Parse the MANIFEST and return all the required parameters """
    
    user_id = None
    disks = []
    preps = []
    op_id = None
    fg_tcpass = None
    
    config = configparser.ConfigParser()

    try:
        config.read(manifest)
        user_id = config.get('op', 'userid')
        disks = config.get('op', 'disks')
        preps = config.get('op', 'project')
        op_id = config.get('op', 'schedid')
        fg_tcpass = config.get('op', 'shdata')
    except Exception as error:
        print("An error occurred while parsing the MANIFEST file --> {}".
              format(error))
        
    return(manifest, user_id, disks, preps, op_id, fg_tcpass)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a MANIFEST file.')
    parser.add_argument('OPNAME', type=str, nargs=1, help='The opname for '
                        'which to process the manifest file')
    args = parser.parse_args()
    opname = args.OPNAME[0]
        
    process(opname)
