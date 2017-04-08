#!/usr/bin/env perl
#
# This parses $nopen_mylog in a while loop called OUTSIDE.
# Each if {} block in this loop is independent of others and can be placed
# in any order. Order of output is dependent upon /current/etc/autodone.
#
$VER="1.10.0.6" ;
#use Encode;
#use encoding "ascii";
use File::Basename ;
my $gotutils=0;
my $path = dirname($0);


$dbgcount=0;
foreach ("",
#	 "/tmp/etc/autoutils",
	 "/current/etc/autoutils",
	 "$path/autoutils",
	) {
  if (-w $_) {
    $gotutils++;
#    do $_ ;
    require $_ ;
    last;
  }
}
$opdir = "." unless (-d $opdir);
unless ($gotutils) {
  $prog = basename $0 ;
  $vertext = "$prog version $VER\n" ;
  require Time::Local;
  require "getopts.pl";
  unless ($opt_C) {
    $COLOR_SUCCESS="\033[1;32m";
    $COLOR_FAILURE="\033[1;31m";
    $COLOR_WARNING="\033[1;33m";
    $COLOR_NORMAL="\033[0;39m";
    $COLOR_NOTE="\033[0;34m";
  }
  $opdir = "/current";
  $opup = "$opdir/up" ;
  $opbin = "$opdir/bin" ;
  $opetc = "$opdir/etc" ;
  $opdown = "$opdir/down" ;
  $optmp = "$opdir/tmp" ;

  $nopen_mylog = $ENV{NOPEN_MYLOG} ;
  $nopen_mypid = $ENV{NOPEN_MYPID} ;
  $nopen_rhostname = $ENV{NOPEN_RHOSTNAME} ;
  ($nopen_hostonly) = $nopen_rhostname =~ /(.*)\.\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/ ;
  ($nopen_myip) = $nopen_rhostname =~ /(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$/ ;
  $nopen_server_os = $ENV{NOPEN_SERVERINFO} ;
  ($nopen_ip) = $nopen_rhostname =~ /\.(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/ ;
}
$usagetext = setusagetext();
usage("bad option(s)") if (! Getopts( "vhl:f:p:asCB" ) ) ;
$beep = "\a";
$beep = "" if $opt_B;

if ($opt_C) {
  $COLOR_SUCCESS="";
  $COLOR_FAILURE="";
  $COLOR_WARNING="";
  $COLOR_NORMAL="";
  $COLOR_NOTE="";
}
$opdown = "." unless (-d $opdown);
$path = "$opdown/cmdout" ;
$path = "./" unless (-d $path);
usage() if $opt_h or $opt_v;
%mons=("Jan","01","Feb","02","Mar","03","Apr","04","May","05","Jun","06","Jul","07","Aug","08","Sep","09","Oct","10","Nov","11","Dec","12");

mymydie("Cannot use -l and -s together") if ($opt_l and $opt_s) ;
#mymydie("Cannot use ANY options with a list of targets") if (($opt_l or $opt_s) and @ARGV) ;
$statusnotdone = 1;
$gotrpcoutput = 0 ;
$logfile = $opt_l ;
$doall = $opt_a ;
$findit = $opt_s ;
$saveoutputto = $opt_f ;
$autodoneruns=0;
$path = $opt_p if ($opt_p and -d $opt_p);
# Some globals
$globaltarget = "" ;
$latewarnings = "" ;
my $nopenafter = "";
mymydie("Cannot read path $path\n") unless (-x $path and -r _) ;
@targets = @ARGV ;
mymywarn("Throwing away \"@targets\" parameters because of -a") if (@targets and $doall) ;
@targets = ("-1") unless @targets ;
if ($doall) {
  @targets = () ;
  # Note: The grep -v here is I think no longer needed?
  foreach (split (/\n/,
#    `grep -rl "DONE running $opetc/autone" $path/* 2>/dev/null | grep -v autodone`)) {
    `grep -rl "DONE running $opetc/autone" $path/* 2>/dev/null`)) {
    s/.*\/([^\/]*)-\d{4}-\d{2}-\d{2}-\d{2}:\d{2}:\d{2}.*/$1/ ;
    push(@targets,$_) ;
  }
  mymydie("No autodone output found recursively in $path") unless (@targets);
}
dbg("got nopen_mylog=$nopen_mylog=
findit=$findit=
targets=(@targets)");
TARGET: while (@targets) {
  %donethisoffset = () ;
  $target = shift(@targets) ;
  unless ($target eq "-1") {
    (@logs) = split (/\n/,
		   `find $path/ -type f 2>/dev/null | grep "$target.*:??" | grep -v "scans.*$target"`) ;
    my %logs = () ;
    foreach (@logs) {
      s/-\d{4}-\d{2}-\d{2}-\d{2}:\d{2}:\d{2}.*// ;
      $logs{"$_"}++ unless (/-find$/ or /replay/) ;
    }
    my (@tmp) = (keys %logs) ;
    dbg("got tmp=(\n".join("\n",@logs)."\n)");
    if (! @tmp) {
      my $more = ", trying next..." if (@targets) ;
      mymywarn("Target not found with 'find $path/ -type f 2>/dev/null | grep \"$target.*:??\"'$more");
      next TARGET ;
    }
    if (@tmp > 1) {
      mymywarn("More than one match. The -t target \"$target\" must be unique");
      foreach (keys %logs) {
	mymywarn("$_");
      }
      next TARGET ;
    }
    my (@tmp) = (keys %logs) ;
    ($nopen_rhostname) = $tmp[0] =~ /([^\/]*)$/  ;
    next unless $nopen_mylog = findit() ;
    ($nopen_ip) = $nopen_mylog =~ /\.(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/ ;
  } # else proceed with the $nopen vars in env
  if ($nopen_rhostname_with_slashes) {
    foreach my $movefile
      ("$optmp/.crondates.",
       "$opdown/linuxstats.cmdout.",
       "$opdown/solarisstats.cmdout.",
       "$opdown/utc_offset.",
       "$optargetcommands/${nopen_rhostname}_date-rfc2822.",
       "$opdown/mkoffset.",
      ) {
	$newfile = "$movefile$nopen_rhostname";
	$movefile .= $nopen_rhostname_with_slashes;
	next unless -f $movefile;
	preservefile($newfile);
	rename($movefile,$newfile);
      }
  }
  if ($findit) {
    $nopen_mylog = findit() ;
  }
  if ($logfile) {
    $nopen_mylog = $logfile ;
    mymydie("No such file: $logfile") unless (-e $logfile) ;
    mymydie("Cannot read file: $logfile") unless (-r _ ) ;
    $nopen_rhostname = "" ;
  }
dbg("got nopen_mylog=$nopen_mylog=");
  mymydie("No NOPEN_MYLOG environment var") unless $nopen_mylog ;
  unless ($nopen_rhostname) {
    # so we got MYLOG but not RHOSTNAME--so find it
    (@lines) = split (/\n/,`head -20 $nopen_mylog | grep "^\\\[.*\\\]\\\[.*\\\]\$"`);
    foreach (@lines) {
      last if (($nopen_rhostname) = /\[.*\]\[.* -> ([^:]*):/) ;
    }
    mymydie("Could not find \$nopen_rhostname in $logfile") unless $nopen_rhostname;
    # Does this one actually have autodone in it?
    chomp($autodoneruns = `grep -c "BEGIN running .*auto.* on $nopen_rhostname" "$nopen_mylog"`);
    unless ($autodoneruns) {
      @logs = () ;
      $nopen_mylog = findit();
      unless ($nopen_mylog) {
	mymywarn("Could not find autodone in $logfile.
Also could not find it in these other $nopen_rhostname logs in $path:");
	my $str = "" ;
	foreach (@logs) { $str .= "\t$_\n" ; } ;
	mymydie("$str");
      }
    }
  } else {
    chomp($autodoneruns = `grep -c "BEGIN running .*auto.* on $nopen_rhostname" "$nopen_mylog"`);
  dbg("0 autodoneruns=$autodoneruns= looking for BEGIN in nopen_mylog=$nopen_mylog=");
  }

  mymydie("Cannot read log file $nopen_mylog") unless (-r "$nopen_mylog") ;

  # assert: Both MYLOG and RHOSTNAME are defined now

  mymywarn("$prog parsing $nopen_mylog",$COLOR_NOTE) ;
  if ($saveoutputto) {
    print OUT ("$COLOR_NOTE$prog parsing $nopen_mylog
   saving output in $saveoutputto.$nopen_rhostname$COLOR_NORMAL") ;
  }
  unless (open(IN,"< $nopen_mylog")) {
    mymywarn ("Cannot open $nopen_mylog for read");
    next TARGET ;
  }
  # Skip to the most recent autodonerun if more than one
  my $linecount=0;
  print ("Multiple runs of autodone found ($autodoneruns)...skipping to last one.\n")
    if ($autodoneruns > 1);
  dbg("autodoneruns=$autodoneruns= looking for BEGIN");
  while ($autodoneruns >= 1 and !(eof IN)) {
    $linecount++;
    $_=<IN>;
    $autodoneruns-- if (/DONE running .*auto.* on $nopen_rhostname/);
    $autodoneruns-- if (/AUTONEWDONE IS NOT FINISHED/);
    $autodoneruns-- if (/BEGIN running .*auto.* on $nopen_rhostname/);
    last if ($autodoneruns <= 1 and /BEGIN running .*auto.* on $nopen_rhostname/);
  }
  dbg("autodoneruns=$autodoneruns= Found BEGIN at line $linecount of ".`wc -l "$nopen_mylog"`);
  if ($saveoutputto) {
    if (open(OUT, "> $saveoutputto.$nopen_rhostname")) {
      select (OUT) ;
      print OUT ("$COLOR_NOTE$prog parsing $nopen_mylog$COLOR_NORMAL\n") ;
      mymywarn("    saving output in $saveoutputto.$nopen_rhostname",$COLOR_NOTE) ;
    } else {
      mymywarn("Unable to save output to $saveoutputto.$nopen_rhostname.
Sending to STDOUT instead.") ;
      select (STDOUT) ;
    }
  }
  $found = 1 ;

  # If any SUCTIONCHAR pulled yet for this guy, we log there here too
  if (open(IN2,"$opdown/gotsuc.$nopen_rhostname")) {
    while (<IN2>) {
      print ;
    }
    close(IN2);
  }

  my $lcount=0;
  if (open(INEXTRA,"< $opetc/opscript.txt")) {
    my $ip,$tmpin ;
    while($tmpin = <INEXTRA>) {
#      next unless /^\#/ ; # only read comments
#      next if /\// ;# Skip working dir if seen
      ($val) = $tmpin =~ /[\#\s]+(\S+)/ ;
      if (ipcheck($val)) {
	$ip = $val if (ipcheck($val) and $nopen_rhostname =~ /$val$/) ;
#	print "yesip $nopen_rhostname " if ipcheck($val) ;
#print "DBG0: $val $ip $dnsname ++ $tmpin\n";
      } else {
	$dnsname = $val ;# unless length($val);
	#print "DBG1: $val $ip $dnsname ++ $tmpin\n";
      }
      last if ($lcount++ > 15 or ($ip and $dnsname)) ;
    }
    if ($ip and $dnsname) {
      print "IP: $ip\n";
      print "DNS name: $dnsname\n" ;
    }
  } else {
    mymywarn("Unable to open $opetc/opscript.txt for read");
  }
  close(INEXTRA);
  my $hwarch="";
  my %runalready=();
  my $procmeminfo=0;
  my $memprintlater = "";
  my $dfprint = "";
  my $uptimeprint = "";
  my $loadprint = "";
  my $hostnamesave = "";
  my $domainnamesave = "";

  dbg("HERE: autodoneruns=$autodoneruns=");

 OUTSIDE: while (! (eof IN)) {
    logerror($_)  if (!$found and $_) ;
    $found = 1 ;
    getline(undef,"FROM OUTSIDE: ") unless $gotone ;  $gotone = 0 ;
    #  ($line) =~ s/\033\[[0-3];\d\dm//g ;# get rid of color codes if there
    next unless ($_) = $line =~ /^\[(.*)\]$/ ;
    s/-nohist//;
    s/^\s*//;
#    last if (m+DONE running $opetc/autonext+) ;
    next if / GMT\]\[.*$nopen_rhostname\:[\d]+$/ ;
    # the hunt is on! might have some good stuff here
    $found = 0 ;		# We increment this only if good input found or no matches at all
    # Each of the following if blocks looks for the command it wants to parse.
    # When it finds one, inside the if is a while loop that parses that command's
    # output until it finds what it expects and/or the next command is found
    # (i.e., $gotone is true).
#    if (/-lsh.*mkoffset/) {
#dbg("Found THIS mkoffset:$_");
#      while (getline(undef,"FROM")) {
#dbg("gotone=$gotone Found THISline mkoffset:$line");
#	next OUTSIDE if $gotone ;
#	if ($line =~ /UTC_OFFSET=([\d-]+)/) {
#	  print "UTC Offset: $1\n" unless $donethisoffset{$1}++ ;
#	  $found++ ;
#	}
#      }
#    }
    if (/-getenv/) {
      while (getline(undef,"COMEONMANgetenv") and ! (eof IN)) {
	next OUTSIDE if $gotone ;
	print "System Path: $1\n" if $line =~ /^PATH=(.*)/;
	$found++ ;
      }
      next OUTSIDE ;
    }
    if (/hostid/) {
      getline(undef,"COMEONMANhostid") ;
      next OUTSIDE unless $line ;
      print "Host ID: $line\n";
      $found++ ;
      next OUTSIDE ;
    }
    if (!$hostnamesave and /hostname/ and ! m,(cat|more).* /etc/hostname, ) {
	while (1 and ! (eof IN)) {
	    getline(undef,"FROM hostname") ;
	    last if (!$line or $line !~ /:::::::::::::/);
	}
      next OUTSIDE unless ($line and $line !~ /hostname.*(command not found|no such file)/i);
      $hostnamesave = $line;
      $found++ ;
      next OUTSIDE ;
    }
#    if ( /hostname/) {
#	warn "DBG: Got hostnamesave=$hostnamesave= at _=$_= and line=$line=";
#	`echo "DBG: Got hostnamesave=$hostnamesave= at _=$_= and line=$line=" >> /tmp/dammit`;
#    }
    if (/domainname/) {
      # assert: hostname, then =autorpc, have both been done already
      # $hostnamesave has hostname output
      getline(undef,"COMEONMANdomainname") ;
      next OUTSIDE unless $line ;
      $domainnamesave = $line;
      my ($nopen_ip) = $nopen_rhostname =~ /(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/ ;

      my (@IP,%FQDN,%KEYSTR,%OS,%IMPLANTS,
	  %UTCOFFSET,%ALLIMPLANTKEYS,%IMPLANTKEYS) = () ;
#dbg("nopen_myip=$nopen_myip
#\$nopen_rhostname=$nopen_rhostname=
#\$nopen_ip=$nopen_ip=
#");

      if (findinvarkeys($nopen_ip,1,\@IP,\%FQDN,\%KEYSTR,\%OS,\%IMPLANTS,
				 \%UTCOFFSET,\%ALLIMPLANTKEYS,\%IMPLANTKEYS)
	 ) {
	if ($FQDN{$nopen_ip}) {
	  print "FQDN: $FQDN{$nopen_ip}\n";
	}
      }

      $found++ ;
      next OUTSIDE ;
    }
    if (/^-lsh date ; date -u/ or /^Our .*local\/GMT:/) {
#dbg("Inside here lsh date or Our.*GMT");
      my $count = 0 ;
      while (getline(undef,"COMEONMANlsh date") and ! (eof IN)) {
	next OUTSIDE if $gotone ;
	next unless $count++ ;	# skip date, want date -u
	($mon,$d,$year) = $line =~ /(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+.*\s(\d{4})/i ;
	($h,$m,$nothing,$s) = $line =~ /\s(\d{2}):(\d{2})(:(\d{2})){0,1}\s+/ ;
	($tz) = $line =~ /([\D]+)\s+$year/;
	$tz =~ s/^\s*(.*)\s*$/$1/;
	$d += 100 ; $d = substr($d,1) ;
	print "Access Start (zulu): $year-$mons{$mon}-$d $h:$m:$s\n";
	print "OP Box UTC Time Zone: $tz\n";
	$gmnow = Time::Local::timegm($s,$m,$h,$d,$mons{$mon}-1,$year);
	$found++ ;
	next OUTSIDE ;
      }
    }
#    if (/^date ; date -u/) {
#      while (getline(undef,"FROM")) {
#dbg("autodone/gethostinfo.pl processing date/date -u output:$line");
#	#next if ( $line =~ /^\[Saving\s+output to: \/current\/etc\/dates/ ) ;
#	#      next OUTSIDE if $gotone ;
#	next unless ($line =~ /(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+.*\s(\d{4})/i) ;
#my ($newway,$monstr,$mday,$hr,$min,$myyear) =epochseconds($line);
#dbg(" gethostinfo.pl target tzdate(newway,monstr,mday,hr,min,myyear) = ($newway,$monstr,$mday,$hr,$min,$myyear)");
#	($mon,$d,$year) = $line =~ /(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+.*\s(\d{4})/i ;
#	($h,$m,$nothing,$s) = $line =~ /\s(\d{2}):(\d{2})(:(\d{2})){0,1}\s+/ ;
#	# 20051027: Change this next from [\D]+ to [\S]{3,} for TZs like GMT+3
#	($tz) = $line =~ /\s([\S]{3,})\s+$year/;
#	$d += 100 ; $d = substr($d,1) ;
#	print "Box Time Zone: $tz\n";
#	my $tznow = Time::Local::timegm($s,$m,$h,$d,$mons{$mon}-1,$year);
#dbg("gmnow=$gmnow tznow=$tznow= Time::Local::timegm($s,$m,$h,$d,$mons{$mon}-1,$year);");
#	my $offset = int(($tznow - $gmnow) / 60 + 0.50 );
#	print "Box Offset: $offset\n";
#	my $offsethr = int(($offset / 60)) ;
#	$offset = -1 * $offset if ($offsethr < 0) ; # neg shown only in hr
#	my $offsetmin = int(0.50 + (($offset / 60) - int($offset / 60))* 60) ;
#	print "Box Offset String: $offsethr hours $offsetmin minutes\n";
#	$found++ ;
#	next OUTSIDE ;
#      }
#    }
    if (/-lsh mv .*\.dates.*crondates.*Our.*local.*mkoffset/) {
#      dbg("FOUND mkoffset match: $_");
      my $boxutcoffset = "";
      while (getline(undef,"COMEONMANcrondates")  and ! (eof IN)) {
	my ($ourdate,$ourudate,$theirdate,$theirudate) = ();
	next OUTSIDE if $gotone ;
#	dbg("OUTER gotone=$gotone autodone/gethostinfo.pl processing -gs mkoffset output:$line");
	my $utcline = "";
	# Next line will be our date, one after that our date -u
	# But its output is not available here via getline(undef,"FROM"), instead we read
	# $opdown/mkoffset.$nopen_rhostname which has it all (gs.mkoffset just wrote it).
	if (open(OFFSETIN,"$opdown/mkoffset.$nopen_rhostname")) {
	  my $count=0;
	  my $opboxdate = "";
	  while ($line = <OFFSETIN>) {
	    if ($opboxdate) {
	      next unless $line =~ /UTC_OFFSET/;
	      ($boxutcoffset) = $line =~ /(UTC_OFFSET=[-\d]*)/;
	    }
#	    dbg("INNER:$line");
	    next unless $line =~ /(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+.*\s(\d{4})/i ;
	    $count++;
	    chomp($ourdate = $line) if ($count == 1);
	    chomp($ourudate = $line) if ($count == 2);
	    chomp($theirdate = $line) if ($count == 3);
	    chomp($theirudate = $line) if ($count == 4);
#	    dbg("INNER count=$count autodone/gethostinfo.pl processing -gs mkoffset output:$line
#so far:ourdate=$ourdate
#so far:ourudate=$ourudate
#so far:theirdate=$theirdate
#so far:theirudate=$theirudate
#");
	    # skip our date/date -u, target date then  want his date -u
	    next unless $count == 4 ;
	    # ASSERT: $line is now target's date -u
#	    dbg("INNER SETTLED ON $line");
	    $opboxdate = $line;
	  }
#dbg("out of INNER");
	  $line = $opboxdate;
	  close(OFFSETIN);
	  # ASSERT: OK, this $line is opbox date, $ourudate is opbox date -u.
	  ($mon,$d,$year) = $ourudate =~ /(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+.*\s(\d{4})/i ;
	  ($h,$m,$nothing,$s) = $ourudate =~ /\s(\d{2}):(\d{2})(:(\d{2})){0,1}\s+/ ;
	  ($tz) = $ourudate =~ /([\D]+)\s+$year/;
	  $tz =~ s/^\s*(.*)\s*$/$1/;
	  $d += 100 ; $d = substr($d,1) ;
	  print "Access Start (zulu): $year-$mons{$mon}-$d $h:$m:$s\n";
	  print "OP Box UTC Time Zone: $tz\n";
	  $gmnow = Time::Local::timegm($s,$m,$h,$d,$mons{$mon}-1,$year);
	  # ASSERT: OK, this $theirdate is target's "date" output
#dbg("Calling epochseconds($theirdate);",1);
	  my ($newway,$monstr,$mday,$hr,$min,$myyear) =epochseconds($theirdate);
#dbg("Just returned from 	  my ($newway,$monstr,$mday,$hr,$min,$myyear) =epochseconds($theirdate);");
	  ($mon,$d,$year) = $theirdate =~ /(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+.*\s(\d{4})/i ;
	  ($h,$m,$nothing,$s) = $theirdate =~ /\s(\d{2}):(\d{2})(:(\d{2})){0,1}\s+/ ;
	  # 20051027: Change this next from [\D]+ to [\S]{3,} for TZs like GMT+3
	  ($tz) = $theirdate =~ /\s([\S]{3,})\s+$year/;
	  ($utctz) = $theirudate =~ /\s([\S]{3,})\s+$year/;
	  $d = sprintf("%02d",$d) ;
	  print "Box Local Time: $theirdate\n";
	  print "Box UTC Time: $theirudate\n";
	  print "Box UTC_OFFSET: $boxutcoffset\n";
	  print "Box Time Zone: $tz\n";
	  print "Box UTC Time Zone: $utctz\n";
	  my $tznow = Time::Local::timegm($s,$m,$h,$d,$mons{$mon}-1,$year);
#	  dbg("gmnow=$gmnow tznow=$tznow= Time::Local::timegm($s,$m,$h,$d,$mons{$mon}-1,$year);");
	  my $offset = int(($tznow - $gmnow) / 60 + 0.50 ) unless $gmnow <= 0;
	  print "Box Offset: $offset\n";
	  my $offsethr = int(($offset / 60)) ;
	  $offset = -1 * $offset if ($offsethr < 0) ; # neg shown only in hr
	  my $offsetmin = int(0.50 + (($offset / 60) - int($offset / 60))* 60) ;
	  print "Box Offset String: $offsethr hours $offsetmin minutes\n";
	  $found++ ;
	}
	next OUTSIDE ;
      }
    }
    if (/(ssh(d{0,1})) -V/) {
      my ($sshbin,$daemon) = ($1,$2);
      $daemon = uc $daemon;
      while (getline(undef,"COMEONMANssh/sshd")) {
	next OUTSIDE if $gotone ;
	next if $line =~ /^\s*$/;
	next if $line =~ /^NO\!/;
	next if $line =~ /no such.*file/i;
	next if $line =~ /illegal/i;
	last if $line =~ /usage/i;
	last if $line =~ /option requires an argument.*V/i;
	last if $line =~ /No SSH binaries found/;
	print "SSH${daemon}_version: $line\n";
	$found++ ;
      }
    }
    if (/locale/) {
      while (getline(undef,"COMEONMANlocale")) {
	next OUTSIDE if $gotone ;
	if ($line =~ /^LANG=(.+)/) {
	  print "Box Language: $1\n" ;
	  $found++ ;
	}
	if ($line =~ /^LC_CTYPE=(.+)/) {
	  print "LC_CTYPE: $1\n" ;
	  $found++ ;
	}
      }
    }
    if (/^-ifconfig/) {
      my $header = "Hardware: Interface\n";
      while (getline(undef,"COMEONMAN-ifconfig")) {
	next OUTSIDE if $gotone ;
	($int,$flags,$mtu) = ($1,$2,$3) if
	  $line =~ /^(.*):\s+flags=(.+).*mtu ([\d.]+)/ ;
	next unless (
		     ($junk,$ip,$bc,$nm) =
		     $line =~ /^(inet|.*is 0.*) ([\d.]+) broadcast ([\d.]+) netmask ([\d.]+)/
		    ) ;
        next if ($ip eq "0.0.0.0" or $ip eq "6.3.6.0") ;
	if ($ip eq "127.0.0.1") {
	  ($int,$flags,$mtu,$ip,$bc,$nm) = () ;
	  next ;
	}
	print "${header}Instance: $int; FLAGS: $flags; MTU: $mtu\n" ;
	$header = "" ;
	getline(undef,"FROM") ;
	if (($mac) =  $line =~ /^ether ([abcdef\d:]+)/i) {
	  # nopen -ifconfig does not pad one digit to two, so we do
	  $mac =~ s/([a-f0-9]+)/0$1/g ; # this makes some three digits
	  $mac =~ s/0([a-f0-9]{2})/$1/g ; # this makes all 3 digits just two
	}
	my ($network) = `ipcalc --network --silent $ip $nm` =~ /NETWORK=(.*)/ ;
#	print "Instance: address: $ip subnet: $network/$nm broadcast: $bc\n";
#	print "Instance: MAC Addres: $mac\n" ;
	print "IP: $ip\nMAC Addres: $mac\nSubnet: $network/$nm\nBroadcast: $bc\n";
	($int,$flags,$mtu,$ip,$bc,$nm) = () ;
	$found++ ;
      }
    }   
#    if (/notgonnause--was-status/) {
#      my $count = 0 ;
#      while (getline(undef,"FROM")) {
#	next OUTSIDE if $gotone ;
#	next unless ( $line =~ / Remote Host:Port / ) ;
#	next unless $count++ ;	# get second match like above
#	($val,$val2) = $line =~ /([\d.]+):(\d+)\)$/ ; # get rid of color codes if there
#	print "IP: $val\n";
#	$targetip = $val ;
#	print "RAT port: $val2\n";
#	$found++ ;
#	next OUTSIDE ;
#      }
#    }
    if (/uname -a/) {
      getline(undef,"COMEONMANuname");
      $hwarch .= "HW Architecture: $line\n" unless $hwarch;
    }
    if (/-status/ and $statusnotdone) {
      my ($whichend,$othertools,$ratclientver,$ratserverver,$os,$remoteip,
	 $remoteport,$scriptfile,$lookfor,$skiplines,@tmp,$newlatewarning) = () ;
      while (getline(undef,"FROMstatus")) {
	$whichend = "local" if ($line =~ /^local/i)  ;
	$whichend = "remote" if ($line =~ /^remote/i)  ;
	$whichend = "connection" if ($line =~ /^connection/i)  ;
	next OUTSIDE if $gotone ;
	if ($whichend eq "remote") {
	  if ( ($os) = $line =~ / OS\s+(.*)/ ) {
	    print "OS: $os\n";
	    print "OS Version: $1\n" if $os =~ /[^\s]+\s+([^\s]+)\s/ ;
	    $hwarch .= "HW Architecture: $1\n" if ($os =~ /\s+([^\s]+)$/ and !$hwarch);
	  }
	  if ( $line =~ / NOPEN server\s+(.*)/ ) {
	    $ratserverver = $1 ;
	    print "RAT server ver: NOPEN $ratserverver\n";
	  }
	  print "RAT server cwd: $1\n" if ( $line =~ / CWD\s+(.*)/ );
	  $found++ ;
	}
	if ($whichend eq "connection") {
	  if ($line =~ /Remote Host:Port.*\(([\.\d]+):(\d+)\)/) {
	    $remoteip = $1 if $1 ;
	    $remoteport = $2 if $2 ;
	  }
	}
	if ($whichend eq "local") {
	  $lookfor = $line if ($line =~ /Command Out/) ;
	  if ($line =~ / NOPEN client\s+(.*)/ ) {
	    $ratclientver = $1;
	    print "RAT client ver: NOPEN $ratclientver\n";
	    $found++ ;
	  }
	}
	if ($remoteip and $remoteport and $ratclientver and 
	    $ratserverver and !$othertools) {
	  $statusnotdone=0;
	  my $clientdiff = "" ;
	  my $ratserververshort = $ratserverver ;
	  $ratserververshort =~ s/(\d+\.\d+\.\d+)\.*\d+.*/\1/ ;
	  my $ratclientvershort = $ratclientver ;
	  $ratclientvershort =~ s/(\d+\.\d+\.\d+)\.*\d+/\1/ ;
	  if ($ratserververshort eq $ratclientvershort) {
	    if ($ratserverver =~ s/version mismatch/server--acceptable version mismatch/g) {
#	      $ratserverver =~ s/([\d\.]+)/$1 \(server\)/;
	      $clientdiff = "\nTool Comments: $ratclientver (client)".
		"\nTool Comments: $ratserverver";
	    }
	  } else {
	    $clientdiff = "\nTool Comments: mismatched client $ratclientver" ;
	  }
	  $globaltools .= "--\nTool: NOPEN V3.X\nVersion: $ratclientver$clientdiff\n".
	    "Usage: EXERCISED\nUsage: ACCESSED\nTool Status: Successful\n".
	      "Implant IP: $remoteip\nImplant port: $remoteport\n";
	  $othertools++ ; # do this if block only once
	  if (-s "$opdown/ls_etc-ct.$nopen_rhostname") {
	    if (open(IN3,"< $opetc/.ls-ct.$nopen_rhostname")) {
	      my ($mon,$d,$h,$m,$year);
	      while (chomp($line3 = <IN3>)) {
		$line3 =~ s/\r//g ; # Get rid of ^M's
		next unless (($mon,$d,$h,$m,,$year) = $line3 =~
			     /(\S{3})\s+(\d+)\s+(\d+):(\d+) (\d+) \//) ;
		$d += 100 ; $d = substr($d,1) ;
		print "OS Installation Time: $year-$mons{$mon}-$d $h:$m:00\n";
		last;
	      }
	      close(IN3);
	    }
	  }
	  # Now look for other tools accessed before NOPEN
	  # Find the script.* file with us in it
	  chomp($scriptfile = `grep -l "$lookfor" $opdown/script* 2>/dev/null| head -1`) ;
	  unless ("$scriptfile" and open(IN2,"< $scriptfile")) {
	    my $str ="\nCannot open \"script -af\" file containing $nopen_mylog.\nIS THIS AN UNSCRIPTED WINDOW?" ;
	    mymywarn ($str) ;
	    $latewarnings .= "$str\n" ;
	    next ;
	  }
	  # If we're not first NOPEN target in there, skip others before
	  # looking for ish.
	  # make sure to get the right one? Multi-hops?
	  my ($gotish,$gotenv,$gottelnet,$version,@c,$tool,$toolextra,$prevline2) ;
	  my $notthere = 1 ;
	  while (chomp($line2 = <IN2>)) {
#next if ($line2 =~ /DBG.*keys=.*tn.spayed/ );
	    if ( $line2 =~ /keys=.*_(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s.*tn.spayed/ ) {
	      $prevline2 = $line2;
	      if ( $1 eq $nopen_ip ) {
		chomp($line2 = <IN2>) ;
		if (! ($line2 =~ /(call returned|We found)/) ) {
		  $notthere=0; # we are just before ish for our guy
		} else {
		  $notthere=1; # next ish is someone else
		}
	      } else {
		$notthere=1;
	      }
	    }
	    next if $notthere;
	    my $badcr;
	    while ($badcr = chop($line2)) {
	      last unless ($badcr eq "\r") ;
	    }
	    $line2 = $line2.$badcr ;
	    if ($line2 =~ /TARG_AYT.*=\s+(\S+)\s+(\S+)\s+(\S+)/) {
	      if ($1 and $2 and $3) {
		@c = ($1,$2,$3) ;#@c always has most recent TARG_AYT
	      }
	    }
	    $gotish=1 if ($line2 =~ /running: ish /) ;
	    next unless $gotish ;
	    if ( $line2 =~ /^(\d+)\,\d+$/ ) {
	      $toolextra .= " PID=$1" ;
	    }
	    if ( $line2 =~ /PF=(.*)$/ and ! ($line2 =~ /Tool Comments:/) ) {
	      if ($1) {
		$toolextra .= " PF=$1 " unless ($toolextra =~ / PF=$1 /);
		$newlatewarning .= "\n--\nPOTENTIAL INCISION ERROR ON $nopen_rhostname: ".
		  "PF=$1\n";
	      }
	    }
	    if ( $line2 =~ /^VERSION=(.*)$/ ) {
	      if ($version) {
		if ($1 and ! $version eq $1) {
		  $newlatewarning .= "\nDifferent version numbers for IN on $nopen_ip: $version and $1--How can that be?\n" ;
		}
	      } else {
		$version = $1 ;
	      }
	    }
	  }
	  if ($version and @c) {
	    $globaltools .= "--\nTool: INCISION\nVersion: $version\n".
	      "Usage: ACCESSED\nTool Status: Successful\n".
		"Key: @c\n";
	    $globaltools .= "Tool Comments: $toolextra\n" if $toolextra;
	    ($version,@c) = () ;
	    $notthere=1 ; # VERSION is last entry of this ish
	    $gotish=0;
	  }
	  if ($newlatewarning) {
	    $latewarnings .= $newlatewarning . "VERSION=$version\n";
	  }
	  close(IN2);
	}
      }#while (getline(undef,"FROM"))
    }#if (/-status/)
    if (/^-w$/) {
      my $gotusers = 0;
      while (getline(undef,"FROM-w")) {
        my $ut = "";
	my $usernum = 0;
	next OUTSIDE if $gotone ;
	next if $line =~ /^USER.*/;
	next OUTSIDE if $line =~ /^NO!.*/;
        $found++;
	
	$ut = $1 if $line =~ /^Uptime:\s(.*)$/;
	if ($ut and !$uptimeprint) {
	  $uptimeprint = $ut;
	  next;
	}
	else {
	  $gotusers++;
	}
	if ($gotusers and !($line eq "") and ($line !~ /^Uptime/)) {
	  print "Active User: $line\n";
	  $latewarnings .= "\nActive User: $line\n";
	}
      }
    }
    if (/^uptime/ or /^w$/) {
      my $gotusers = 0;
      while (getline(undef,"FROMuptime")) {
        my $ut = "";
	my $userline = "";
	my $usernum = 0;
	next OUTSIDE if $gotone ;
	
	($ut,$userline,$loadprint) = ($1,$2,$3)
	  if $line =~ /^\s+\S{5,9}\s+(up \d+ \S+,\s+\S+),(\s+\d+\susers?),\s+(load averages?:.*)$/;
	$usernum = $1 if $userline =~ /\s*(\d+).*/;
	$gotusers++ if $usernum;
	
	if ($ut and !$uptimeprint) {
	  $uptimeprint = $ut;
	  next;
	}
	else {
	  $gotusers++;
	}
	if ($gotusers and !($line eq "") and ($line !~ /(^USER|^NO!|load average)/i)) {
	  $found++;
	  print "Active User: $line\n";
	  $latewarnings .= "\nActive User: $line\n";
	}
      }
    }
#    if (/^w$/) {
#      my $gotusers = 0 ;
#      while (getline(undef,"FROM")) {
#	my $ut = "";
#	my $usernum = 0;
#	next OUTSIDE if $gotone ;
#	next if $line =~ /^(USER|NO!).*/;
#	($ut,$loadprint) = ($1,$2) if ($line =~ /(.*)(load average.*)/i);
#	$ut = $line if (!$ut and !$uptimeprint and $line =~ /(uptime| up )/i);
#	$ut =~ s/uptime:\s*//gi;
#	$ut =~ s/.* up /up /i;
#	$usernum =~ /\s+(\d+)\s+users*/i;
#	$ut =~ s/\s+\d+users*//i;
#	if ($ut) {
#	  $uptimeprint = $ut;
#	  $found++ ;
#	  next ;
#	}
#	if ($gotusers and !($line eq "")) {
#	  print "Active User: $line\n";
#	  $latewarnings .= "\nActive User: $line\n";
#	}
#	$gotusers++ if $line =~ /^USER/ and $usernum ;
#      }
#    }
    if (/^last | egrep.*boot/) {
      while (getline(undef,"COMEONMANlast grep boot")) {
	next OUTSIDE if $gotone ;
	next unless ($line =~ /^reboot/ or $line =~ /system boot/ ) ;
	chomp($year = `date +\%Y`) unless $year ;
	if (($day,$mon,$d,$h,$m) = $line =~ 
	    /(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\w{3}) ([ \d]{2}) (\d{2}):(\d{2})/) {
	  $d += 100 ; $d = substr($d,1) ;
	  print "Last reboot: $year-$mons{$mon}-$d $h:$m:00\n";
	  $found++ ;
	  next OUTSIDE ;
	}
      }
    }
    if (/-ls.*wtmp(x?)/) {
      # Open the $opdown/last.$nopen_rhostname and get the reboot info from there.
      next OUTSIDE if ($gotlastoutput);
      chomp(my $file = `ls -rt $optargetcommands/*last* | grep "${nopen_rhostname}" | tail -1`);
      if (open(IN2,"< $file")) {
      	$found++ ;
        while (chomp($line2 = <IN2>)) {
	  next unless ($line2 =~ /^reboot/ or $line2 =~ /system boot/ ) ;
	  chomp($year = `date +\%Y`) unless $year ;
	  if (($day,$mon,$d,$h,$m) = $line2 =~ 
	      /(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\w{3}) ([ \d]{2}) (\d{2}):(\d{2})/) {
	    $d += 100 ; $d = substr($d,1) ;
	    print "Last reboot: $year-$mons{$mon}-$d $h:$m:00\n";
	    $gotlastoutput++ ;
	    last ;
	  }
        }
        close(IN2);
      } else {
	mymywarn("Unable to open $file",$COLOR_WARNING) ;
      }
      next OUTSIDE ;
    }
    if (/^netstat -[antpu]+/) {
      chomp(my $file = `ls -rt $optargetcommands/*netstat* | grep "${nopen_rhostname}" | tail -1`);
      if (open(IN2,"< $file")) {
	my $mode = "" ;
	my %udp = () ;
	my %tcp = () ;
	my $udp = "" ;
	my $tcp = "" ;
	while (chomp($line2 = <IN2>)) {
	  $line2 =~ s/\r//g ; # Get rid of ^M's
	  $mode = uc $1 if ($line2 =~ /^(UDP|TCP)/i)  ;
	  next unless (($duh,$port,$what) = $line2 =~ /(0.0.0.0:|\*\.)(\d+).*\s+(\w+)/) ;
	  if ($mode eq "UDP") {
	    $udp{$port}++;
	  } else { #"TCP"
	    $tcp{$port}++;
	  }
	}
	close(IN2) ;
	$udp .= "$_," foreach (sort by_num keys %udp) ;
	$tcp .= "$_," foreach (sort by_num keys %tcp) ;
	chop($udp);
	chop($tcp);
	print "UDP ports listening: $udp\n" if $udp;
	print "TCP ports listening: $tcp\n" if $tcp;
	$found++ if ($udp or $tcp);
      } else {
	mymywarn("Unable to open $file\n",$COLOR_WARNING) ;
      }
      next OUTSIDE ;
    }
    if (/^rpcinfo.*/ or /^-scan brpc 127.0.0.1/) {
      # only do this output once even if both ways done (builtin and not)
      next OUTSIDE if ($gotrpcoutput) ;
      chomp(my $file = `ls -rt $optargetcommands/*rpcinfo* | grep "${nopen_rhostname}" | tail -1`);
      if (open(IN2,"< $file")) {
	my %vers = () ;
	my %detail = () ;
	my %owner = () ;
	my %prog = () ;
	my %host = () ;
	my $longrpc = 0 ;
	my $shortrpc = 0 ;
	my $portrpc = 0 ;
	while (chomp($line2 = <IN2>)) {
	  $line2 =~ s/\r//g ; # Get rid of ^M's
	  # This next skips extraneous stuff from -scan brpc
	  next if ($line2 =~ /^\#/ or
		   $line2 =~ /^Packet from/ or
		   $line2 =~ /^UDP packet received from/ or
		   $line2 =~ /^cleaning up/ or
		   $line2 =~ /^(local|remote) client closed/ or
		   $line2 =~ /^Should be synced up/ or
		   $line2 =~ /^adios/ or
		   $line2 =~ /^--/) ;
	  # for when "rpcinfo" fails and we get usage, we skip this line
	  next if ($line2 =~ /( rpcinfo|Usage)/) ;
	  my ($prog,$ver,$proto,$port,$netid,$address,$service,$owner) = () ;
	  $line2 =~ s/^\s*// ;
	  if ($line2 =~ /\sowner\s*$/) {
	    $shortrpc=0 ; $longrpc=1 ; next;
	    $gotrpcoutput++ ;
	  }
	  ;
	  if ($line2 =~ /\s(port|service)\s*$/) {
	    $gotrpcoutput++ ;
	    $shortrpc=1 ; $longrpc=0 ; next;
	  }
	  if ($longrpc) {
	    if (($prog,$ver,$netid,$address,@service) =  split(/\s+/,$line2)) {
	      $owner = pop(@service) ;
	      $service = "@service" ;
	      $prog{$prog}++ ;
	      if ($address =~ s/([a-z]*)\.[a-z]+$/$1/i) {
		$host{$prog} = "$1/$host{$prog}" unless ($host{$prog} =~ /^$1\//) ;
	      }
	      $owner{$prog} .= "/$owner" unless ($owner{$prog} =~ /\/$owner/) ;
	      $vers{$prog} .= "/$ver" unless ($vers{$prog} =~ /\/$ver($|\/)/);
	      if ($service eq "-") {
		my @tmp = split(/\s+/,`grep $prog $opbin/rpc 2>/dev/null`) ;
		$service = $tmp[0] if ($tmp[0]) ;
	      }
	      $detail{$prog} .= "/$service" unless ($donedetail{$service} =~ /\/$prog/) ;
	      $donedetail{$service} .= "/$prog" ;
	    }
	  } elsif ($shortrpc) {		# short then
	    if (($prog,$ver,$proto,$port,$service) =  split(/\s+/,$line2)) {
	      $prog{$prog}++ ;
	      $detail{$prog} .= "/$service" unless ($detail{$prog} =~ /\/$service/) ;
	      $detail{$prog} .= "/$proto$port" unless($detail{$prog} =~ /\/$proto$port/) ;
	      $vers{$prog} .= "/$ver" unless ($vers{$prog} =~ /\/$ver($|\/)/);
	    }
	  }
	}
	close(IN2) ;
	if (%prog) {
	  $found++ ;
	  print "RPC Programs: " ;
	  $bshostname = "" ;
	  foreach (keys %prog) {
	    $bshostname = "$bshostname/$host{$_}" unless ($bshostname =~ /(^|\/)$host{$_}($|\/)/) ;
	    print "\n$_" ;
	    foreach $t ($vers{$_},$detail{$_},$owner{$_},$host{$_}) {
	      $t =~ s/^\/+//g ;
	      $t =~ s/\/+$//g ;
	      print "\t$t" ;
	    }
	    $bshostname =~ s/^\/*// ;
	  }
	  print "\n" ;
	  chop($bshostname) ;
	  print "Hostname BS: $bshostname\n" if $bshostname ;
	}
      } else {
	mymywarn("Unable to open $file",$COLOR_WARNING) ;
      }
      next OUTSIDE ;
    }
    # A little different for this. We are parsing the -cmdout saved
    # into linuxstats.cmdout.$nopen_rhostname which is NO LONGER CATTED
    # into the mainline cmdout. Doing so causes the NOPEN autport to
    # break very badly.
    if ( m, .*linuxstats.cmdout,) {
      # Open the linuxstats.cmdout and do our getline(undef,"FROM") against that fp.
      open(LINUXSTATS, "< $opdown/linuxstats.cmdout.$nopen_rhostname") or die "Can't open linuxstats.cmdout.$nopen_rhostname: $!";
      getline(LINUXSTATS,"COMEONMANLINUXSTATS before while") ;  $gotone = 0 ;
      my ($inmeminfo,$memoryoutput,$swapoutput,
	  $totalmem,$freemem,$memwarned,$swapwarned,
	  $totalswap,$freeswap)=();
      while (getline(LINUXSTATS,"COMEONMANLINUXSTATS WHILE LINE")) {
	next unless ($inmeminfo or $line =~ /::::::::/);
	getline(LINUXSTATS,"COMEONMANLINUXSTATS top of while") if ($line =~ /::::::::/);
	$inmeminfo=2 if ($line =~ ?^/proc/meminfo?);
	next unless $inmeminfo ;
	$line =~ s/\s//g;
	$procmeminfo = 1;
	# This $inmeminfo is 1 at top of meminfo, 0 at bottom
	$inmeminfo-- if ($line =~ /^::::::::/ or
			 $line =~ /^\[/ or
			 $line =~ /^\s*$/);
	last if ($inmeminfo <= 0);
	$totalmem = $1 if ($line =~ /mem.*total.*:(.+)/i or
			   $line =~ /total.*mem.*:(.+)/i);
	$freemem = $1 if ($line =~ /mem.*free.*:(.+)/i or
			  $line =~ /free.*mem.*:(.+)/i or
			  $line =~ /mem.*avail.*:(.+)/i or
			  $line =~ /avail.*mem.*:(.+)/i);
	$totalswap = $1 if ($line =~ /swap.*total:(.+)/i or
			    $line =~ /total.*swap:(.+)/i);
	$freeswap = $1 if ($line =~ /swap.*free:(.+)/i or
			   $line =~ /free.*swap:(.+)/i);
	if ($freemem and $totalmem) {
	  my ($usedpct,$usedstr) = freespace($freemem,$totalmem);
	  if ($usedpct >= 90 and !$memwarned) {
	    $memwarned++;
	    my $str = "Memory almost FULL! $freemem/$totalmem$usedstr\n";
	    mymywarn($str);
	    $latewarnings .= $str;
	  }
	  $memoryoutput = "RAM available: $freemem/$totalmem$usedstr\n";
	}
	if ($freeswap and $totalswap) {
	  my ($usedpct,$usedstr) = freespace($freeswap,$totalswap);
	  if ($usedpct >= 90 and !$swapwarned) {
	    $swapwarned++;
	    my $str = "Swap almost FULL! $freeswap/$totalswap$usedstr\n";
	    mymywarn($str);
	    $latewarnings .= $str;
	  }
	  $swapoutput = "Swap available: $freeswap/$totalswap$usedstr\n";
	}
      }
      $found++ if ($memoryoutput or $swapoutput);
      print $memoryoutput if ($memoryoutput);
      print $swapoutput if ($swapoutput);
      #WHICH??????? BUG? 15 JUN2012 TODO
      #next OUTSIDE;
      next ;
    }
    if (?(cat|more).* /proc/cpuinfo?) {	# Linux
      my ($cpu,$c,$id,$vendorid,$speed,$bmips) = () ;
      my @cpu = () ;
      while (getline(LINUXSTATS,"COMEONMANLINUXSTATS cat/more.*proc/cpu")) {
	if ( $gotone ) {
	  if ($cpu) {
	    $cpu =~ s/[, ]*$// ;
	    push(@cpu,$cpu) ;
	    $cpu = "";
	  }
	  if (my $num = @cpu) {
	    print "Number of Processors: $num\n" if (@cpu);
	    $found++ ;
	    foreach $cpu (@cpu) {
	      ($c,$id,$vendorid,$speed,$bmips) = $cpu =~
		/^\#(\d+)\s+((\S+)\s+.*)\s+([\.\d]+)MHz\s+bogomips=([\.\d]+)/ ;
	      print "Processor: $cpu\n";
	      print "CPU $c Speed: $speed\n" if (length($speed)) ;
	      print "CPU $c Identifier: $id\n" if (length($id)) ;
	      print "CPU $c VendorIdentifier: $vendorid\n" if (length($vendorid)) ;
	      print "CPU $c Bogomips: $bmips\n" if (length($bmips)) ;
	    }
	  }
          #WHICH??????? BUG? 15 JUN2012 TODO
          #next OUTSIDE;
	  next ;
	}
	$line =~ s/\s+:\s+/=/ ;
	$line =~ s/^\s*//;
	if ($cpu and ($line =~ /processor=(.+)/ or 
		      $line =~ /cpu=(.+)/)) {
	  $cpu =~ s/[, ]*$// ;
	  push(@cpu,$cpu) ;
	  $cpu = "";
	}
	$cpu .= "#$1 " if ($line =~ /processor=(.+)/ or 
			   $line =~ /cpu=(.+)/);
	$cpu .= "$1MHz " if ($line =~ /cpu MHz=(.+)/);
	$cpu .= "$1 " if ($line =~ /vendor_id=(.+)/);
	$cpu .= "$1 " if ($line =~ /model name=(.+)/);
	#      $cpu .= "flags=\"$1\" " if ($line =~ /flags=(.+)/);
	$cpu .= "bogomips=$1 " if ($line =~ /bogomips=(.+)/i);
	$cpu .= "prom$1=$2 " if ($line =~ /prom(.*)=(.+)/i);
      }
      close(LINUXSTATS);
    } #m, .*linuxstats.cmdout,
    if (/psrinfo -v/) { # Solaris
      my ($cpu,$c,$vendorid,$speed,$fpproc,$gotcpu,$cputype) = () ;
      my @cpu = () ;
      while (getline(undef,"FROMpsrinfo")) {
#	dbg("In psrinfo -v: gotone=$gotone line=$line=

#cpu=$cpu=

#cpu=(\n".
#	    join("\n",@cpu)."
#)

#");
	last if $gotone ;
	if (($cputype,$gotcpu) = $line =~ /Status of (\S*)\s*processor (\S+)/) {
	  if ($cpu) {
	    $cpu =~ s/[, ]*$// ;
	    push(@cpu,$cpu) ;
	  }
	  $cputype .= " " if length $cputype;
	  $cpu = "#$gotcpu $cputype";
	}
	#	$cpu .= "#$1 " if ($line =~ /Status of.* processor (\S+)/) ;
	$cpu .= "up since $1 " if ($line =~ /since (.*)\./) ;
	$cpu .= "$1 " if ($line =~ /(sparc\S*) processor/i) ;
	$cpu .= "$1 " if ($line =~ / (i.86) processor/i) ;
	$cpu .= "$1 " if ($line =~ /operates at (\d+\s*(\S*Hz))/i) ;
	$cpu .= "with $1 " if ($line =~ /and has an{0,1} (.* floating point processor)/i) ;
      }
      push(@cpu,$cpu) if $cpu;
      if (my $num = @cpu) {
	$found++ ;
	print "Number of Processors: $num\n" if (@cpu);
	foreach (@cpu) {
#	  dbg("Looking for vars in: ==$_==");
	  ($c) =
	    /^\#(\d+\S*)/;
	  ($vendorid,$speed) =
	    /(\S+)\s+([\.\d]+\s+\S*Hz)/ ;
	  ($fpproc) =
	    /with\s+(.*\S+)\s*/ ;
	  print "Processor: $cpu\n";
#	  dbg("

#got:  (\$c,\$vendorid,\$speed,\$fpproc) = 
#      ($c,$vendorid,$speed,$fpproc) = $cpu =~
#");
	  print "CPU $c Speed: $speed\n" if (length($speed)) ;
	  print "CPU $c VendorIdentifier: $vendorid\n" if (length($vendorid)) ;
	  print "CPU $c FP processor: $fpproc\n" if (length($fpproc)) ;
	}
      }
      next OUTSIDE ;
    }
    if ( ?^dmesg? ) {
      my $panic = "" ;
      my $totalmem = 0 ;
      my $availmem = 0 ;
      (my $t1,my $t2,my $t3,my $t4) = () ;
      chomp(my $file = `ls -rt $optargetcommands/*dmesg* | grep "${nopen_rhostname}" | tail -1`);
      if (open(IN2,"< $file")) {
        $found++;
	while (chomp($line2 = <IN2>)) {
#dbg("gethostinfo.pl in dmesg:$line2");
	  $line2 =~ s/\r//g ; # Get rid of ^M's
	  $panic .= "$line2\n" if ($line2 =~ /panic/) ;
	  #	($t1,$t2,$t3,$t4) = () ;
	  ($t1,$t2,$t3) = $line2 =~ /(avail.*){0,1}mem\s*[=]\s*(\d+)(K{0,1})/i ;
	  if (scalar $t2 > 0) {
#dbg("Found($t1,$t2,$t3) = $line2 =~ /(avail.*){0,1}mem\s*[=]\s*(\d+)(K{0,1})/i ;");
	    ($avail,$mem,$k) = ($t1,$t2,$t3) ;
	    $mem = $mem / 1024 unless ($k) ; # now in K
	    $mem = int(0.50 + 10 * $mem / 1024)/10 ; # now in M to one decimal
#dbg("0 mem=$mem avail=$avail availmem=$availmem totalmem=$totalmem");
	    $avail ? $availmem = $mem : $totalmem = $mem ;
#dbg("1 mem=$mem avail=$avail availmem=$availmem totalmem=$totalmem");
	  }
	  ($t1,$t2,$t3,$t4) = $line2 =~ /memory..(\d+)(k{0,1})\/(\d+)(k{0,1})/i ;
	  if (scalar $t1 > 0) {
	    $availmem = $t1 ; $k  = $t2 ;
	    $availmem = $availmem / 1024 unless ($k) ; # now in K
	    $availmem = int(0.50 + 10 * $availmem / 1024)/10 ; # now in M to one decimal
	  }
	  if (scalar $t3 > 0) {
	    $totalmem = $t3 ; $k2 = $t4 ;
	    $totalmem = $totalmem / 1024 unless ($k2) ; # now in K
	    $totalmem = int(0.50 + 10 * $totalmem / 1024)/10 ; # now in M to one decimal
	  }	
	}
	close(IN2) ;
	if ($availmem or $totalmem) {
	  if ($totalmem) {
	    $found++ ; # if we did find what we wanted
	    $memprintlater.="RAM: $totalmem MB\n";
	    if ($availmem) {
	      my $availpct = int(0.50 + 100 * 10 * ($availmem/$totalmem)) / 10 ;
	      my $usedpct = int(0.50 + 10*(100 - $availpct))/10 ;
	      $memprintlater.="RAM available: $availmem of $totalmem MB ($usedpct% used)";
	    }
	    $memprintlater.="\n" ;
	  } else { # must be only $availmem
	    $memprintlater="RAM available: $availmem of ??? MB\n" ;
	  }
	}
	if ($panic) {
	  mymywarn("PANICS IN dmesg OUTPUT!!") ;
	  sleep 1;
	  mymywarn("PANICS IN dmesg OUTPUT!!") ;
	  sleep 1;
	  mymywarn ("$panic") if $saveoutputto;
	  print ("${COLOR_FAILURE}\n${panic}${COLOR_NORMAL}\n");
	  sleep 1;
	}
      } else {
	mymywarn("Unable to open $file",
	       $COLOR_WARNING) ;
      }
      next OUTSIDE ;
    }
    if (/-(cksum|sha1sum)/) {
      $found++ ; # do not flag if no output
      # Look for hacked boxes in usual places
      my $hackdirregexp = "(libX\.a|share\/.aPa)" ;
      my $pscheckargs = "";
      while (getline(undef,"FROMcksum/sha1sum first")) {
	my ($hackedfile) = $line =~ /[\+-].* \d{4} (\/.*$hackdirregexp.*)/ ;
  	my ($sign,$file) = $line =~ /([\+-]).* \d{4} (\/.*)/ ;
	$hackedfile =~ s/\s*$// ;
	$file =~ s/\s*$// ;
	if ($sign and $hackedfile) {
	  my $str="DEFINITELY A HACKED BOX!! ";
	  my $lines="";
	  my $therest = "   Checksum for$COLOR_NOTE $file$COLOR_FAILURE matches:\n";
	  if ($sign eq "+") {
	    getline(undef,"FROMcksum/sha1sum") ;
	    $lines .= "$line\n" ;
	  } else {
	    $lines .= "$line\n" ;
	    $therest = "${COLOR_WARNING} But no match for checksum:$COLOR_FAILURE\n";
	  }
	  $str.="$therest$lines" ;
	  mymywarn($str);
	  $latewarnings .= "\n$str";
	  unless ($runalready{$hackedfile}++) {
	    $pscheckargs .= ",$hackedfile";
#	    $nopenafter .= "-lsh echo $hackedfile > $optmp/hacked.ps.$nopen_rhostname\n";
#	    $nopenafter .= "$hackedfile -h 2>&1 | grep \"ps \" >> L:$optmp/hacked.ps.$nopen_rhostname\n"; # is it ps?
#	    $nopenafter .= "$hackedfile -h 2>&1 | grep \"netstat \" >> L:$optmp/hacked.use.netstatcommand.$nopen_rhostname\n"; # is it netstat?
#	    $nopenafter .= "$hackedfile -h 2>&1 | grep \"netstat \" && $hackedfile -an >> L:$optmp/hacked.use.netstatcommand.$nopen_rhostname\n"; # is it netstat?
#	    $nopenafter .= "=pscheck";
	  }
	} elsif ($sign eq "-" and $file) {
	  my $file = $1 ;
	  $file =~ s/(\S*)\s*/$1/ ;
	  my $str="POSSIBLY Hacked? No matching checksum for $file\n";
	  $str .= "$line\n";
	  mymywarn($str);
	  $latewarnings .= "\n$str";
	}
	last if $gotone ;
      }
      if ($pscheckargs) {
	$pscheckargs =~ s/ /\\ /g;
	$pscheckargs =~ s/^,+//;
	$nopenafter .= "-gs pscheck -H$pscheckargs\n";
      }
      next OUTSIDE ;
    }
    if (/autodfcheck/) {
      $found++ ; # do not flag if no output
      # autodfcheck's output is not here--it is in $opdir/latewarnings if it has anything to say
      while (getline(undef,"FROMdfcheck")) {
	last if $gotone ;
      }
      next OUTSIDE ;
    }
    if (/^[-=]{0,1}df/) {
      my @disk = () ;
      my @tmp = () ;
      my $shortline = "" ;
      while (getline(undef,"FROMdf")) {
	if ($shortline) {
	  $line = "$shortline $line" ;
	  $shortline = "" ;
	}
	if ( $gotone = $line =~ /^\[(.*)\]$/ ) {
	  if (my $num = @disk) {
	    $found++ ;
	    # This will get the most recent =df output only
	    $dfprint = "Number of Hard Drives: $num\n" if (@disk);
	    foreach $disk (@disk) {
	      $dfprint .= "Hard Drive: $disk\n";
	    }
	  }
	  next OUTSIDE ;
	}
	@tmp = split (/\s+/,$line) ;
	if (@tmp == 1) {
	  $shortline = $line ;
	  next ;
	}
	($drv,$k,$u,$a,$c,$m) = @tmp;
	next unless ($drv =~ /^\//) ;
	#      push(@disk,"$drv on / $u/$k ($c)") ;
	push(@disk,$line);
      }
    }
    if (/-template/) {
      while (getline(undef,"FROMtemplate")) {
	next OUTSIDE if $gotone ;
	$found++ ; # if we did find what we wanted
      }
      # if no while loop here (one liners) make sure to do next OUTSIDE
    }
    # the lines with no if case above we don't care about
    $found++ ; 
  } # end OUTSIDE: while (! eof IN)
  close(IN);
  print $hwarch if $hwarch;
  $loadprint =~ s/load average:\s*//i;
  print "Load Average: $loadprint\n" if $loadprint;
  if ($uptimeprint) {
    print "Uptime string: $uptimeprint\n";
    my ($d) = $uptimeprint =~ /(\d+)\s+day/;
    my ($h,$m,$s) = $uptimeprint =~ /\s+(\d+):(\d+):(\d+)/;
    ($h,$m) = $uptimeprint =~ /\s+(\d+):(\d+)/ unless $s;
    if (length $h or length $m) {
      my $utmin = $d*24*60 + $h*60 + $m ;
      my $utsecs = $utmin*60 + $s;
      print "Uptime: $utmin\n";
      print "Uptime minutes: $utmin\n";
      print "Uptime seconds: $utsecs\n";
    }
  }
  print "Hostname: $hostnamesave\n" if $hostnamesave;
  if (!$domainnamesave) {
    ($domainnamesave) = $hostnamesave =~ /^[^\.]+\.(.+)/;
  }
  print "Domain: $domainnamesave\n" if $domainnamesave;
  print $dfprint;
  print $memprintlater if ($memprintlater and !$procmeminfo);
  print $globaltools if ($globaltools) ;
  close(OUT);
  select STDOUT ;
  if (@targets) {
    print "\n\n${COLOR_SUCCESS}Now looking for $targets[0]\n$COLOR_NORMAL\n";
  }
  my $output = "";
  foreach $targetwarningfile (
			      "$opdown/ethcheckout.txt.VMW*.$nopen_rhostname",
			      "$opdown/ethcheckout.txt.vmw*.$nopen_rhostname",
			      "$opdown/ethcheckout.txt.XEN*.$nopen_rhostname",
			      "$opdown/ethcheckout.txt.xen*.$nopen_rhostname",
			      "$opdir/latewarnings.$nopen_rhostname",
			     ) {
    next unless -s $targetwarningfile;
    chomp($output = `cat $targetwarningfile 2>/dev/null`) ;
    next unless $output;

    $output .= "\n\nThere were$COLOR_FAILURE ALERTS$COLOR_NORMAL: You must examine output above before you continue.\n\n";
    mypause("$beep\n${COLOR_FAILURE}$output");
  }
  unlink("$opdir/latewarnings.$nopen_rhostname") ;
} # end foreach $target (@targets)
if ($latewarnings) {
  print("$beep\n${COLOR_FAILURE}$latewarnings");
  sleep 1;
  print ("$beep$COLOR_NORMAL\n") ;
}

my $ext=$$;
if ($nopenafter) {
  foreach ("ps","netstat") {
    chomp(my $file = `ls -rt $optargetcommands/*${_}* | grep "${nopen_rhostname}" | tail -1`);
    if (-e $file) {
      my $new = $file;
      $new =~ s,_$_,_$_.hackedmaybe,g;
      preservefile($new);
      rename($file,$new);
      # USED TO BE: "$opdown/$_.$nopen_rhostname.hackedmaybe.$ext");
    }
  }
  if (open(OUT,"> $opetc/nopen_auto.$nopen_mypid.$ext")) {
    print OUT "#NOGS\n$nopenafter";
  }
  close(OUT);
  rename("$opetc/nopen_auto.$nopen_mypid.$ext","$opetc/nopen_auto.$nopen_mypid");
}


sub findit {
  # Finds and returns file in $path containing autodone output
  # Dies if single such file not found.
  mymydie("No NOPEN_RHOSTNAME environment var") unless $nopen_rhostname ;
  @logs = split (/\n/,
      `grep -l "BEGIN running .*auto.* on $nopen_rhostname" $path/"$nopen_rhostname_orig"*:??`) ;
dbg("In findit(@_) got logs=(@logs)");
  if (@logs > 1) {
    die "$COLOR_FAILURE
More than one log for $target has \"running $opetc/auto.*done.* on $nopen_rhostname\"--how can that be?
@logs$COLOR_NORMAL\n" ;
  }
  chomp($autodoneruns = `grep -c "BEGIN running .*auto.* on $nopen_rhostname" "$logs[0]"`);
dbg("Got autodoneruns=$autodoneruns returning $logs[0]");
  return $logs[0] ;
} # end sub findit

sub mymydie {
  die "\n${COLOR_FAILURE}$beep@_$COLOR_NORMAL\n" ;
}#mymydie

sub mymywarn {
  ($str,$color) = (@_) ;
  unless ($color) {
    $color = $COLOR_FAILURE ;
  }
  warn "${color}${beep}$str$COLOR_NORMAL\n" ;
}#mymywarn

sub logerror {
  (my $err) = @_ ;
  mymywarn("NO OUTPUT TO PARSE: $err",$COLOR_WARNING,1) ;
  print ERROUT "$err\n" 
    if open(ERROUT,">> $opdown/gethostinfo.err.$nopen_rhostname") ;
#  `echo "$err" >> $opdown/gethostinfo.err.$nopen_rhostname` 
#    if (-w "$opdown/gethostinfo.err.$nopen_rhostname");
  close(ERROUT);
}#logerror

sub getline {
  # globals changed: $line and $gotone
  # Sets $gotone true if we've hit the end of this command and
  # the beginning of the next.
  local ($where,$from) = (@_);
  $where = "IN" unless $where;
  chomp($line = <$where>) ;
  $linecount++;
#  dbg("in Getline From $from  In getline line=$linecount, from where=$where= got line=$line Got eof $where==".scalar eof $where);
  $line =~ s/\r//g ; # Get rid of ^M's
  $gotone = $line =~ /^\[(.*)\]$/ ;
  return ! (eof $where);
}#getline

sub freespace {
  local ($avail,$total) = (@_);
  ($avail) = $avail =~ /(\d+)/;
  ($total) = $total =~ /(\d+)/;
  if ($total and $avail and $total > 0) {
    my $availpct = int(0.50 + 100 * 10 * ($avail/$total)) / 10 ;
    my $usedpct = int(0.50 + 10*(100 - $availpct))/10 ;
    my $usedstr = " ($usedpct% used)";
    return ($usedpct,$usedstr);
  } else {
    return ();
  }
}#freespace

sub setusagetext {
  return "
Usage:  $prog [-h]                     (prints this usage statement)
        $prog [options] [ unique-IP-or-host1 unique-IP-or-host2 ... ]

$prog parses NOPEN's logs looking for the initial output from
\"autodone\", which is done exactly once per target (not once per NOPEN
session on that target). Then a summary of that information is put to
STDOUT in \"name: val\" format.

With no arguments, $prog processes the data according to the
environment variables NOPEN_MYLOG and NOPEN_RHOSTNAME.

With one or more arguments (after any options), $prog attempts
to find NOPEN logs files for a host that uniquely matches each argument
(partial match OK, so just the IP or even hostname might be sufficient),
then finds the one for that unique match that has autodone data and
processes it.

options:

-C        Disable color output.

-B        Disable beeps in output

-a        Show hostinfo output for EVERY host found to have autodone
          output in one of the files in $opdown/cmdout (or in the
          -p path).

-s        Find the right log file based on the environment variable
          \$nopen_rhostname. Usually run as \"-lsh gethostinfo.pl -s\"
          from a noclient session to your target from a window that did
          not run autodone (i.e., was not first noclient to target).

-l log    Uses the NOPEN logfile \"log\" (has to have autodone output).

-p path   Look for log files in \"path\" instead of $opdown/cmdout

-f file   Save output for each target for which autodone data is found
          to \"file.hostname.IPADDRESS\" (in your current directory).

"
}

## GRRR....here down should come from  autoutils?
__END__

sub fffffffdbg {
  my $sleep = 0;
  if ($_[$#_] =~ /^\d+$/) {
    $sleep = pop(@_);
  }
  dammit("$t ${prog}[$$]: ${COLOR_FAILURE}DBGwarn$beep: @_$COLOR_NORMAL") ;
  sleep $sleep if $sleep;
#    if ("@_" =~ /dammit/); #dbg
#  mywarn("${COLOR_FAILURE}DBGmywarn$beep: @_$COLOR_NORMAL") ; #dbg
}#dbg
sub dammit {
  my $duh = "@_";
  if (open(TMPOUT,">> $optmp/dammit")) {
    print TMPOUT "@_\n";
    close(TMPOUT);
  } else {
    `echo -e "$duh" >> $optmp/dammit`;
  }
}
sub findinvarkeys {
  local($target,        # Target we desire (IP/hostname)
	# Uppercase below are all references, @$IP is an array of IPs,
	# the rest are hashed arrays with those IPs as the keys.
	$IP,       # IPs that match
	$FQDN,     # FQDNs of each match
	$KEYSTR,   # KEYSTRs of each match
	$OS,       # OSs of each match
	           # (I.e. PROJECT___hostname.domainname___IP___YYYYMMDD--HHMMSS)
	$IMPLANTS, # IMPLANTs of each match, a space delimited string
	$exactonly,# If set, must match $target exactly.
       ) = (@_);
  my $match = 0 ; # Set to # of matches found
  my $wantip = $target =~ /^\d+\.\d+\.\d+\.\d+$/;
  my $wantname = !$wantip;
  # Looking in $opbin/varkeys/*
  # Given (maybe partial) hostname, return (list of) IP(s) that match
  # Given (maybe partial) IP, return (list of) FQDN(s) that match
  return 0 unless ($target and opendir(VARDIR,"$opbin/varkeys"));
  foreach $vardir (grep { ! /^\./ } sort readdir VARDIR) {
    next unless -d "$opbin/varkeys/$vardir" ;
    unless (opendir(PROJECTDIR,"$opbin/varkeys/$vardir")) {
      mywarn("autoutils::findinvarkeys: Cannot open $opbin/varkeys/$vardir");
      next;
    }
    foreach $t (grep { ! /^\./ } sort readdir PROJECTDIR) {
      next unless -d "$opbin/varkeys/$vardir/$t" ;
      next unless $t =~ /$target/;
      my ($fqdn,$ip) = $t =~ /^([^_]*)___([\d\.]+)/;
      if ($wantip) {
	next unless (!$exactonly or $ip eq $target);
      } else {
	next unless (!$exactonly or $fqdn eq $target);
      }
      push (@$IP,$ip);
      $$FQDN{$ip} = $fqdn;
      unless (opendir(TDIR,"$opbin/varkeys/$vardir/$t")) {
	mywarn("autoutils::findinvarkeys: Cannot open $opbin/varkeys/$vardir/$t");
	next;
      }
      $match++;
      foreach $implant (grep { ! /^\./ } sort readdir TDIR) {
	next unless -f "$opbin/varkeys/$vardir/$t/$implant"
	  and -r _ and -s _;
	next unless
	  open(VARIN,"$opbin/varkeys/$vardir/$t/$implant");
	$$IMPLANTS{$ip} .= " $opbin/varkeys/$vardir/$t/$implant";
	while (<VARIN>) {
	  if (my ($os) = /OS:\s*(\S+)/) {
	    $$OS{$ip} = $os unless $$OS{$ip};
	    if ($os ne $$OS{$ip}) {
	      mywarn("autoutils::findinvarkeys: Multiple different OS's for $ip in varkeys/");
	      $$OS{$ip} .= " $os" unless
		$$OS{$ip} =~ / $os/;
	    }
	  }
	}
      }
      $$IMPLANTS{$ip} =~ s/^ //;
      close(VARIN);
    }
  }
  closedir(DIR);
  return $match;
}#findinvarkeys
sub ipcheck {
  # returns 1 iff $ipstr is in dotted decimal notation with each 
  # octet between 0 and 255 inclusive (i.e. 0.0.0.0 and 255.255.255.255 are valid)
  my $maxval=255;
  my $minval=0;
  while ($_[$#_] =~ /no/) {
    if ($_[$#_] =~ /no255/) {
      pop(@_);
      $maxval=254;
    }
    if ($_[$#_] =~ /no0/) {
      pop(@_);
      $minval=1;
    }
  }
  local($ipstr,$minoctets,$maxoctets) = @_;
  $minoctets=abs(int($minoctets)) if defined $minoctets;
  $maxoctets=abs(int($maxoctets)) if defined $maxoctets;
  unless($minoctets) {
    $minoctets=4 ;
  }
  unless (defined $maxoctets and $maxoctets <= 4 and $maxoctets > 0) {
    $maxoctets=4;
  }
  # strip trailing "." if partial IPs allowed
  $ipstr =~ s/\.$// if ($maxoctets < 4) ;
  # need -1 in following split to keep null trailing fields (to reject "1.2.3.4.")
  my @octets=split(/\./,$ipstr,-1);
  return 0 if (@octets < $minoctets or @octets > $maxoctets);
  foreach (@octets) {
    # return 0 if (empty or nondigits or <0 or >$maxval)
    return 0 if (( /\D/ ) || $_ < $minval || $_ > $maxval);
    # next line allows partial IPs ending in ".", ignore last
    return 0 if ($minoctets == 4 and $_ eq "");
  }
  return 1;
} #ipcheck
sub by_num {
  return ($a <=> $b);
}#by_num
