#!/usr/local/bin/python
# VER=2.0.0.2
# 09 FEB 2012

"""
fg UTILITIES
requires:
 + winscp for win32
 + pexpect 2.3 on linux
"""
import re, sys, time, os, getpass, string, traceback
from os import popen
from optparse import OptionParser
from subprocess import * 

try:
	import pexpect
except:
	
	pass


class fg:
	def __init__(self, userLogin, userID, userPassword, server, **kwargs):
		"""
		Initializes class setup some variables.
		fg = fg(userLogin, userID, userPassword, server, kwargs[sharedDIRBool, userDIRBool, diskDIRBool, fileWildcard, debugBool, timeout, privKeyFile])
		"""
		self.sharedDIRBool = self.userDIRBool = self.diskDIRBool = False
		self.fileWildcard = ""
		self.debugBool = False 
		self.timeout = 120
		
        #determine OS
		self.platform = sys.platform
		if self.debugBool: print "Running on %s" % self.platform
		self.userLogin = userLogin
		self.userID = userID
		self.userPassword = userPassword
		self.server = server
		self.remoteDir = ""
		self.destDir = "."
		#self.privKeyFile =  privKeyFile 
		
		if kwargs.__contains__("sharedDIRBool"):
			self.sharedDIRBool = kwargs["sharedDIRBool"]
			if self.sharedDIRBool: self.remoteDir = "/data/shared/"
		if kwargs.__contains__("userDIRBool"):
			self.userDIRBool = kwargs["userDIRBool"]
			if self.userDIRBool: self.remoteDir = "/data/users/" + self.userID + "/"
		if kwargs.__contains__("diskDIRBool"):
			self.diskDIRBool = kwargs["diskDIRBool"]
			if self.diskDIRBool: self.remoteDir = "/data/gc/"

		if kwargs.__contains__("privKeyFile"):
			self.privKeyFile = kwargs["privKeyFile"]
			
		if kwargs.__contains__("fileWildcard"): 
			self.fileWildcard = kwargs["fileWildcard"]

		self.debugBool = kwargs["debugBool"]
		self.timeout = int(kwargs["timeout"])
	
		#ask for a password if the user didn't specify one or a privKeyFile	
		if not self.userPassword and not self.privKeyFile:
			self.userPassword = self.setPass()
		if not self.userID:			
			print "USER ID NOT SET!!"
			exit(0)

		if not os.path.isfile(self.privKeyFile):
			print bcolors.BOLD + bcolors.FAIL + "\n\t[!] Key file does not exist: " + self.privKeyFile + bcolors.ENDC + "\n\n"
			sys.stdout.flush()
			exit(0)

		#this is the host key for the server to SSH into, needed for winscp
		self.host_key = "ssh-rsa 2048 xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx"
		if(self.platform == "linux2"):
			self.sshKeys = [
							'authenticity',
							'assword:',
							'denied',
							'No such file or directory',
							'100%',
							'ETA',
							pexpect.EOF,
							'Permission denied',
							'total '
							]
			self.sftpKeys = [
							'authenticity',
							'assword:',
							'denied',
							pexpect.EOF,
							'sftp>',
							'Connecting to'
							]

#--------------------------------
	def setPass(self):
		"""
		Prompts the user for a password if this class was not passed the password by another script
		"""
		print "\n"
		userPassword = getpass.getpass()
		if self.debugBool: print "Password set: %s" % (userPassword)
		print "\n\n"  
		return(userPassword)

	#--------------------------------
	def fgAutoGet(self):
		"""
		Automatically gets the files. Does a dir, displays the file list, prompts user for all, #, or wildcard get
		"""   
		#if self.debugBool: print "Using options: %s --> %s" % (self.type, self.userLogin)
        
		if(self.platform == "win32"):
			# list the files then display them to the user           
			print "AUTO GET FILES WIN32"
			print "===================================="
			#cmd = 'cmd.exe /c winscp ' + self.userLogin + ":" + self.userPassword + '@' + self.server + " -hostkey\=\"" + self.host_key + "\" /command \"option confirm off\" \"get " + self.remoteDir + self.fileWildcard + "* " + self.destDir + "\ \" exit \n"
			#cmdnopass = 'cmd.exe /c winscp ' + self.userLogin + ":" + "<PASSWORD>" + '@' + self.server + " -hostkey\=\"" + self.host_key + "\" /command \"option confirm off\" \"get " + self.remoteDir + self.fileWildcard + "* " + self.destDir + "\ \" exit \n"
			cmd = 'cmd.exe /c winscp ' + "/console /command \"open " + self.userLogin + ":" + self.userPassword + '@' + self.server + "\" \"option confirm off\" \"get " + self.remoteDir + self.fileWildcard + "* " + self.destDir + "\ \" exit" + " -hostkey\=\"" + self.host_key
			print cmd
			
			#print "SENDING COMMAND: %s" % cmdnopass
			#output = fg.winRunIt(cmd)
			#print "\t[+] " + output.strip() 
			
		elif(self.platform == "linux2"):
			print "AUTO GET FILES LINUX"

			additionalArgs=""
			#If we need to pass some additional args, do so here
			if (self.privKeyFile):
				additionalArgs= '-i ' + self.privKeyFile + ' '
			if (self.fileWildcard[0]=='^'):
				cmd = 'scp ' + str(additionalArgs) + self.userLogin + '@' + self.server + ':' + self.remoteDir +  self.fileWildcard.lstrip('^') + "* " + self.destDir
			else:
				cmd = 'scp ' + str(additionalArgs) + self.userLogin + '@' + self.server + ':' + self.remoteDir + "*" + self.fileWildcard + "* " + self.destDir
			print "===================================="
			print "\t" + cmd
			try:
				outputChild = fg.nixRunIt(cmd, self.sshKeys)
			except CustomException, (instance):
				print bcolors.BOLD + bcolors.FAIL + "\n\t[!] " + instance.parameter + bcolors.ENDC + "\n\n"
				exit(0)
			

	#--------------------------------
	def fgManualGet(self):
		"""
		Provides the user with a list of files then gets the user selected files.
		"""       
		file_re = re.compile(r"^[drwx-]+\s", re.IGNORECASE | re.VERBOSE) 
		if(self.platform == "win32"):
			#cd into directory then dir
			print "====================================\n"
			print " SORRY NOT WORKING YET! PUNT!"
			exit(0)
			#cmd = 'cmd.exe /c winscp ' + self.userLogin + ":" + self.userPassword + '@' + self.server + " -hostkey\=\"" + self.host_key + "\" /command \"cd " + self.remoteDir + "\" dir exit \n"
			#output = fg.winRunIt(cmd)
			
		elif(self.platform == "linux2"):
			additionalArgs=""

			#If we need to pass some additional args, do so here
			if (self.privKeyFile):
				additionalArgs= '-oIdentityFile=' + self.privKeyFile + ' '

			# TODO, implement this with sftp:  sftp -oIdentityFile=/root/testKey op@server
			sftpCmd = 'sftp ' + str(additionalArgs) + self.userLogin + '@' + self.server
			sftpRunCmd='ls -l ' + self.remoteDir
			print sftpCmd + " THEN RUNNING " + sftpRunCmd		
			print "===================================="		
			try:
				#outputChild = fg.sftpRunCmd(sftpCmd,sftpRunCmd, self.sftpKeys)
				result = fg.sftpRunCmd(sftpCmd,sftpRunCmd, self.sftpKeys)
			except CustomException, (instance):
				print bcolors.BOLD + bcolors.FAIL + "\n\t[!] " + instance.parameter + bcolors.ENDC + "\n\n"
				exit(0)
			
			#lines =  string.split(str(outputChild.before), "\r\n")
			#outputChild.close()
			#result =  string.split(str(outputChild.before), "\r\n")
			lines =  string.split(str(result), "\r\n")

			fileList = {}
			print "\t[+] Getting list of files...\n"
			for line in lines:
				if file_re.match(line):
					filename = re.split('\s+', line)
					nf = string.strip(filename[len(filename)-1])
					nftype = string.strip(filename[0])
					if not (nf == "." or nf == ".."):
						fileList[nf] = nftype
			cnt = 1
			keys = fileList.keys()
			keys.sort()
			fileList2 = {}
			for key in keys:
				print "\t[%3s] %10s %s" % (cnt, fileList[key], key)
				fileList2[cnt] = [key, fileList[key]]
				cnt = cnt + 1 
			if cnt > 1:
				print "Please select file(s) to copy: (\"all\" | num,[num...] | part of the filename) q = quit"
				filesget = raw_input('-->')
				print "====================================\n"
			else:
				print "NO FILES WAITING! SKIPPING PROMPT!"
				filesget = "quit"			

			if filesget == "q" or filesget == "quit":
				exit(0)
			elif filesget == "all":
			#get all files
				for key in keys:
					cmd = "scp " + str(additionalArgs) + self.userLogin + "@" + self.server + ":" + self.remoteDir + key + " " + self.destDir
					print "\t[+] " + cmd
					try:
						outputChild = fg.nixRunIt(cmd, self.sshKeys)
					except CustomException, (instance):
						print bcolors.BOLD + bcolors.FAIL + "\n\t[!] " + instance.parameter + bcolors.ENDC + "\n\n"
						exit(0)
					print "\t======="
			#get #,# | # #
			elif re.match("[0-9\,]+", filesget):
				filesget = filesget.replace(", ", ",")
				tmpF = re.split(",|\s", filesget)
				for i in tmpF:
					#catch error when user put in number out of index, or not an INT
					if str(i).isdigit() and int(i) <= int(len(keys)):
						cmd = "scp " + str(additionalArgs) + self.userLogin + "@" + self.server + ":" + self.remoteDir + str(fileList2[int(i)][0]) + " " + self.destDir
						print "\t[+] " + cmd
						try:
							outputChild = fg.nixRunIt(cmd, self.sshKeys)
						except CustomException, (instance):
							print bcolors.BOLD + bcolors.FAIL + "\n\t[!] " + instance.parameter + bcolors.ENDC + "\n\n"
							exit(0)
						print "\t======="
					else:
						#raise CustomException("\t[!] BAD USER INPUT FORMAT! - %s, MALFORMED CHARACTER OR INDEX OUT OF BOUNDS!!" % i)
						if str(i).isdigit() and int(i) > int(len(keys)):

							#try a wildcard get on the file even though it is an integer before bailing out
							getFileStr = "*" +str(i) + "*"
							cmd = "scp " + str(additionalArgs) + self.userLogin + "@" + self.server + ":" + self.remoteDir + getFileStr + " " + self.destDir
							print "\t[+] " + cmd
							try:
								#TODO properly handle the output for when this matches multiple files (it works it just doesn't show all the files that got copied)
								outputChild = fg.nixRunIt(cmd, self.sshKeys)
							except CustomException, (instance):
								print bcolors.BOLD + bcolors.FAIL + "You either entered a number that was invalid or a filename with digits only which apparently wasn't on the server"
								print bcolors.BOLD + bcolors.FAIL + "\n\t[!] " + instance.parameter + bcolors.ENDC + "\n\n"
								exit(0)

							#print bcolors.BOLD + bcolors.FAIL + "\t[!] BAD USER INPUT! <" + str(i) + "> INDEX OUT OF BOUNDS, SKIPPING TO NEXT ONE..." + bcolors.ENDC
							#print "\t======="
						else:
							print bcolors.BOLD + bcolors.FAIL + "\t[!] NO IDEA WHAT YOU DID! <" + str(i) + ">, SKIPPING TO NEXT ONE..." + bcolors.ENDC
							print "\t======="
			#get filename match
			#TODO fixup case where string is given that doesn't match ( ie someone accidentally types filename,1,3 )
			elif re.match('\w+', filesget):
				for key in keys:
					if re.search(filesget, key, re.IGNORECASE | re.VERBOSE):
						cmd = "scp " + str(additionalArgs) + self.userLogin + "@" + self.server + ":" + self.remoteDir + key + " " + self.destDir
						print "\t[+] " + cmd
						try:
							outputChild = fg.nixRunIt(cmd, self.sshKeys)
						except CustomException, (instance):
							print bcolors.BOLD + bcolors.FAIL + "\n\t[!] " + instance.parameter + bcolors.ENDC + "\n\n"
							exit(0)
						print "\t======="
					#This seems to not be needed
					#elif (keys=1):  #if we get througnall keys and no match:
					#	print "DEBUGGING  key " + key + " keys " + str(keys) + " filesget " + filesget
					#	raise CustomException("\t[!] FILE MATCH NOT FOUND! - THINK ABOUT WHAT YOU WANT THEN TRY AGAIN!!")
			else:
				raise CustomException("\t[!] BAD USER INPUT FORMAT! - THINK ABOUT WHAT YOU WANT THEN TRY AGAIN!!")

	#--------------------------------
	def winRunIt(self, cmd):
		"""
		Run a command
		"""
		pass
		#print "Running " + cmd
		#p1 = Popen(cmd, stdout=PIPE, stderr=PIPE)
		#output = p1.communicate()[0]
		#erroutput = p1.communicate()[1]
		#p1.wait()
		#return output
	#--------------------------------
	def sftpRunCmd(self, sftpConnectCmd, sftpCommand, expectKeys):

		child = pexpect.spawn(sftpConnectCmd, timeout=self.timeout,)
		seen = child.expect(expectKeys)
		workedB = False
		printWorkedCNT = 0
		cnt = 0
		cnt2 = 0

		#yup, this is a horrible duplication of code
		while seen != 3:

			#print "Debugging " + str(child)
			cnt = cnt + 1
			if printWorkedCNT == 1:
				sys.stdout.write(bcolors.OKGREEN + "\r[OK]" + bcolors.ENDC + "\n")
				sys.stdout.flush()
				sys.stdout.write("\t[+] RUNNING COMMAND [ " + sftpConnectCmd + " ]")
				sys.stdout.flush()
			#~~~~~~~~~~~~~~~
			#authenticty
			if seen == 0:
				sys.stdout.write("\t[+] ACCEPTING RSA KEY...")
				sys.stdout.flush()
				child.sendline('yes')
				seen = child.expect(expectKeys)
				sys.stdout.write(bcolors.OKGREEN + "\r[OK]" + bcolors.ENDC + "\n")
				sys.stdout.flush()
			#assword:
			if seen == 1:
				child.sendline(self.userPassword)
				if cnt2 < 1: 
					sys.stdout.write("\t[+] AUTHENTICATING WITH SSH SERVER...")
					sys.stdout.flush()
				else:
					if cnt2 == 1:
						sys.stdout.write("\r|")
						sys.stdout.flush()
					if cnt2 == 2:
						sys.stdout.write("\r/")
						sys.stdout.flush()
					if cnt2 == 3:
						sys.stdout.write("\r-")
						sys.stdout.flush()
					if cnt2 == 4:
						sys.stdout.write("\r\\")
						sys.stdout.flush()
						cnt2 = 0
				cnt2 = cnt2 + 1
				seen = child.expect(expectKeys)
			#sftp>
			if seen == 4:
				sys.stdout.write(bcolors.OKGREEN + "\r[OK]" + bcolors.ENDC + "\n")
				sys.stdout.flush()
				print "Sending command " + sftpCommand 
				sys.stdout.flush()
				child.sendline(sftpCommand)
				seen = child.expect(expectKeys)
				sys.stdout.write(bcolors.OKGREEN + "\r[OK]" + bcolors.ENDC + "\n")
				sys.stdout.flush()
				workedB = True
				#print "DEBUGGING case 4 " + str(child)
				result=str(child.before)
				
				#now quit and cleanup
				child.sendline("quit")
				seen = child.expect(expectKeys)
				child.close()
				return result
			#Connecting to ...
			if seen == 5:
				print "Connecting to server"
				seen = child.expect(expectKeys)
				

		if workedB: 
			sys.stdout.write(bcolors.OKGREEN + "\r[OK]" + bcolors.ENDC + "\n")
			sys.stdout.flush()
			sys.stdout.write(bcolors.OKGREEN + "[OK]" + bcolors.ENDC + "\t[+] SESSION COMPLETE!\n")
			sys.stdout.flush()
		else: 
			print bcolors.BOLD + bcolors.FAIL + "\n\t[!] CONNECTION ERROR - CHECK IP ADDRESS, USERNAME, OR PASSWORD\n\n"
			sys.stdout.flush()
		#seen = child.expect(expectKeys)
		return(child)
	#--------------------------------
	def nixRunIt(self, cmd, expectKeys):
		"""
		Controls Pexpect for 
		"""
		child = pexpect.spawn(cmd, timeout=self.timeout,)
		seen = child.expect(expectKeys)
		workedB = False
		printWorkedCNT = 0
		cnt = 0
		cnt2 = 0
		while seen != 6:
			cnt = cnt + 1
			if printWorkedCNT == 1:
				sys.stdout.write(bcolors.OKGREEN + "\r[OK]" + bcolors.ENDC + "\n")
				sys.stdout.flush()
				sys.stdout.write("\t[+] RUNNING COMMAND [ " + cmd + " ]")
				sys.stdout.flush()
			#~~~~~~~~~~~~~~~
			#authenticty
			if seen == 0:
				sys.stdout.write("\t[+] ACCEPTING RSA KEY...")
				sys.stdout.flush()
				child.sendline('yes')
				seen = child.expect(expectKeys)
				sys.stdout.write(bcolors.OKGREEN + "\r[OK]" + bcolors.ENDC + "\n")
				sys.stdout.flush()
			#assword:
			if seen == 1:
				child.sendline(self.userPassword)
				if cnt2 < 1: 
					sys.stdout.write("\t[+] AUTHENTICATING WITH SSH SERVER...")
					sys.stdout.flush()
				else:
					if cnt2 == 1:
						sys.stdout.write("\r|")
						sys.stdout.flush()
					if cnt2 == 2:
						sys.stdout.write("\r/")
						sys.stdout.flush()
					if cnt2 == 3:
						sys.stdout.write("\r-")
						sys.stdout.flush()
					if cnt2 == 4:
						sys.stdout.write("\r\\")
						sys.stdout.flush()
						cnt2 = 0
				cnt2 = cnt2 + 1
				seen = child.expect(expectKeys)
			#denied:
			if seen == 2:
				workedB = False
				child.kill(0)
				raise CustomException("ACCESS DENIED! - CHECK USERNAME OR PASSWORD\n\n\t!! IF YOU SEE A DIALOG BOX CLOSE PRESS CANCEL !!")
			#'No such file or directory',
			if seen == 3:
				#workedB = False
				child.kill(0)
				sys.stdout.write(bcolors.OKGREEN + "\r[OK]" + bcolors.ENDC + "\n")
				sys.stdout.flush()
				raise CustomException("FILE MATCH NOT FOUND! - MAYBE THERE ARE NO FILES WAITING FOR YOU ON THE SERVER?")
			#100%
			if seen == 4:
				printWorkedCNT = printWorkedCNT + 1
				workedB = True
				sys.stdout.write(bcolors.OKGREEN + "\r[OK]" + bcolors.ENDC + "\n")
				sys.stdout.flush()
				sys.stdout.write("\t")
				sys.stdout.flush()
				tmpStr = str(child.before)
				tmpStr = tmpStr.replace("\r", "")
				tmpStr = tmpStr.replace("\d", "")
				tmpStr = tmpStr.replace("\n", "")
				sys.stdout.write(tmpStr)
				sys.stdout.flush()
				seen = child.expect(expectKeys)
			#ETA
			if seen == 5:
				printWorkedCNT = printWorkedCNT + 1
				workedB = True
				if cnt == 1:
					sys.stdout.write("\r|")
					sys.stdout.flush()
				if cnt == 2:
					sys.stdout.write("\r/")
					sys.stdout.flush()
				if cnt == 3:
					sys.stdout.write("\r-")
					sys.stdout.flush()
				if cnt == 4:
					sys.stdout.write("\r\\")
					sys.stdout.flush()
					cnt = 1
				seen = child.expect(expectKeys)
			#Permission denied
			if seen == 7:
				workedB = False
				child.kill(0)
				raise CustomException("ACCESS DENIED! - CHECK USERNAME OR PASSWORD\n\n\t!! IF YOU SEE A DIALOG BOX CLOSE PRESS CANCEL !!")
			workedB = True
			#total   (result from an ls when a key is used versus password authentication)
			if seen == 8:
				wokedB = True
				sys.stdout.write("\t[+] REMOTE LISTING COMPLETE.")
				sys.stdout.flush()
				seen = child.expect(expectKeys)

		if workedB: 
			sys.stdout.write(bcolors.OKGREEN + "\r[OK]" + bcolors.ENDC + "\n")
			sys.stdout.flush()
			sys.stdout.write(bcolors.OKGREEN + "[OK]" + bcolors.ENDC + "\t[+] SESSION COMPLETE!\n")
			sys.stdout.flush()
		else: 
			print bcolors.BOLD + bcolors.FAIL + "\n\t[!] CONNECTION ERROR - CHECK IP ADDRESS, USERNAME, OR PASSWORD\n\n"
			sys.stdout.flush()
		#seen = child.expect(expectKeys)
		return(child)
		
	#--------------------------------
class CustomException(Exception):
	"""
	Custom Exceptions...kinda
	"""
	def __init__(self, value):
		self.parameter = value
	def __str__(self):
		return repr(self.parameter)
		
#--------------------------------
class bcolors:
	"""
	Pretty colors on the console
	"""
	HEADER  = '\033[95m'
	OKBLUE  = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	def disable(self):
		self.HEADER = ''
		self.OKBLUE = ''
		self.OKGREEN = ''
		self.WARNING = ''
		self.FAIL = ''
		self.BOLD = ''
		self.ENDC = ''
		
#--------------------------------

if(__name__ == "__main__"):
	"""
	Main
	"""
	# setup args
	VER = '2.0.0.1'
	parser = OptionParser(usage='%prog -l <USERLOGIN> -u <USERID> -p <USERPASS> -s <SERVER> (--sharedDIR|--userDIR|--diskDIR) [-f PART_OF_FILENAME]', add_help_option = True)	
	#connection info
	parser.add_option("-v", dest="versionB", action="store_true", default=False)
	parser.add_option("-l", "--LoginUser", dest="userLogin", help="Your server login username")
	parser.add_option("-u", "--userID", dest="userID", help="Your user ID number")
	parser.add_option("-p", "--pass", dest="userPassword", default=None, help="Your password")
	parser.add_option("-s", "--server", dest="server", help="The server to connect to")
	#types
	parser.add_option("--sharedDIR", dest="sharedDIRBool", action="store_true", default=False, help="Get files from shared directory")
	parser.add_option("--userDIR", dest="userDIRBool", action="store_true", default=False, help="Get files from user directory")
	parser.add_option("--diskDIR", dest="diskDIRBool", action="store_true", default=False, help="Get files from disk directory")
	parser.add_option("-f", "--file", dest="fileWildcard", default=None, help="Get files with this wildcard; REGEX used => .*YOURTEXT.*")	
	parser.add_option("-i", "--privKeyFile", dest="privKeyFile", default=None, help="Keyfile to use for server authentication")
	
	parser.add_option("--debug", dest="debugBool", action="store_true", default=False, help="Prints more stuff to the screen")
	parser.add_option("--timeout", dest="timeout", default=120, help="Overrides the timeout for ssh sessions to server")
	(options, sys.argv) = parser.parse_args(sys.argv)
	
	#print "login:" + options.userLogin + "\nuser:" + options.userID + "\npass:" + options.userPassword + "\nserver:" + options.server + "\nshared:" + str(options.sharedDIRBool) + "\nuser:" + str(options.userDIRBool) + "\ndisk:" + str(options.diskDIRBool) + "\nwildcard:" + str(options.fileWildcard) + "\ndebug:" + str(options.debugBool) + "\ntimeout:" + str(options.timeout)
	
	if options.versionB:
		print VER
		exit(0)

	#User must put in one of these options or fail!
	if not(options.sharedDIRBool or options.userDIRBool or options.diskDIRBool):
		print "\n\n!!! DID NOT SPECIFY TYPE !!!\n\t[--sharedDIR | --userDIR | --diskDIR]\n\n"
		exit(0)

	try:
	   fg = fg(options.userLogin, options.userID, options.userPassword, options.server, sharedDIRBool=options.sharedDIRBool, userDIRBool=options.userDIRBool, diskDIRBool=options.diskDIRBool, fileWildcard=options.fileWildcard, debugBool=options.debugBool, timeout=options.timeout, privKeyFile=options.privKeyFile)
	   
	except:
		print "\n\n!!! FG EXCEPTION !!!\n!!! CHECK USAGE !!!"
		print "usage: fg.py -l <USERLOGIN> -u <USERID> -p <USERPASS> -s <SERVER> (--sharedDIR|--userDIR|--diskDIR) [-f PART_OF_FILENAME]\n\n"
		try:
			raise CustomException("ACCESS DENIED! - CHECK USERNAME OR PASSWORD\n\n\t!! IF YOU SEE A DIALOG BOX CLOSE PRESS CANCEL !!")
		except CustomException, (instance):
			print bcolors.BOLD + bcolors.FAIL + instance.parameter + bcolors.ENDC + "\n\n"
			
		if options.debugBool: print sys.exc_info()
		if options.debugBool: print str(traceback.tb_lineno(sys.exc_traceback))
		exit(0)
	#shared
	if options.sharedDIRBool:
		if options.debugBool: print "SHARED!!"
		if options.fileWildcard:
			print "AUTO GET WITH WILDCARD %s" % options.fileWildcard
			try:
				fg.fgAutoGet()
			except CustomException, (instance):
				print bcolors.BOLD + bcolors.FAIL + instance.parameter + bcolors.ENDC + "\n\n"
				exit(0)
		else:
			print "PROMPT USER FILENAMES TO GET"
			try:
				fg.fgManualGet()
			except CustomException, (instance):
				print bcolors.BOLD + bcolors.FAIL + instance.parameter + bcolors.ENDC + "\n\n"
				exit(0)
	#user
	elif options.userDIRBool:
		if options.debugBool: print "USER_DIR!!"
		if options.fileWildcard:
			print "AUTO GET WITH WILDCARD %s" % options.fileWildcard
			try:
				fg.fgAutoGet()
			except CustomException, (instance):
				print bcolors.BOLD + bcolors.FAIL + instance.parameter + bcolors.ENDC + "\n\n"
				exit(0)
		else:
			print "PROMPT USER FILENAMES TO GET"
			try:
				fg.fgManualGet()
			except CustomException, (instance):
				print bcolors.BOLD + bcolors.FAIL + instance.parameter + bcolors.ENDC + "\n\n"
				exit(0)
	#disks
	elif options.diskDIRBool:
		if options.debugBool: print "DISK!!"
		if options.fileWildcard:
			print "AUTO GET WITH WILDCARD %s" % options.fileWildcard
			try:
				fg.fgAutoGet()
			except CustomException, (instance):
				print bcolors.BOLD + bcolors.FAIL + instance.parameter + bcolors.ENDC + "\n\n"
				exit(0)
		else:
			print "PROMPT USER FILENAMES TO GET"
			try:
				fg.fgManualGet()
			except CustomException, (instance):
				print bcolors.BOLD + bcolors.FAIL + instance.parameter + bcolors.ENDC + "\n\n"
				exit(0)

	print "\n\n\n"
#----------------------------------
