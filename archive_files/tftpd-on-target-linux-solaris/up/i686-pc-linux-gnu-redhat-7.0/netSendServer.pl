#!/usr/bin/perl

#
# netSendServer.pl
#
# usage:
#
# netSendServer.pl [<port>] [<filename>]
#
#   Default <port>: 6667
#   Default <filename>: "cisco-config"
#
# Listens on the supplied port for connections.  When one arrives,
# copies the supplied filename to the socket.
#
# To test, in another window run:
#
#   nc localhost 6667
#

use Socket;

$port = shift || 6667;
$outputFilename = shift || "cisco-config";
$outputFilenumber = 0;
$proto = getprotobyname('tcp');

($port) = $port =~ /^(\d+)$/                        or die "invalid port";

print "Port is $port\n";

socket(Server, PF_INET, SOCK_STREAM, $proto)        || die "socket: $!";

bind(Server, sockaddr_in($port, INADDR_ANY))        || die "bind: $!";

listen(Server,SOMAXCONN)                            || die "listen: $!";

use POSIX ":sys_wait_h";
sub REAPER {
  my $child;
  while (($waitedpid = waitpid(-1,WNOHANG)) > 0) {
#    print "reaped $waitedpid" . ($? ? " with exit $?" : '');
#    print "\n";
  }
  $SIG{CHLD} = \&REAPER;  # loathe sysV
}

$SIG{CHLD} = \&REAPER;

for ($waitedpid = 0;
     ($paddr = accept(Client,Server)) || $waitedpid;
     $waitedpid = 0, close Client) {
  next if $waitedpid and not $paddr;
  ($port,$iaddr) = sockaddr_in($paddr);
  $name = gethostbyaddr($iaddr,AF_INET);
  print "Connect from $name\n";
  $outputFilenumber++;
  $pid = fork;
  next if $pid;

  $bytesSent = 0;
  open(INPUT, "$outputFilename") || die "open: $!";
  while(($rc = sysread INPUT, $buf, 512) > 0) {
    syswrite Client, $buf, $rc;
    $bytesSent += $rc;
  }
#  while(<INPUT>) {
#    print Client;
#    $bytesSent += length($_);
#  }
  close Client;
  close INPUT;
  ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday) = gmtime(time);
  $now = sprintf "%02d:%02d:%02d", $hour, $min, $sec;
  print "$now Sent file $outputFilename ($bytesSent bytes)\n";
  exit 0;
}



exit 0;


