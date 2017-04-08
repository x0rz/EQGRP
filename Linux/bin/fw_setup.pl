#!/usr/bin/env perl
$version = "1.1.0.2";
use LWP;
use HTTP::Cookies;
use File::Basename qw(basename dirname);
my $autoutils = "../etc/autoutils" ;
unless (-e $autoutils) {
  $autoutils = "/current/etc/autoutils" ;
}
if (-e $autoutils) {
  require $autoutils;
}

#########################################################
#
# 19 Feb 2008
#
# A commandline script to configure the
# FK fireawll. Can be used to setup
# two default rules, and tear them down.
#
#########################################################

############### Configuration ###############

# Number of hours to apply our firewall rules
$TIMEOUT = 6;

############### MAIN ###############

my $ostype = lc $^O;
if ($ostype ne "linux") {
  die "This script is only meant to be run in Linux. Sorry!\n";
}

my $dowhat = "";

while (@ARGV) {
  if($ARGV[0] =~ /-v/i) {
    print "$prog version $version\n";
    exit 1;
  } elsif(lc $ARGV[0] eq "up" or lc $ARGV[0] eq "down") {
    $dowhat = lc shift(@ARGV);
  }
  if ($ARGV[0] =~ /([oi])=(\d+)/i) {
    $dowhat = "up";
    ($whichdirection,$port) = ($1,$2);
  }
  shift(@ARGV);
}

printUsage() unless $dowhat;

# get our default router, where the webpage lives
$route = `route -n`;
($dummy,$GATEWAY) = $route =~ /(0.0.0.0|default)\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+0.0.0.0/;
die "Cannot find default gateway via \"route -n\" command. Output was=$route=\n"
  unless $GATEWAY;

# get our ip
$ifconfig = `ifconfig eth0`;
$ifconfig =~ /inet addr:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+Bcast/;
$OUR_IP = $1;
die "Unable to determine our eth0 IP\n"
  unless $OUR_IP;


# FW username and password
if (0) {
  $USERNAME = getinput("\n\n$prog v.$version : Bringing firewall $dowhat at ".
		       gmtime()."\n(or enter \"abort\")\n\nLocal Firewall Username: ","user");
  die "User aborted\n" if ($USERNAME =~ /^abort/i);
  $PASSWORD = getinput("Local Firewall Password: ");
} else {
  $USERNAME = "user";
  $PASSWORD = "";
}

if ($dowhat eq "up") {
  # Want to start with clean slate if given a port to fix
  print "Re-setting firewall rules....\n";
  removeRules();
  sleep 1;
  createRules(lc $whichdirection,$port);
  my $expiretime = `date -d +6hours`;
  my $alarmtime = `date -d +330minutes`;
dbg("Calling   setAlarm");
  setAlarm(int(($TIMEOUT-0.50) * 60 * 60),30,
           "FIREWALL",
           "Your firewall rules will expire in 30 minutes.\n\n".
           "If necessary, use \"fw_setup.pl up\" to re-set it to $TIMEOUT hours,\n".
           "or use the browser GUI to add more time.\n\n".
           "Note that using \"fw_setup.pl up\" will cause a brief loss of comms that recovers nicely.",
	   "`date -d +6hours`"
	  );
  print "\n\nFirewall alarm is set, will go off at  $alarmtime".
    "to remind you that firewall expires at $expiretime\n\n";
} else {
  killothers("firewall going down");
  removeRules();
}

####################################################################
sub printUsage()
  {
    print <<EOF;

$prog [up | down] [i|o=PORTNUM]

Brings up/down your gateway's firewall rules to/from your IP.

If you use o=PORTNUM, the rules will allow ONLY traffic to outside
listeners (e.g., PITCHIMPAIRS) on PORTNUM.

If you use i=PORTNUM, the rules will allow ONLY traffic to
listeners on your IP at PORTNUM (e.g., -nrtun's or noclient -l's).

NOTE: Re-setting/removing firewall rules with $prog will NOT
      sever your ESTABLISHED sessions. They may time out eventually,
      but that alone does not kill them. (i.e., $prog is safe
      to use mid-op.)

Be sure your default gateway has already been set before running this script.

$prog v.$version
EOF
	exit -1;
}

####################################################################
sub createRules() {
  local ($direction,$port) = (@_);
  my $more = "";
  $more = ", outbound tcp destination port fixed to $port"
    if ($direction eq "o");
  $more = ", inbound tcp destination port fixed to $port"
    if ($direction eq "i");

	print "Setting your gateway ($GATEWAY) firewall rules$more...";

	# construct objects
	$useragent = LWP::UserAgent->new;
	$cookie_jar = HTTP::Cookies->new;

	# send request for main FW page
	$request = new HTTP::Request('GET',"http://$GATEWAY");
	$response = $useragent->simple_request($request);

	# extract cookie from response header
	$cookie_jar->extract_cookies($response);

	# login and get auth cookie
	$request = new HTTP::Request('GET',"http://$GATEWAY/session_login.cgi?page=%2F&user=$USERNAME&pass=$PASSWORD");
	$cookie_jar->add_cookie_header($request);
	$response = $useragent->simple_request($request);

	# save that authenticated cookie
	$cookie_jar->extract_cookies($response);

	# get fw config webpage
	$request = new HTTP::Request('GET',"http://$GATEWAY/firewall/");
	$cookie_jar->add_cookie_header($request);
	$response = $useragent->simple_request($request);

	# Get magic number from this page, used for saving the rules
	$response->as_string =~ /input type=hidden name=oldatjob value=(\d*)>/;
	$magic_num = $1;

	# Bring up the Edit Rule webpage
	$request = new HTTP::Request('GET',"http://$GATEWAY/firewall/edit_rule.cgi?table=0&chain=FORWARD&modip=$OUR_IP&new=1");
	$cookie_jar->add_cookie_header($request);
	$response = $useragent->simple_request($request);

	# Open tunnel INBOUND from GATEWAY
	$request = new HTTP::Request('POST',"http://$GATEWAY/firewall/save_rule.cgi");
	$cookie_jar->add_cookie_header($request);
	$request->referer("http://$GATEWAY/firewall/edit_rule.cgi?table=0&chain=FORWARD&modip=$OUR_IP&new=1");
	$request->content_type('application/x-ww-form-urlencoded');
  if ($direction eq "o") {
    $request->content("table=0&idx=&new=1&chain=FORWARD&before=&after=&modip=$OUR_IP&cmt=&jump=ACCEPT&other=&rwithdef=1&rwithtype=icmp-net-unreachable&source=0&source_mode=0&dest=$OUR_IP&dest_mode=1&frag=0&proto_mode=1&proto=tcp&proto_other=&sport_mode=1&sport_type=0&sport=$port&sport_from=&sport_to=&dport_mode=0&dport_type=0&dport=&dport_from=&dport_to=&ports_mode=0&ports=&tcpflags_mode=0&tcpoption_mode=0&tcpoption=&icmptype_mode=0&icmptype=any&macsource_mode=0&macsource=&limit_mode=0&limit0=&limit1=second&limitburst_mode=0&limitburst=&state_mode=0&tos_mode=0&tos=Minimize-Delay&mods=&args=");
  } elsif ($direction eq "i") {
    $request->content("table=0&idx=&new=1&chain=FORWARD&before=&after=&modip=$OUR_IP&cmt=&jump=ACCEPT&other=&rwithdef=1&rwithtype=icmp-net-unreachable&source=0&source_mode=0&dest=$OUR_IP&dest_mode=1&frag=0&proto_mode=1&proto=tcp&proto_other=&sport_mode=0&sport_type=0&sport=&sport_from=&sport_to=&dport_mode=1&dport_type=0&dport=$port&dport_from=&dport_to=&ports_mode=0&ports=&tcpflags_mode=0&tcpoption_mode=0&tcpoption=&icmptype_mode=0&icmptype=any&macsource_mode=0&macsource=&limit_mode=0&limit0=&limit1=second&limitburst_mode=0&limitburst=&state_mode=0&tos_mode=0&tos=Minimize-Delay&mods=&args=");
  } else {
    $request->content("table=0&idx=&new=1&chain=FORWARD&before=&after=&modip=$OUR_IP&cmt=&jump=ACCEPT&other=&rwithdef=1&rwithtype=icmp-net-unreachable&source=0&source_mode=0&dest=$OUR_IP&dest_mode=1&frag=0&proto_mode=0&proto=tcp&proto_other=&sport_mode=0&sport_type=0&sport=&sport_from=&sport_to=&dport_mode=0&dport_type=0&dport=&dport_from=&dport_to=&ports_mode=0&ports=&tcpflags_mode=0&tcpoption_mode=0&tcpoption=&icmptype_mode=0&icmptype=any&macsource_mode=0&macsource=&limit_mode=0&limit0=&limit1=second&limitburst_mode=0&limitburst=&state_mode=0&tos_mode=0&tos=Minimize-Delay&mods=&args=");
  }

	$response = $useragent->simple_request($request);

	# Bring up the Edit Rules page
	$request = new HTTP::Request('GET',"http://$GATEWAY/firewall/edit_rule.cgi?table=0&chain=FORWARD&modip=$OUR_IP&new=1");
	$cookie_jar->add_cookie_header($request);
	$response = $useragent->simple_request($request);

	# Open tunnel OUTBOUND from GATEWAY
	$request = new HTTP::Request('POST',"http://$GATEWAY/firewall/save_rule.cgi");
	$cookie_jar->add_cookie_header($request);
        $request->referer("http://$GATEWAY/firewall/edit_rule.cgi?table=0&chain=FORWARD&modip=$OUR_IP&new=1");
	$request->content_type('application/x-ww-form-urlencoded');
  if ($direction eq "o") {
    $request->content("table=0&idx=&new=1&chain=FORWARD&before=&after=&modip=$OUR_IP&cmt=&jump=ACCEPT&other=&rwithdef=1&rwithtype=icmp-net-unreachable&source=$OUR_IP&source_mode=1&dest=0&dest_mode=0&frag=0&proto_mode=1&proto=tcp&proto_other=&sport_mode=0&sport_type=0&sport=&sport_from=&sport_to=&dport_mode=1&dport_type=0&dport=$port&dport_from=&dport_to=&ports_mode=0&ports=&tcpflags_mode=0&tcpoption_mode=0&tcpoption=&icmptype_mode=0&icmptype=any&macsource_mode=0&macsource=&limit_mode=0&limit0=&limit1=second&limitburst_mode=0&limitburst=&state_mode=0&tos_mode=0&tos=Minimize-Delay&mods=&args=");
  } elsif ($direction eq "i") {
    $request->content("table=0&idx=&new=1&chain=FORWARD&before=&after=&modip=$OUR_IP&cmt=&jump=ACCEPT&other=&rwithdef=1&rwithtype=icmp-net-unreachable&source=$OUR_IP&source_mode=1&dest=0&dest_mode=0&frag=0&proto_mode=1&proto=tcp&proto_other=&sport_mode=1&sport_type=0&sport=$port&sport_from=&sport_to=&dport_mode=0&dport_type=0&dport=&dport_from=&dport_to=&ports_mode=0&ports=&tcpflags_mode=0&tcpoption_mode=0&tcpoption=&icmptype_mode=0&icmptype=any&macsource_mode=0&macsource=&limit_mode=0&limit0=&limit1=second&limitburst_mode=0&limitburst=&state_mode=0&tos_mode=0&tos=Minimize-Delay&mods=&args=");
  } else {
    $request->content("table=0&idx=&new=1&chain=FORWARD&before=&after=&modip=$OUR_IP&cmt=&jump=ACCEPT&other=&rwithdef=1&rwithtype=icmp-net-unreachable&source=$OUR_IP&source_mode=1&dest=0&dest_mode=0&frag=0&proto_mode=0&proto=tcp&proto_other=&sport_mode=0&sport_type=0&sport=&sport_from=&sport_to=&dport_mode=0&dport_type=0&dport=&dport_from=&dport_to=&ports_mode=0&ports=&tcpflags_mode=0&tcpoption_mode=0&tcpoption=&icmptype_mode=0&icmptype=any&macsource_mode=0&macsource=&limit_mode=0&limit0=&limit1=second&limitburst_mode=0&limitburst=&state_mode=0&tos_mode=0&tos=Minimize-Delay&mods=&args=");
  }
	$response = $useragent->simple_request($request);

	# Set the timeout and apply config
	$request = new HTTP::Request('GET',"http://$GATEWAY/firewall/apply.cgi?table=0&modip=$OUR_IP&oldatjob=$magic_num&duration=$TIMEOUT&duration_units=60");
	$cookie_jar->add_cookie_header($request);
	$response = $useragent->simple_request($request);

	print gmtime()." done, timeout set to $TIMEOUT hours\n";
  logaction("firewall opened $direction=$port");
}

####################################################################
sub killothers {
  local ($morecomment) = (@_);
  my $comment = "Killing previous instance of fw_setup.pl alarm";
  $comment .= ", $morecomment" if $morecomment;
  $comment .= ":";
  dbg("ps -ef | egrep -v \" $$ |grep\" | grep perl.*fw_setup.pl");
  chomp(my $othertest = `ps -ef | egrep -v " $$ |grep" | grep perl.*fw_setup.pl`);
  foreach (split(/\n/,$othertest)) {
    # alarms only started by fw_setup.pl up (not down).
    next if /fw_setup.pl down/;
    my ($pid) = /root\s*(\d+)\s/;
    print "\n\n$comment\n".
      $_;
    kill(15,$pid);
  }
  print "\n\n";
}

####################################################################
sub removeRules() {
	print "Removing your gateway ($GATEWAY) firewall rules...";


	# construct objects
	$useragent = LWP::UserAgent->new;
	$cookie_jar = HTTP::Cookies->new;

	# send request for main FW page
	$request = new HTTP::Request('GET',"http://$GATEWAY");
	$response = $useragent->simple_request($request);
	
	# extract cookie from response header
	$cookie_jar->extract_cookies($response);
	
      # login and get auth cookie
      $request = new HTTP::Request('GET',"http://$GATEWAY/session_login.cgi?page=%2F&user=user&pass=");
      $cookie_jar->add_cookie_header($request);
      $response = $useragent->simple_request($request);

	# save that authenticated cookie
	$cookie_jar->extract_cookies($response);
	
	# get fw config webpage
	$request = new HTTP::Request('GET',"http://$GATEWAY/firewall/");
	$cookie_jar->add_cookie_header($request);
	$response = $useragent->simple_request($request);
	
	# Clear the rules
	$request = new HTTP::Request('GET',"http://$GATEWAY/firewall/save_policy.cgi?table=0&modip=$OUR_IP&chain=FORWARD&clear=Clear+All+Rules");
	$cookie_jar->add_cookie_header($request);
	$response = $useragent->simple_request($request);
	
	# Confirm we want to clear the rules
	$request = new HTTP::Request('GET',"http://$GATEWAY/firewall/save_policy.cgi?table=0&modip=$OUR_IP&chain=FORWARD&clear=1&confirm=Delete+Now");
	$cookie_jar->add_cookie_header($request);
	$response = $useragent->simple_request($request);

      # Set the timeout and apply config
      $request = new HTTP::Request('GET',"http://$GATEWAY/firewall/apply.cgi?table=0&modip=$OUR_IP&oldatjob=$magic_num&duration=$TIMEOUT&duration_units=60");
      $cookie_jar->add_cookie_header($request);
      $response = $useragent->simple_request($request);
	
	print gmtime()." done\n";
  logaction("firewall closed");
}
sub getinput {
  local($prompt,$default,@allowed) = @_;
  local($ans,$tmp,%other) = ();
  $other{"Y"} = "N" ; $other{"N"} = "Y" ;
  if ($other{$default} and ! (@allowed)) {
    push(@allowed,$other{$default}) ;
  }
  $tmp = $default;
  if (chop($tmp) eq "^M") {
    #damn ^M's in script files
    $default = $tmp;
  }
  SUB: while (1) {
    print STDERR $prompt;
    if ($default) {
      print STDERR " [$default] ";
    } else {
      print STDERR " ";
    }
    if ($prompt =~ /password/i) {
      print "(echo off)";
      `stty -echo`;
    }
    chomp($ans = <STDIN>);
    if ($prompt =~ /password/i) {
      `stty echo`;
      print "(echo on)\n";
    }
    $ans = $default if ( $ans eq "" );
    last SUB if ($#allowed < 0) ;
    foreach ($default,@allowed) {
      last SUB if $ans =~ /^$_/i ;
    }
  }
  return $ans;
} # getinput

sub logaction {
  preservefile("$opdown/fw_setup.log");
  open(LOG,">/current/down/fw_setup.log") or return;
  print LOG gmtime()." @_\n";
  close(LOG);
}

sub setAlarm {
  local($sleepsecs,$expiremin,$type,$comment,$expires) = (@_);
  $comment =~ s,\",\\\",g;
  $comment =~ s,\n,\\n,g;
  $expires = "EXPIRES=\"$expires\""
        if $expires;
  my $alarmfile = "/tmp/Alarm.sh";
  my $title = "ALARM";
  $type =~ s/\s/_/g ;
  $title .= "_$type" if $type;
  killothers("previous alarm not needed");
  if (open(ALARMOUT,">$alarmfile")) {
    print ALARMOUT <<EOF;
#!/bin/sh
/bin/rm -f \$0
$expires
while [ 1 ] ; do
  clear
  echo -e "\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\a"
  echo -e "Current time: `date`\\n\\n\\n"
  [ "\$EXPIRES" ] && echo -e "EXPIRES time: \$EXPIRES\\n\\n\\n"
  echo -e "$comment"
  echo -e "\\n\\n\\n\\n\\n\\n"
  echo "^C or close this window as desired, but this alarm has no snooze!"
  sleep 5
done
EOF
    close(ALARMOUT);
    chmod(0777,$alarmfile);
  }
  return if fork;
  close(STDOUT);
  close(STDIN);
  close(STDERR);
  sleep $sleepsecs;
  if (open(ALARMOUT,">$alarmfile")) {
    print ALARMOUT <<EOF;
#!/bin/sh
/bin/rm -f \$0
$expires
while [ 1 ] ; do
  clear
  echo -e "\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\a"
  echo -e "Current time: `date`\\n\\n\\n"
  [ "\$EXPIRES" ] && echo -e "EXPIRES time: \$EXPIRES\\n\\n\\n"
  echo -e "$comment"
  echo -e "\\n\\n\\n\\n\\n\\n"
  echo "^C or close this window as desired, but this alarm has no snooze!"
  sleep 5
done
EOF
    close(ALARMOUT);
    chmod(0777,$alarmfile);
    exec("xterm -ut +cm +cn -sk -sb -ls -title ALARM ".
         "-geometry 174x52-53+26 -bg white -fg red -e ".
         "$alarmfile");
  }
  exit;
}
