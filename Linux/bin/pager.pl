#!/usr/bin/env perl
$version="2.0.0.2";
print("pager v$version called as: $0 @ARGV\n");

#DEFAULTS
$def_modem = "modem";
$def_phone_number = "918002537863";

#
# pager
#

$lockFile = "chat_lock";
$debug = (0 or defined $ENV{DEBUG} or defined $ENV{DBG});
#require 'codes.pl';
use Fcntl ':flock'; # import LOCK_* constants
use Getopt::Long;
use File::Basename;
$COLOR_SUCCESS="\033[1;32m";
$COLOR_FAILURE="\033[1;31m";
$COLOR_WARNING="\033[1;33m";
$COLOR_NORMAL="\033[0;39m";
$COLOR_NOTE="\033[0;34m";


$prog = basename $0;
# Display help message and exit with code
sub showHelp {
  my($exitCode) = @_;
  print <<EOF ;
usage: ${prog} [options] --code=pagerCode pagerNumbers

OPTIONS [defaults]
  --help
  --fake                Just shows the chat command that would be run.
  --phone=number        the number to dial               [$def_phone_number]
  --modem=DEV           device in /dev to dial with             [$def_modem]
  --code=pagerCode      number to send to pager(s)           (REQUIRED)

   pagerCode will show up on the pager(s) with '*' replaced by '-'

   pagerNumbers is a space speperated list of pager numbers, which
   can be named defined (pagerByName) in the codes.pl file.

   DEV -- when given, $0 uses /dev/DEV instead of /dev/$def_modem

$prog version $version
EOF
  exit $exitCode;
}



#
# Process options
#
$ok = &GetOptions("code=s" => \$code,
		  "modem=s" => \$modem,
		  "phone=s" => \$phone_number,
		  "fake" => \$fakePage,
		  "short" => \$shortCommand,
		  "help" => \$help);

dbg("code is $code",
    "phonenumber is $phone_number",
    "fake is $fakePage",
    "shortCommand is $shortCommand",
    "help is $help",
    "ok is $ok",
   );

if ($help) {
  &showHelp(0);
}

if (! $code) {
  $ok = 0;
  progprint("Must specify pager code");
}

if ($#ARGV < 0) {
  $ok = 0;
  progprint("Must specify pager numbers");
}

$modem =~ s,/dev/,,;
$modem = $def_modem unless $modem ;
if (! -e "/dev/$modem") {
  $ok = 0;
  progprint("/dev/$modem does not exist");
}

if (! $ok) {
  &showHelp(1);
}

# Use default number if not specified
if (! $phone_number) {
  $phone_number = $def_phone_number;
}

# Convert any '-'s to '*'s as that is what the paging
# system uses.  They will get displayed as '-' on the pagers.
$code =~ s/-/*/g;

#
# Build list of pager numbers from command line
# Some may be names that get translated from the codes.pl file
#
@pagers = ();
for $pagenum (@ARGV) {
  if ($pagenum+0 eq 0) {
    dbg("doing lookup of $pagenum");
    if (! defined $pagerByName{$pagenum}) {
      warn("$prog Warning: '$pagenum' is not defined in 'pagerByName' in codes.pl file\n");
      next;
    }
    $pagenum = $pagerByName{$pagenum};
  }

  push @pagers, $pagenum;
}


# Create lock file
open(FH, "> $lockFile");
flock(FH, LOCK_EX);

$problems=0 ;
# Send page to each pager
foreach $pager_number (@pagers) {
  chomp(my $now = `date -u "+%C%y%m%d-%RZ"`) ;
  progprint("$now page call '$phone_number', pager id '$pager_number', send code '$code', using /dev/$modem");
  $problems += page($phone_number, $pager_number, $code);
}

# Unlock
flock(FH,LOCK_UN);
close(FH);
exit $problems;




# Send a page to the number provided.  The code indicates the outage
# severity (normal or failure).  The code is sent in the page
# instead of the usual telephone number.
# The script works on a "expect - command" pair.
sub page {
    my($phone_number, $pager_number, $code) = @_;
    my $command = 	" chat -t 45 -v -- " . 
	" ABORT BUSY ABORT ERROR ABORT 'NO DIALTONE' HANGUP OFF " .
	" ''  " .			# expect nothing to begin
	" 'ATZ'    'OK'  " .		# reset modem
	" 'ATM1'   'OK'  " .		# speaker on
	" 'ATS7=5' 'OK'  " .		# wait time for carrier
	" 'ATDT$phone_number,,,,,$pager_number,,,,,$code#' 'NO CARRIER'  " .
	" < /dev/$modem > /dev/$modem " ;
    if ($fakePage) {
      if ($shortCommand) {
	$command = 	" chat -t 45 -v -- " . 
	  " ABORT BUSY ABORT ERROR ABORT 'NO DIALTONE' HANGUP OFF " .
	  " ''  " .			# expect nothing to begin
	  " 'ATDT$phone_number,,,,,$pager_number,,,,,$code#' 'NO CARRIER'  " .
	  " < /dev/$modem > /dev/$modem " ;
      }
      progprint ("--fake is on, so not running this\n\n$command\n");
      return ;
    }
    if ($shortCommand || system($command)) {
      # If user says try short first, or if it fails first time,
      # we try without any commands except the atdt
      $command = 	" chat -t 45 -v -- " . 
	" ABORT BUSY ABORT ERROR ABORT 'NO DIALTONE' HANGUP OFF " .
	" ''  " .			# expect nothing to begin
	" 'ATDT$phone_number,,,,,$pager_number,,,,,$code#' 'NO CARRIER'  " .
	" < /dev/$modem > /dev/$modem " ;
      system($command) && return 1;
    }

    return 0;
}
sub progprint {
  local ($what,$color,$color2,$what2) = (@_) ;
  $color = $COLOR_NOTE unless $color ;
  $color = $COLOR_FAILURE unless $ok;
  $color2 = $color unless $color2 ;
  $what2 = " $what2" if ($what2) ;
  my $child = "(parent)";
  $child = "(child )" if (! $kidpid);
  $child = "" unless (defined $kidpid) ;
  print("${color2}${prog}${child}[$$]$what2: ${color}$what$COLOR_NORMAL\n") ;
}#progprint
sub dbg {
  return unless $debug ;
  foreach (@_) {
    progprint("DBG: $_");
  }
}#dbg
