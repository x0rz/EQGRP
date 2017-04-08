#!/usr/local/bin/python3.3

import os
import re
import subprocess
from time import sleep

host_share = '/mnt/hgfs/host/'
opname_file = (host_share + 'opname.txt')
site_file = (host_share + 'site.txt')


def check_site():
    """" Determine the site so we contact the correct FG server """

    fg_srv = ''
    site = ''
    selection = ''

    # Determine the site
    if os.path.exists(site_file):
        with open(site_file) as file:
            line = file.readline()
            site = line.strip()

    else:
        print("\nI could not determine the site. Please choose one below:")
        print("-"*61)
        print("1) North")
        print("2) South")
        print("3) East")
        print("4) West")
        print()
        while selection == '':
            try:
                selection = input("Selection: ")
                if selection == '1':
                    site = 'North'
                    break
                elif selection == '2':
                    site = 'South'
                    break
                elif selection == '3':
                    site = 'East'
                    break
                elif selection == '4':
                    site = 'West'
                    break
                else:
                    selection = ''
            except KeyboardInterrupt:
                print()
        print()
    
    # Set the FG server address based on the site
    if site == 'North':
        fg_srv = '10.0.129.254'
    elif site == 'South':
        fg_srv = '10.11.129.253'
    elif site == 'East':
        fg_srv = '10.21.129.254'
    elif site == 'West':
        fg_srv = '10.31.129.254'
    else:
        fg_srv = '10.0.129.254'

    return (fg_srv)


def execute():
    """ Determine Opname and pull correct manifest """

    try:
        opname = None

        if os.path.exists(opname_file):
            with open(opname_file, 'r') as file:
                line = file.readline()
                opname = line.strip()
                opname = opname.upper()
            answer = ''
            print()
            answer = input("Is '{}' the correct Op name? ([Y]/n): ".
                           format(opname))
            if re.match('[Nn]', answer):
                opname = input("Please enter the correct Op name now: ")
                opname = opname.upper()
		
        else:
            opname = input("Please enter the correct Op name: ")
            opname = opname.upper() 

        # Now that we know the Opname, check to see if someone else 
        # already pulled a MANIFEST zip
        contents = []
        manifest_here = False
        if os.path.exists(host_share):
            contents = os.listdir(host_share)
            for item in contents:
                if re.match('.*MANIFEST.*\.zip$', item):
                    manifest_here = True
                    break
        
        # If a manifest is found in the host share directory, 
        # proceed to parsing it    
        print("Getting Manifest for {}...".format(opname), end="", flush=True)

        if manifest_here:
            manifest_proc = subprocess.Popen(['python3', '/root/manifest.py', 
                                              '{}'.format(opname)]).communicate()
        else:
            # Determine the correct FG server
            fg_srv = check_site()

            # SCP the MANIFEST down to our local staging area
            scp_retval = subprocess.call(['scp', 
                                          '-oIdentityFile=/etc/keyfile.scp', 
                                          '-oStrictHostKeyChecking=no',
                                          'op@{}:/data/opsetup/*{}*.zip'.
                                          format(fg_srv, opname), 
                                          '/home/black/tmp/fg/'], 
                                          stdout=subprocess.DEVNULL, 
                                          stderr=subprocess.DEVNULL)

            if scp_retval == 1:
                print("I could not find a Manifest, exiting in 5 seconds...\n")
                sleep(5)
            elif scp_retval == 0:
                # Now we have a MANIFEST, parse it
                manifest_proc = subprocess.Popen(['python3', 
                                                  '/root/manifest.py', '{}'.
                                                  format(opname)]).communicate()

    except KeyboardInterrupt:
        print('\n\nGood bye...\n')

if __name__ == '__main__':
	execute()
