#!/usr/bin/env perl
# $Id: scripme.pl,v 1.19 2006/03/17 18:22:23 ident Exp $
use File::Basename;
require "getopts.pl";
use FileHandle ;
use IPC::Open2 ;
#version:
$VER="2.0.1.2" ;
# ===============
$prog = basename ${0};
$otherprog = $prog ;
$otherprog =~ s/.pl$//;
$SIG{INT} = \&my_exit;
$SIG{TERM} = \&my_exit;
$SIG{HUP} = \&my_exit;
$rand = $ENV{RAND} ;
$opdir = "/current" ;
$opbin = "$opdir/bin" ;
$opetc = "$opdir/etc" ;
$opdown = "$opdir/down" ;

$usagetext = "
Usage: $prog [-hcVd]

   -h  print this usage statement

   -c  call \$EXPLOIT_SCRIPME via \"sh -c '$EXPLOIT_SCRIPME'\" (this
       is ignored unless -t EXPLOIT is used with $otherprog)

   -V  show all commands executed to stdout

   -d  show but do not execute the commands

$prog scripts the current window to $opdown/script.\$\$.
$prog is normally called by \"$otherprog\".  See:

$otherprog -h

$prog version $VER
";
usage("bad option(s)") if (! Getopts( "hvVDdck" ) );
&usage if ($opt_h);
if ($opt_v) {
  print "$prog version $VER\n";
  exit;
}
$shminusc = $opt_c ;
$killwindow = $opt_k ;

require "$opetc/scripme.default.$rand"
  if (-r "$opetc/scripme.default.$rand") ;

require "$opetc/scripme.override"
  if (-r "$opetc/scripme.override") ;

# If this one exists, it has correct exploit entry only
# and the user provided his own .override file which
# we don't trust to have a good exploit

require "$opetc/scripme.exploit.$rand"
  if (-r "$opetc/scripme.exploit.$rand") ;

$debug = "-d" if ($opt_d or $opt_D or "$ENV{DEBUG}") ;

$what = $ENV{WINTYPE} ;
$what = "SCRIPT" if ($what > 0 and $what < 20) ;
# set our pwd
if ($what eq "TCPDUMP") {
  chdir ("$opdown") || die "Cannot cd $opdown" ;
} elsif ($what eq "OPSCRIPT") {
  chdir ("$opetc") || die "Cannot cd $opbin" ;
} else {
  chdir ("$opbin") || die "Cannot cd $opbin" ;
}
## our preferred path beginning
#$PATH =
  #"../bin:$opbin:/usr/local/sbin:/usr/local/bin:/bin:/usr/bin:/sbin:/usr/sbin:." ;
#foreach (split (/:/,$PATH) ) {
  #$PATH{$_}++ ;
#}
## tack on anything that had been in PATH before
## after our preferred path unless we already had it
#foreach (split (/:/,$ENV{"PATH"}) ) {
  #$PATH .= ":$_" unless $PATH{$_} ;
#}
# These are our preferences that will be added to 
# ENV (environment for our program and anything we
# call) in the loop to follow
$display = ":0" ;
$display = $ENV{DISPLAY} if ( $ENV{DISPLAY} =~ /:/ ) ;
%environment = (PS1,"\\t \\h \\w> ",
		DISPLAY,"$display",
		#PATH,"$PATH",
);
# set our ENV
print "Setting Environment Variables: \n";
foreach (sort keys %environment) {
  $ENV{$_} = $environment{$_} ;
  print "\t$_=\"$ENV{$_}\"\n";
}
print "\n";

$colornorm = "\033[0;39m";
$colorfail = "\033[1;31m";
$colorwarn = "\033[1;33m";
$colornote = "\033[0;34m";
$colorgren = "\033[1;32m";
foreach ("EXPLOIT","UPGRADE") {
  $autorun{$_} = $_ ;
}

if ($what eq "TCPDUMP" or $autorun{$what} eq $what or $what eq "OPSCRIPT" ) {
  if ($what eq "TCPDUMP") {
    open (CMDIN , "sh -c '$xtermcommands{$what}' |") ||
      die "Could not open \"sh -c '$xtermcommands{$what}' |\"" ;
    $cmdinopen++ ;
    $outfile = "$opdown/tcpdump.raw" ;
    $ext = "" ;
    $ext++ while (-e "$outfile$ext" ) ;
    $outfile = "$outfile$ext" ;
    open (CMDSCRIPT, ">> $outfile") ||
      die "Could not open \">> $outfile\"" ;
    binmode(CMDIN) ;
    binmode(CMDSCRIPT) ;
    $cmdscriptopen =  $outfile ;
    select CMDSCRIPT ;
    $| = 1; # unbuffered output
    select STDOUT ;
    $| = 1; # unbuffered output
    script_tag("started");
    my $tmpline = `date; pwd; uname -a; netstat -rn ; ifconfig -a` ;
    printboth($tmpline) ;
    while ($line =<CMDIN>) {
      printboth("$line") ;
    }
    # how'd we get here? Maybe someone killed the tcpdump but not the perl?
    # anyway, the &my_exit below will log the "done" line via script_tag
  } elsif ($what eq "OPSCRIPT") {
    my $clear = "\n"x80 ;
    while (1) {
      system("$xtermcommands{$what}") ;
      while (1) {
	print "$colorwarn$clear$what editor terminated.\n\n";
	print "Type \"again\" to bring it up again. Or
just ${colorfail}IGNORE$colorwarn OR$colorfail KILL$colorwarn this window. (${colornote}ALT-F4$colorwarn kills)\n\n";
	while (<>) {
	  last if (/again/i);
	}
	last if (/again/i) ;
      }
      print "\n$colornorm\n";
    }
  } elsif ($autorun{$what} eq $what ) {
    $open2mode++ ;
    if ($shminusc) {
      $taskpid = open2( \*Reader, \*Writer, "sh -c '$xtermcommands{$what}' 2>&1") ;
    } else {
      $taskpid = open2( \*Reader, \*Writer, "$xtermcommands{$what} 2>&1") ;
    }
    binmode(Reader) ;    select Reader ;    $| = 1; # unbuffered output
    binmode(Writer) ;    select Writer ;    $| = 1; # unbuffered output
    $cmdinopen++ ;
    my $lcwhat = lc $what ;
    $outfile = "$opdown/script.$lcwhat.$$" ;
    if ($ENV{"OUTFILE"}) {
      $outfile = "$opdown/$ENV{OUTFILE}.$$" ;
    }
    $ext = "" ;
    $ext++ while (-e "$outfile$ext" ) ;
    $outfile = "$outfile$ext" ;
    open (CMDSCRIPT, ">> $outfile") ||
      die "Could not open \">> $outfile\"" ;
    binmode(CMDSCRIPT) ;
    $cmdscriptopen =  $outfile ;
    select CMDSCRIPT ; $| = 1; # unbuffered output
    select STDIN ;     $| = 1; # unbuffered output
    select STDERR ;    $| = 1; # unbuffered output
    select STDOUT ;    $| = 1; # unbuffered output
    my $tmpline = `date; pwd; uname -a; netstat -rn ; ifconfig -a` ;
    script_tag("started");
    printboth($tmpline) ;
    printboth("$colorwarn
NOTE: Your input may appear here twice (if echoed back--e.g., passwords only once).$colornorm\n") ;
    $forking = 1 ;
    $kidpid = fork ;
    if (! $kidpid) { # child
      $ppid = getppid ;
      $prog = "[$$] (child of $ppid)" ;
      sleep 1 ;
      $| = 1;			# unbuffered output
      while () {
	$lengthread = read(Reader,$readbuf,1) ;
	#    print "DBG: read $lengthread\n";
	last if ($lengthread == 0) ;
	printboth ($readbuf) ;
      }
      printboth ("$colornote
${prog}: EOF from task running \"$xtermcommands{$what}\".
${prog}: Sending SIG TERM to parent and exiting.${colornorm}\n");
      kill(TERM,$ppid) ;
    } else { # parent
      $prog = "[$$](parent of $kidpid)" ;
      printboth ("
[$$] Parent  (task's input)
[$kidpid] Child   (task's output)
[$taskpid] Task ($xtermcommands{$what})
");
      $| = 1;			# unbuffered output
      while () {
        my $gotnull = 0 ;
	$lengthread = read(STDIN,$readbuf,1) ;
        #TODO: ^D not working still want to ignore it
	if ($lengthread == 0) {
          $gotnull++ ;
          printboth ("${colornote}$prog: Ignoring EOF from STDIN\n") unless $gotnull;
        } else {
          $gotnull = 0 ;
	  printboth($readbuf,"Writer") ;
        }
      }
      printboth ("${colorfail}${prog}: SHOULD NEVER SEE THIS\n");
    }
  }
} elsif ($what eq "SCRIPT") {
  $outfile = "$opdown/script.$$" ;
  $ext = "" ;
  $ext++ while (-e "$outfile$ext" ) ;
  $outfile = "$outfile$ext" ;
  $cmdscriptopen =  $outfile ;
  $xtermcommands{$what} .= ".$$" ;
  $xtermcommands{$what} .= "$ext" if ($ext);
  # now run $what's commands
  system("$xtermcommands{$what}");
} elsif ($what =~ /^UNSCRIPTED/ ) {
  system("$xtermcommands{$what}");
} else {
  die "UNRECOGNIZED TYPE $what" ;
}
my_exit("done") ;

sub my_exit {
  my $signame = shift;
  my $kidstuff = "" ;
#  if ($kidpid) {
#    $kidstuff .= "(parent of $kidpid) " ;
#  }
  if ($signame) {
    printboth("\n${colorfail}${prog}: RECEIVED SIG $signame${colornorm}\n");
    exit if ($signame eq "HUP" and ($what eq "OPSCRIPT")) ;
    exit if ($killwindow and $signame eq "done");
  }
  # if we've forked and this is parent, die quietly--child does rest
  if ($forking) {
    if ($signame eq "INT" and $open2mode) {
      if ($kidpid) {
	printboth("${prog}: Sending INT to task[$taskpid] running \"$xtermcommands{$what}\"\n");
#	print Writer "\003" ; # parent does this
	sleep 1 ;
	kill(2,$taskpid) ;
      } else {
	printboth("${prog}: Ignoring INT (sent to task)\n") ;
      }
      return; # both return from INT's
    }
    if ($kidpid) {
      printboth("Parent $$ waiting on $kidpid then exiting after SIG $signame\n");
      waitpid($kidpid,NULL) ;
    } else {
      printboth("Child $$ exiting (ppid=$ppid) after SIG $signame");
      exit ;
    }
  }
  # This is parent--child died if any
  # before we close, try to kill the tcpdump if that's the case
  if ($what eq "TCPDUMP") {
#    print `killall tcpdump 2>&1` ;
    # thought that would get the "## packets seen..." lines tcpdump
    # gives out at end, but it doesn't. Doing a kill of that pid
    # elsewhere does, tho. Hmph.
  }
  return if ( ($what eq "OPSCRIPT") or ($what =~ /^UNSCRIPTED/) ) ;
  close (CMDIN) ;
  close (Reader) ;
  close (Writer) ;
  script_tag("done") ;
  if ($ENV{AFTERNOTE} and -r $ENV{AFTERNOTE}) {
    printboth("\n${colorwarn}====================================================\n");
    my $output = `cat $ENV{AFTERNOTE}` ;
    if ((! $forking or ($forking and $kidpid)) and (! $what =~ /PACKRAT/)) {
      unlink("$ENV{AFTERNOTE}") ;
    }
    printboth("\n${colornote}$output${colornorm}\n");
    printboth("\n${colorwarn}====================================================$colornorm\n");
  }

  close (CMDSCRIPT) ;
  print "${colornorm}See $cmdscriptopen for output\n
$what IS DONE.\n";
  if ($killwindow) {
    print "Window closing in 3...\n\a";
    sleep 1;
    print "2...\n\a";
    sleep 1;
    print "1...\n\a";
    sleep 1;
    exit ;
  } else {
    print "\n\nTo re-script this window, paste in:

cd /current/down ; script -af $cmdscriptopen


ANOTHER ^D KILLS THIS WINDOW\n\n\n";
    exec("/bin/bash --rcfile /etc/bashrc-u") ;
  }
} # end sub my_exit

sub script_tag {
  my ($which) = (@_) ;
  printboth ("\nScript $which on ".`date`."\n\n") ;
  if ($which eq "started") {
    printboth( "Running $what via\n
$xtermcommands{$what}\n\n");
    if ($ENV{NOPENJACK}) {
      unlink("$opetc/nocallbackprompt");
      printboth("Called via -jackpop:
=========
  RA=$ENV{RA}
  RP=$ENV{RP}
  TA=$ENV{TA}
  TP=$ENV{TP}
  CMD=$ENV{CMD}
=========
") ;
    }
  }
} # end sub script_tag

sub usage() {
  print "\nFATAL ERROR: @_\n" if ( @_ );
  print $usagetext;
  print "\nFATAL ERROR: @_\n" if ( @_ );
  exit;
} # end sub usage

sub printboth() {
  my ($output,$channel) = (@_) ;
  
  print CMDSCRIPT "$output" ;
  print STDOUT "$output" unless $channel;
  print Writer "$output" if ($channel eq "Writer") ;
} # end sub printboth
