#!/bin/env python

# N+1.x.x.x is the Python version of the N.y.y.y Perl script, if any
VER="2.0.0.1" 

import sys,os

sys.path = ["/current/tmp"] + sys.path
sys.path = ["/current/etc"] + sys.path


if os.path.isfile("/current/etc/autoutils.py"):
    from autoutils import *
else:
    print "Could not import autoutils.py"
    exit()

if not nopenenv:
    die('%s must be run in a NOPEN window' % prog)


if re.search('Linux 2\.4',nopen_serverinfo):
    print COLOR_FAILURE + '\n\n\n# NOPEN on Linux 2.4 cannot run -ifconfig\n\n'
else:
    #autosocket = pilotstart(quiet)

    #print 'TODO: must still write doit() to do this:doit("\\-ifconfig")'
    doit("\\-ifconfig")
   


'''
#!/usr/bin/env perl 
##
$VER="1.0.0.1";

$| = 1 ;
($scriptcount, $functioncount) = ();
myinit() ;

if ($nopen_serverinfo =~ /linux 2.4/i
#TESTING:     or $nopen_serverinfo =~ /Linux 2.6.18-194.el5PAE \#1 SMP Tue Mar 16 22:00:21 EDT 2010 i686/i
    ) {
    progprint($COLOR_FAILURE."\n\n\n # NOPEN $serverver cannot run -ifconfig on:\n\n".
	      $COLOR_NORMAL.
	      " $nopen_serverinfo, try:\n\n      ifconfig -a");
} else {
    my ($output) = doit("\\-ifconfig");
    if ($ifconfig_outfile) {
	if ($ifconfig_append) {
	    writefile("APPEND",$ifconfig_outfile,$output);
	} else {
	    writefile($ifconfig_outfile,$output);
	}
    }
}


# Called via do so must end with 1;
1;

sub myinit {
  # If $willautoport is already defined, we must have been called
  # by another script via require. We do not re-do autoport stuff.
  $calledviarequire = 0 unless $calledviarequire;
  $stoiccmd = "called as: -gs ifconfig @ARGV";
  if ($willautoport and $autosocket) {
    $stoiccmd = "in $prog, called as: ifconfig(@ARGV)";
    dbg("via require autoifconfig ARGV=(
".join("\n",@ARGV)."
) prog=$prog");
#    progprint("$prog called -gs ifconfig @ARGV");
    $calledviarequire = 1;
  } else {
    $prog = "-gs ifconfig";
    $willautoport=1;
    my $autoutils = "../etc/autoutils" ;
    unless (-e $autoutils) {
      $autoutils = "/current/etc/autoutils" ;
    }
    require $autoutils;
    $vertext = "$prog version $VER\n" ;
  }
  clearallopts();
  $vertext = "$prog version $VER\n" ;
  mydie("No user servicable parts inside.\n".
	"(I.e., noclient calls $prog, not you.)\n".
	"$vertext") unless ($nopen_rhostname and $nopen_mylog and
			    -e $nopen_mylog);

  my $origoptions = "@ARGV";
  mydie("bad option(s)") if (! Getopts( "hvaf:" ) ) ;

  $ifconfig_outfile = $opt_f;
  $ifconfig_append = $opt_a;
  
  ###########################################################################
  # Set strings used in usage before calling it
  ###########################################################################



  ###########################################################################
  # PROCESS ARGUMENTS
  ###########################################################################


  usage() if ($opt_h or $opt_v);


  # Connect to autoport, we need status and more interactively.
  # If $autosocket is already defined, we must have been called
  # by another script via require. We do not re-do autoport stuff.
  $autosocket = pilotstart(quiet) unless $autosocket;

  ## ERROR CHECKING OF OPTS

}

sub setusagetexts {
  # Separate long usage strings as separate function
  $usagetext="
Usage: $prog [-h]                       (prints this usage statement)

NOT CALLED DIRECTLY

$prog is run from within a NOPEN session when \"$prog\" or
\"=ifconfig\" is used.

";
  my $newname = $opt_N unless ($opt_N =~ /[\/\s]/);
  $newname = "NEWNAME" unless $newname;

  $gsusagetext="
Usage:  $prog [INTERFACE]

$prog is a wrapper to the NOPEN builtin -ifconfig. If you are on any
Linux 2.4 kernel, $prog will refuse to run -ifconfig for you, otherwise
it does.

OPTIONS

  -f FILE   Save output to file
  -a        Append when saving to file

Usage:  $prog [INTERFACE]

";
}#setusagetexts
'''
