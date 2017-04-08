from socket import *
from time import sleep
import getopt
import sys
import logging
import threading
logging.basicConfig(level = logging.ERROR)
log = logging


Version = "1.2"


def usage():
	print "MysticTunnels Version  " + Version
	print "Usage: " + sys.argv[0] + " <options>"
	print "\t--lport  <port> default:690\t<listen port, point nopen to this>"
	print "\t--oport  <port> default:699\t<source port, output of the local tunnel>"
	print "\t\t !!! These are only exposed in case you get a port bound error or are just that bored\n"
	print "\t--tport <port> default:69\t<dest port, port that tftp is bound locally,(verify that tftp bound, netstat -anp)>"
	print "\t--sip  <ip>    default:127.0.0.1\t<IP to forward data to>"
	print "\t--lip  <ip>    default:127.0.0.1\t<IP to listen on>" 
	print "\tThis is a UDP tunnel mechanism for avoiding tftp issues through nopen but feel free to find new and exciting ways to leverage it."
	print "\nNow with Sentrytribe!!\n\t--sentry   Sets defaults for a sentrytribe trampoline. You can change the defaults with other args"
	print "\t Default will be l 5000 192.168.254.72 5000"
	print "\n\n\tGo forth and be merry"
	sys.exit(0)


def checkports():
	try:
		if t2.srcport:
			t.destport = t2.srcport
	except NameError:
		log.debug("T2 not Defined yet.")

class sockbuild():
	def __init__(self, port, addr="127.0.0.1", addrfam=AF_INET, socktype=SOCK_DGRAM):
		self.port = port
		self.addr = addr
		self.addrfam = addrfam
		self.socktype = socktype
	def build(self):
		self.newsock = socket(self.addrfam, self.socktype)
		self.newsock.bind((self.addr, self.port))
		return self.newsock


class Socketeer(threading.Thread):
	def __init__(self,  event, checkports, recsock, sendsock, dstaddr="127.0.0.1", destport=69):
		threading.Thread.__init__(self)
		self.destport = destport
		self.dstaddr = dstaddr
		self.recsock = recsock
		self.sendsock = sendsock
		self.srcip = False 
		self.srcport = False
		self.event = event
		self.checkports = checkports

	def udprec(self):
		log.debug("%s waiting for data", self.getName())
		try:
			data, addr = self.recsock.recvfrom(1024)
			self.srcip, self.srcport = addr
			self.newdata = data
			if data:
				store = self.srcip
				self.event.set()
		except timeout:
			log.info("Connection ended due to timeout")
			self.newdata = False

	def udpsend(self, ip, port):
		self.checkports()
		log.debug("Sending data via %s to %s on %s"% (self.getName(), self.dstaddr, self.destport))
		self.sendsock.sendto(self.newdata,(self.dstaddr,self.destport))

	def run(self):
		print "Starting new thread %s" % self.getName()
		while True:
			self.udprec()
			if not self.newdata:
				continue
			self.udpsend(self.dstaddr, self.destport)

if __name__ == '__main__':
	listenport = 690
	sourceport = 699
	destport = 69
	addr="127.0.0.1"
	dstaddr="127.0.0.1"
	sip=False
	sentry = False 
	addrfam=AF_INET
	socktype=SOCK_DGRAM
	try:
		options, remainder = getopt.getopt(sys.argv[1:], '',["lport=", "oport=", "tport=", "sip=","lip=", "sentry"])
	except getopt.GetoptError as e:
		print "\n\n######################################"
		usage()
	for opt, arg in options:
		if opt == "--sentry":
			sentry = True
			addr = "" if addr == "127.0.0.1" else addr
			dstaddr = "192.168.254.72" if dstaddr == "127.0.0.1" else dstaddr
			destport = 5000 if destport == 69 else destport
			listenport = 5000 if listenport == 690 else listenport
		elif opt == "--lport":
			listenport = int(arg)
		elif opt == "--oport":
			sourceport = int(arg)
		elif opt == "--tport":
			destport = int(arg)
		elif opt == "--sip":
			sip = True
			dstaddr = arg
		elif opt == "--lip":
			addr = arg

	if sip:
		print("Your tunnel is listening on %s sending data to %s %s"%(listenport, dstaddr, destport))	
	elif sentry:
		print("SentryTribe Mode listening on %s sending data to %s  port %s"%(listenport, dstaddr, destport))
	else:
		print ("Your setup should be:\n\t-rutun 69 127.0.0.1 %s\n\tYour tftp server should be bound on %s" %(listenport, destport))

	sockt = sockbuild(listenport, addr, addrfam, socktype).build()
	sockt2 = sockbuild(sourceport, addr, addrfam, socktype).build()
	event = threading.Event()
	t = Socketeer(event, checkports, sockt, sockt2, dstaddr, destport)
	t.daemon=True
	try:
		t.start()
		while not event.wait(7):
			pass
		log.debug("Data Recieved starting thread 2.")
		t2 = Socketeer(event, checkports, sockt2, sockt, t.srcip, t.srcport)
		t2.daemon=True
		t2.start()	
		log.debug("Waiting to join.")
		while t.is_alive():
			t.join(7)

	except KeyboardInterrupt:
		print "Boom Headshot"
		quit()




