#!/usr/bin/env perl
use File::Basename ;
use File::Copy ;
require Time::Local;
require "getopts.pl";
$VER="1.1.0.2" ;
$outfile = "unixdump";
$outdir = "/home/black/tmp/pcaps";
mkdir $outdir unless -d $outdir;
$SIG{INT} = \&catch_zap;
$SIG{TERM} = \&catch_zap;
$delaysecs = 2;

myinit() ;
dbg("Fresh instance of $prog on $intf RESTART=$restart ourip=$ourip");

my %ipshit = ();
while (1) {
  # Re-loop forever here. If between loops eth0 goes down, comes up, 
  # a new /current link is made, etc., we are good. That's what we want,
  # is to always log on eth0, always to /current, do nothing if eth0 is
  # not there.
  $intf_info = `ifconfig $intf 2>/dev/null`;
  ($ourip) = $intf_info =~ /\sinet addr:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s/;
  unless ($intf_info =~ /UP /) {
    last unless mastercheck();
# Have to remove this will fill up /current/tmp partition
#    dbg("Interface $intf is not up....waiting $delaysecs secs trying again.");
    sleep $delaysecs;
    next;
  }
  # Start the ascii tcpdump to read from. We parse this
  # and for each new IP we do not currently have a pcap
  # running on, we fork and start one.
  unless(open(TCPDUMP,"tcpdump -l -n -n -i $intf ip |")) {
    last unless mastercheck();
# Have to remove this will fill up /current/tmp partition
#    dbg("Could not start tcpdump on $intf, waiting a few seconds, trying again");
    sleep $delaysecs;
    next;
    exit 1;
  }

  while (<TCPDUMP>) {
    last unless mastercheck();
    chomp;
    #  dbg("parsing:$_");
    my $newip = "";
    my $dbg="";
    if (/ IP $ourip.* > (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/) {
      $newip = $1;
      $dbg="found ours=$ourip > $newip";
    } elsif ( / IP (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).* > $ourip/) {
      $newip = $1;
      $dbg="found $newip > ours=$ourip";
    }
    next unless $newip ;
    next if $ipshit{$newip}++;
    $tstamp = timestamp(short);
    $capfile = "$outfile.${tstamp}_${newip}__${ourip}";
    dbg("$dbg LINE=$_ THIS WILL START tcpdump -w to $capfile");
    startdump($intf,$newip,$capfile,$_);
  }
  undef %ipshit;
  dbg("KILLED/DYING:tcpdump -l -n -n -i $intf ip");
  last unless mastercheck();
  dbg("Looping around for more, set RESTART=die to kill me.");
}
mydie("exiting: end of main");
exit 0;
## END MAIN LOGIC

##### SUBROUTINES #####
sub mastercheck {
  # We are done here if our $masterfile is gone,
  # means theres a new master. This returns true
  # if we ARE STILL THE MASTER.
  return 1 if (-e $masterfile);
  dbg("New master in town");
  return 0;
}

sub startdump {
  my $kidpid = fork;
  return $kidpid if $kidpid;
  # Child continues
  local($intf,$newip,$capfile,$line) = (@_);

  # We put the $line that our (ascii) tcpdump saw
  # at top of the .info file.
  # Give below time to start, we append to the .info file it created
  if (open(OUT,">> $outdir/$capfile.info")) {
    dbg("Writing to $capfile.info: ".timestamp() . " tcpdump -l -n -n -i $intf ip CAPTURED: $line");
    print OUT "# ". timestamp() . " tcpdump -l -n -n -i $intf ip CAPTURED:\n".
      "$line\n";
  }
  close(OUT);

  # Start tcpdump. Odd: If we do not redirect stderr here, it ends up as first
  # line of the -w output file, which breaks it.

  # NOTE: exec a bit cleaner here. Code works either way, just have one
  # extra perl process per tcpdump out there with system. But with system,
  # we get to see the dbg of the unixdump ending if we care.
#  system("tcpdump -i $intf -U -s0 -w $outdir/$capfile host $newip 2>>$outdir/$capfile.info");
  exec("tcpdump -i $intf -U -s0 -w $outdir/$capfile host $newip 2>>$outdir/$capfile.info");
  dbg("Child unixdump for $newip on $intf dying");
  exit 0;
}

sub hostinit {
    # Some one-off things we want done per host, good place for it while
    # alwayspcap.pl lives on.
    # TODO: If we replace alwayspcap.pl, put this in scrubhands? mabye...
    unless (-f "/usr/local/sbin/linksfixed") {
        foreach my $targetfile ("/usr/lib/libreadline.so") {
            next unless (-f $targetfile or -l $targetfile);
            my $str = basename($targetfile);
            my @files = split(/\n/,`grep -l $str $opbin/*`);
            my $newlib = "";
            foreach my $file (@files) {
                ($newlib) = grep /$str.*not found/ , `ldd $file`;
                next unless $newlib;
                ($newlib) = $newlib =~ /^\s*(\S+)\s/;
                if ($newlib) {
                  `ln -sf $targetfile /usr/lib/$newlib`;
                  $created .= "  ln -sf $targetfile /usr/lib/$newlib\n";
                }
            }
        }
        writefile("/usr/local/sbin/linksfixed",scalar gmtime()."\n".
                  "By alwayspcap. Created these links:\n$created\n");
    }
}


sub myinit {
  my $gotutils=0;
  my $waitcount=1;
  while (1) {
    sleep 2 unless $waitcount < 2;
    # Loop up to 4min, if no autoutils by then we die
    foreach ("../etc/autoutils",
	     "/current/etc/autoutils",
	     "autoutils",
	     "NOTTHERE"
	    ) {
      if (-r $_) {
	require $_ or next;
	progprint("Sourcing $_",STDOUT)
	  if ($inlab and ! ("@ARGV" =~ /-\S*[hv]/i));
	$gotutils++;
	last;
      }
    }
    if ($gotutils) {
      sleep 3 unless $waitcount < 10;
      mywarn("Just read in autoutils after $waitcount x 2 seconds")
	unless length $ENV{RCLOCAL};
      dbg("Just read in autoutils after $waitcount x 2 seconds");
      last;
    }
    last if $waitcount++ > 120;
  }
  die("Could not find autoutils. Cannot run $0\n.")
    unless $gotutils;
  $| = 1;

  hostinit();

  $intf = $ENV{INTERFACE};
  $restart = 1 if $ENV{RESTART};
  $restart = 0 if $ENV{RESTART} eq "0";
  $thendie = $ENV{RESTART} =~ /die/i;
  $usagetextshort = setusagetext();

  mydie("bad option(s)") if (! Getopts( "hv" ) ) ;
  usage() if ($opt_h or $opt_v) ;
  mydie("INTERFACE is not set") unless $intf or $thendie;
  $intf_info = `ifconfig $intf 2>/dev/null`;
  mydie("Invalid INTERFACE=$intf")
    unless $intf or $thendie;
  dbg("Got restart=$restart thendie=$thendie intf=$intf intf_info=$intf_info=");

  # This is my master file, we only write it if we are master
  # after removing all other master files first who will then
  # know to die off.
  $masterfile = "$outdir/alwayspcap.master.$$";
  # Check if we are only or RESTART instance
  my @otherpids = progalreadyrunning();
  if (@otherpids) {
    dbg("progalreadyrunning=(@otherpids)");
    unless($restart) {
      # If already running and RESTART= not set, we just exit
      dbg("mydying quietly, $prog[@otherpids] already running");
      mydie("dying quietly, $prog[@otherpids] already running");
      exit 1 ;
      dbg("NOT dying quietly TESTING ONLY");
    } else {
      `rm -f $outdir/alwayspcap.master*`;
      my $s = "s" if @otherpids > 1;
      my $perlpid = $otherpids[0];
      mywarn("Killing other instance$s of ${prog}[@otherpids] to start anew")
	unless length $ENV{RCLOCAL};
      dbg("ps -ef | egrep \"unixdump|perl|pcap\"\n".`ps -ef | egrep "unixdump|perl|pcap" | grep -v grep`);
      # Must kill tcpdumps run by @otherpids, sleep a bit, then if
      # still there we kill @otherpids, then we can continue
      # or if $thendie we just die not starting any new stuff
      # ($thendie should be used in debugging only)
      my @psoutput = `ps -efwwww | grep -v grep | egrep -v "root [ ]*$$"`;
      my $toomany=0;
      while (1) {
	foreach (@psoutput) {
	  # Look here for only tcpdumps writing to unixdump,
	  # not the shells that spawned them.
	  next unless  / (\d+) .*tcpdump .*-w.*unixdump.* host ([\d\.]*)/;
	  my ($pid,$ip) = ($1,$2);
	  my $exe = `ls -l /proc/$pid/exe 2>/dev/null`;
	  $exe =~ s/.* \-\> //g;
	  next unless $exe =~ m,tcpdump,;
	  dbg("Killing pid=$pid on ip=$ip exe=$exe: $_");
	  kill(TERM,$pid);
	}
	$toomany++;
	@otherpids = progalreadyrunning();
	dbg("In infinite otherpids loop (@otherpids)");
	dbg("ps shows\n".`ps -ef |egrep "perl|tcpdu"`);
	last unless @otherpids;
	kill(TERM,@otherpids) if @otherpids;
	sleep 1;
	dbg("AFTER kill otherpids=(@otherpids) SHOULD EVENTUALLY BE EMPTY")
	  if @otherpids;
	last if $toomany > 55;
      }
      mydie("VERY BAD: other $prog instances are still running even though this one just sent kill(TERM,@otherpids)")
	if @otherpids;
    }
  }
  @otherpids = ("none") unless @otherpids;
  if ($thendie) {
    dbg("Exiting after killing other instances if any");
    mydie("Exiting after killing other instances if any");
  }

  # Now we touch $masterfile as we are it
  mydie("BAD CANNOT WRITE TO MY MASTERFILE") unless open(OUT,">$masterfile");
  print OUT "$$\n";
  close(OUT);

  # fork/exit so parent returns immediately
  fork and exit 0;

  # All prints from now on via dbg() only to dammit file
  close(STDOUT);
  close(STDERR);
  close(STDIN);

  # Set a few more things then continue
  ($ourip) = $intf_info =~ /\sinet addr:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s/;
}

sub progalreadyrunning {
  # ps grep out us print just pids
  my @hits = split(/\n/,
    `ps -efwwww | grep -v grep | grep "$prog" | egrep -v "root [ ]*$$" | awk '{print \$2}'`);
  return @hits;
#  return map { $_ =~ s/^\s*\S+\s+(\d+).*/\1/ },@hits;
}

sub catch_zap {
  dbg("caught TERM, stopping capture on $intf to $capfile");
  close(TCPDUMP);
  if ($capfile) {
#    sleep 5;
  }
#  exit 0;
} # end sub catch_zap

sub setusagetext {
  return "
Usage: $prog [-h|-v]

OPTIONS: -h and -v show help and version, respectively.

With no options, and INTERFACE set to a valid interface, $prog
will daemonize and then run and parse a tcpdump on that interface.
(Unless another copy of $prog is running already, in which case
it exits quietly.) If the interface goes down, $prog will try
every few seconds to start again. So $prog can and will ALWAYS
run on the op box. Anytime the interface goes down or the tcpdump is
killed, the child process that started it will exit.

For every IP from which our INTERFACE receives traffic, a separate
tcpdump -w will be run in a child process collecting all raw data
from that IP. At the end of your op, getopdata will rename all of
these files to:

   $outfile.SRCIP__OURIP.IP.TIMESTAMP.HOSTNAME.pcap

where SRCIP generated the traffic to our OURIP and IP.HOSTNAME is
the (first) PITCHIMPAIR host in opnotes.txt. (So it will only be put
in ONE pitchimpair's directory, not several if we switch pitches.)

The data files written to will be in $outdir and
initially called $outfile.SRCIP__OURIP.TIMESTAMP. Whatever
/current points to is where the capture files will be generated
(i.e., always in /current/down).

It first checks in /proc for another instance of $prog, and
does nothing if one is already running. Or set the RESTART= variable,
and $prog will first kill the running instance and all its
tcpdump children, then start a fresh instance. This will stop all
previous capture files (potentially in an old /current after scrubhands
was just run), allowing the new instance to start fresh files in the
new /current/down. scrubhands runs \"RESTART=yes $prog\" every
time it starts a new session.

";
}
