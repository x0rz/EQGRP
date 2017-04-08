#!/usr/bin/env perl
# 
# date:   6 feb 2001
# revised 6 apr 2001
#
# see $opt_h if statment below for comments

require "getopts.pl";
&Getopts( "hd" );
$debug = $opt_d;

$timefield = 8;
$hrfield = $timefield + 1;
$minfield = $hrfield + 1;
$secfield = $minfield + 1;
$commandfield = 2;
$commands{"ls"} = $commands{"sh"} = $commands{"head"} = 1;

if ($opt_h) {
  print ("

# OK, this is still a major kludge.

# It looks in stdin for any three consecutive lines whose time 
# fields are within one second and whose three different commands
# are in the associative array $commands{xxx} with value 1.

# Those lines are marked as $notours{nn}.

# The input is saved off during the while(<>) loop line-by-line 
# as-is into $lines[nn]. After the input finishes, the lines in 
# the $lines[nn] array which ARE (probably) ours are printed.

# The -v option prints each triplet as they're found, separated 
# by '===' lines.

# PROBLEMS: 

Usage:	thisprogram <inputfile>

	Where <inputfile> contains the pclean generated pacct 
		lines in question.
	OUTPUT: Only those lines that DO NOT appear to be the 
		following commands at the same time (+/- 1 sec):
			");
  for  (keys(%commands)) {
    print "$_\n\t\t\t";
  }
  print ("\n");
exit;
}
($ctr,$cmd,$user,$group,$day,$mon,$date,$time,$year) = ("","","","","","","","","");
@prev1 = (0,$ctr,$cmd,$user,$group,$day,$mon,$date,$time,$year) ;
@prev2 = (-1,$ctr,$cmd,$user,$group,$day,$mon,$date,$time,$year) ;
$line = 1;
while ( <> ) {
  $lines[$line] = $_;
  ($ctr,$cmd,$user,$group,$day,$mon,$date,$time,$year) = split;
  @this = ($line++,$ctr,$cmd,$user,$group,$day,$mon,$date,$time,$year);
  if ($gotone <= 0) {
    #check if they're within 1 second--&closeintime uses prev1,prev2 and this as globals
    if (&closeintime) {
      #check if they're the ones we care about
      if ( $commands{$prev2[$commandfield]} && $commands{$prev1[$commandfield]} && 
	   $commands{$this[$commandfield]} ) {
	#now check to see they're three different commands...
	if (! (	$prev2[$commandfield] =~ $prev1[$commandfield] ||
		$prev2[$commandfield] =~ $this[$commandfield] ||
		$prev1[$commandfield] =~ $this[$commandfield] ) ) {
	  # i.e. if all three unique commands
	  # flag these as not ours
	  $notours{$prev2[0]} = $notours{$prev1[0]} = $notours{$this[0]} = 1;
	  #set $gotone to skip these if's for two lines
	  $gotone = 2;
	  print "===$prev2[$timefield]\n@prev2\n@prev1\n@this\n===\n" if ($debug);
	}
      }
      
    }
  } else {
    #deleted a triplet one or two back--go to next one...
    $gotone--;
  }
  @prev2 = @prev1;
  @prev1 = @this;
}
#That's it--show 'em what we got...
for ($i=0 ; $i<$line ; $i++) {
  print $lines[$i] if (! $notours{$i});
}
exit;

sub timetocompare {
  local ($time) = (@_);
  local ($hr,$min,$sec) = split(/:/,$time);
  return $hr * 60*60 + $min * 60 + $sec;
}

sub withinone {
  local($x,$y) = (@_);
  return 1 if (abs($x - $y) <= 1);
  return 0;
}
sub closeintime {
  local($t2,$t1,$t0);
  #uses @prev2, @prev1 and @this as globals
# if ($prev2[$timefield] =~ $this[$timefield] && $prev1[$timefield] =~ $this[$timefield]) {
  $t2 = &timetocompare($prev2[$timefield]);
  $t1 = &timetocompare($prev1[$timefield]);
  $t0 = &timetocompare($this[$timefield]);
  if ( &withinone($t2,$t1) && &withinone($t2,$t0) && &withinone($t0,$t1) ) {
    return 1;
  } else {
    return 0;
  }
}


sub cycle {
  local($last,$this,$next) = @_;
}
__END__
