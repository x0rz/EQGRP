#!/bin/env python
import os,sys,binascii,re,time

version = "2.0.0.0"

class clean_wtmps:
	def __init__(self):
		self.original = ""
		self.goodData = ""

	def main(self):
		print version
		if not len(sys.argv) > 1 or str(sys.argv[1]) == "-h":
			print "usage: clean_wtmps.py file [tty] [time]"
			sys.exit(1)

		if not os.path.exists(sys.argv[1]):
			print "File does not exist"
			sys.exit(1)

		self.readwtmps(sys.argv[1])
		#data = self.readwtmps(sys.argv[1])
		#if not data: sys.exit(1)

		if len(sys.argv) == 2:
			self.printStructs()
		elif len(sys.argv) == 4:
			tty = sys.argv[2].strip()
			myTime = binascii.unhexlify(hex(int(sys.argv[3].strip()))[2:])
			#print time
			self.parseOut(tty,myTime,sys.argv[1])

	def readwtmps(self,wtmps):
		print "Reading wtmps file..."

		#goodData = ""
		#original = ""

		f = open(wtmps,'rb')
		self.original = f.read()
		f.close()

		print "Parsing offsets using 652 struct size"
		ans = len(self.original) % 652
		#print ans
		if ans != 0:
			print "File is corrupted.  Attempting to locate invalid offset"
			self.findBroken()
		else:
			self.goodData = self.original

	def findBroken(self):
		count = 0

		for i in range(len(self.original), 0, -652):
			print i
			count += 1
			line = self.original[i-652:i]
			if not re.match("\x00\x00\x02\x88", line):
				print "Located invalid offset at count %d" % count
				print "Walking backwards till I find it"
				numBytes = 0
				while True:
					numBytes += 1
					line = self.original[i-(652+numBytes):i]
					if re.match("\x00\x00\x02\x88", line):
						break

				print "Number of invalid bytes: %d" % numBytes
				break
			else:
				self.goodData = line + self.goodData

		if len(self.goodData) == len(self.original):
			print "Entire file may be corrupt...was unable to find good offsets"

		#default = "n"
		#answer = str(raw_input("Fix wtmps file? [y/N] ")).lower()
		#if not answer:
		#	print "Not fixing"
		#	return False
		#if answer == 'y':
		#	newData = data[:i-numBytes] + data[i:]
		#	ans = len(newData) % 652
		#	if ans == 0:
		#		print "FIXED!"
		#		return newData

		#	return False	

	def printStructs(self):
		for i in range(0,len(self.goodData),652):
			line = self.goodData[i:i+652]
			user = ""
			findUser = re.match("[A-Za-z\.]+",line[4:])
			if findUser:
				user = findUser.group()
			myTime = int(binascii.hexlify(line[352:356]),16)
			prettyTime = time.asctime(time.localtime(int(myTime)))
			#272
			#term = line[272:284].strip()
			term = ""
			termCheck = re.search("(tty|pts)[/]{0,1}[a-z0-9]{0,2}", line)
			if termCheck: term = termCheck.group()
		
			print "%s\t%s\t%s (%s)" % (user, term, str(myTime), str(prettyTime))

	def parseOut(self,tty,myTime,wtmps):
		test = self.goodData[0:652]
		if not re.match("\x00\x00\x02", test):
			print "First entry is not a valid entry"
			return False

		i = 0
		count = 1
		found = False
		numStructs = len(self.goodData) / 652
		newData = ""
		for i in range(0,len(self.goodData),652):
			line = self.goodData[i:i+652]
			count += 1
			#if re.search("%s.+%s" % (tty,time), line):
			if line.find(myTime) != -1:
				#print line.find(time)
				print "Found in struct %d out of %d" % (count, numStructs+1)
				found = True
				if (i+652) == len(self.goodData):
					newData = self.goodData[:i]
				else:
					newData = self.goodData[:i] + self.goodData[i+652:]
				break
		if found is False:
			print "String was not found"
		else:
			if len(self.goodData) != len(self.original):
				newData = self.original[:len(self.original)-len(self.goodData)] + newData

			if len(newData) == len(self.original) - 652:
				print "Cleaned Successfully...iyf"
				f = open(str(sys.argv[1]),'wb')
				f.write(newData)
				f.close()
				print "Data has been written to %s" % str(sys.argv[1])

if __name__ == "__main__":
	clean_wtmps().main()
