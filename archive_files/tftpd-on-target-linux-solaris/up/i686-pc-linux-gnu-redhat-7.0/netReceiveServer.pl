#!/usr/bin/perl

#
# netReceiveServer.pl
#
# usage:
#
# netReceiveServer.pl [<port>] [<filename>]
#
#   Default <port>: 6666
#   Default <filename>: "cisco-config"
#
# Listens on the supplied port for connections.  When one arrives,
# copies the stream on the connection to the supplied filename.
# A one up from one number is appended to the filenames.
#
# To test, in another window run:
#
#   nc localhost 6666 <cisco-config
#

use Socket;

$port = shift || 6666;
$outputFilename = shift || "cisco-config";

$outputFilenumber = 0;

sub makeNextFilename {
  $doneLooping = 0;
  while(not $doneLooping) {
    $outputFilenumber++;
    $trial = "$outputFilename.$outputFilenumber";
    open(TRIAL, "<$trial") || $doneLooping++;
    $doneLooping || close TRIAL;
  }
}

$proto = getprotobyname('tcp');

($port) = $port =~ /^(\d+)$/                        or die "invalid port";

print "Port is $port\n";

socket(Server, PF_INET, SOCK_STREAM, $proto)        || die "socket: $!";

bind(Server, sockaddr_in($port, INADDR_LOOPBACK))        || die "bind: $!";

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
  makeNextFilename;
  $pid = fork;
  next if $pid;

  $bytesReceived = 0;
  open(OUTPUT, ">$outputFilename.$outputFilenumber") || die "open: $!";
  while(($rc = sysread Client, $buf, 512) > 0) {
    syswrite OUTPUT, $buf, $rc;
    $bytesReceived += $rc;
  }
  close Client;
  close OUTPUT;
  ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday) = gmtime(time);
  $now = sprintf "%02d:%02d:%02d", $hour, $min, $sec;
  print "$now Received file $outputFilename.$outputFilenumber ($bytesReceived bytes)\n";
  exit 0;
}



exit 0;


