#!/bin/env perl
$VER="1.0.0.1";
myinit();

my $ans = popalarm($content,$delaysecs);
mydie("popalarm($content,$delaysecs);

Invalid DELAY ($ans): -d $opt_d")
  unless ($ans > 0);

printf("\n\n".
       scalar gmtime().
       "Alarm will go off in $delaystr, showing this content:\n".
       "=====================================================\n".
       $content."\n".
       "=====================================================\n".
       "");


sub myinit {
  use File::Basename ;

  $prog = basename($0);

  my $autoutils = "../etc/autoutils" ;
  foreach $autoutils ("../etc/autoutils",
		      "/current/etc/autoutils",
		      "./autoutils",
		      dirname($0)."/autoutils",
		     ) {
    last if (-f $autoutils);
  }
  require $autoutils;

  mydie("bad option(s)") if (! Getopts( "hvc:d:" ) );

  usage() if ($opt_h or !$opt_c or !$opt_d);

  if (-s $opt_c) {
    $content = readfile($opt_c);
    mydie("$opt_c does not contain any content:\n\n".
	  `ls -al $opt_c`)
      unless (length $content);
  } else {
    $content = $opt_c;
  }

  $delaysecs = strtoseconds($opt_d);
  $delaystr  = secstostr($delaysecs);
  mydie("Invalid DELAY -d $opt_d")
    unless ($delaysecs > 0);
}

sub setusagetexts {
  $usagetext="
Usage: $prog

$prog forks and backgrounds itself, waiting for its timer to expire. When
the timer expires, $prog pops up an xterm displaying the alarm content.

OPTIONS:

  -h/-v         Show usage/version
  -d DELAY      Delay before alarm will fire, in [#d][#h][#m]#[s] format
  -c CONTENT    Content of alarm - can be a string on the command line, or
                a file containing the desired content.

Usage: $prog

";
}
