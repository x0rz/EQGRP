#!/usr/bin/env perl
$version = "2.0.0.3";
use LWP;
use HTTP::Cookies;
require "getopts.pl";
use File::Basename qw(basename dirname);
$prog = basename $0;
#########################################################
#
# 19 Aug 2008
#
# A commandline script to configure the
# FK firewall. 
#
#########################################################

my $autoutils = "../etc/autoutils" ;
unless (-e $autoutils) {
  $autoutils = "/current/etc/autoutils" ;
}
if (-e $autoutils) {
  require $autoutils;
}


############### MAIN ###############

# Get OS ($^0 returns O/S that Perl was compiled for)
my $ostype = lc $^O;

# If OS is not Linux, exit
if ($ostype ne "linux") 
{
  mydie("This script is only meant to be run in Linux. Sorry!");
}
# Use Getopts to parse @ARGV
mydie("bad option(s)") if (! Getopts( "hvrasu:t:p:i:cR:" ) ) ;

mydie("\n$prog version $version\n") if $opt_v;
$initialsetup = $opt_c;
printUsage() if $opt_h or @ARGV;
$remove_rules = $opt_r;
@ADDIPS = split(/[\s,]+/,$opt_i);
foreach (@ADDIPS) {
  mydie("Invalid IP -i $_")
    unless /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/;
}
$allowall = $opt_a;
$showrules = $opt_s;
$TIMEOUT = int($opt_t);
mydie("Timeout -t $TIMEOUT must be at most 8")
  if ($opt_t and ($TIMEOUT > 8 or $TIMEOUT < 0));
$USERNAME = $opt_u;
$USERNAME = $opuser unless $USERNAME;
$PASSWORD = $opt_p;
$PASSWORD = $oppasswd unless $PASSWORD;

mydie("-a cannot be used with any of -i, -c -r or -s")
  if (($remove_rules or $showrules or @ADDIPS or $initialsetup) and
      ($allowall));

mydie("-i and -c cannot be used with -r or -s")
  if (($remove_rules or $showrules) and (@ADDIPS or $initialsetup));

mydie("-u USERNAME is required")
  unless $USERNAME;


#$REMOTEIP = $opt_i;
#mydie("Invalid remote IP -r $REMOTEIP")
#  unless $REMOTEIP =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/;


# If user did not specify a username from the command line,
# display usage and exit
printUsage(0) unless $USERNAME;

# If user did not specify a password from the command line,
# prompt interactively
if(!$PASSWORD) {
  system ("stty -echo");
  print "\n".gmtime()." $prog: Enter Password for $USERNAME: ";
  chomp ($PASSWORD=<STDIN>);
  system ("stty echo");
}
dbg("c=$opt_c i=$opt_i A=(@ADDIPS)");

# Get our default gateway (which is the FW)
# MODIFIED - our test gateway is different than the default gateway
# get our default router, where the webpage lives
$route = `route -n`;
($dummy,$GATEWAY) = $route =~ /(0.0.0.0|default)\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+0.0.0.0/;
# -R option not in usage, switches to this IP for testing if -R is on
$GATEWAY = $opt_R if $opt_R;
mydie("Cannot find default gateway via \"route -n\" command. Output was=$route=")
  unless $GATEWAY =~ /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/;
# <END MODIFICATION>


# Get our FK IP
# MODIFIED - originally, would not die if interface did not contain an IP
# **Also changed "ifconfig eth0" to "ifconfig eth1" because our test system's IP was on eth1
# get our ip
$ifconfig = `ifconfig eth0`;
($dummy2, $OUR_IP) = $ifconfig =~ /(inet addr:)(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+Bcast/;

die "Unable to determine our eth0 IP\n"
  unless $OUR_IP;
# <END MODIFICATION>

# Die here with usage unless we have creds
printUsage(1) unless $USERNAME and $PASSWORD;

# ASSERT: We will be making a connection, so the rest all
# requires authentication.
fwConnect();

if($remove_rules) {
  removeRules();
  listRules();
  exit 1;
}

InitialSetup() if $initialsetup;

if (@ADDIPS) {
  addIp(@ADDIPS);
}

if ($initialsetup or @ADDIPS) {
  listRules();
  exit;
}

if($showrules) {
   listRules();
   exit 1;
}

if($allowall) {
   allowAll();
   exit 1;
}


# If -t option was specified at command line (without -ip)
# **NOTE:  This simply updates duration time (does not create or remove rules)
if($TIMEOUT and !@ADDIPS and !$initialsetup)
{
   setTimeout($TIMEOUT);
   listRules();
   exit 1;
}


# Otherwise, print usage and exit
printUsage(2);


############### FUNCTIONS ###############

####################################################################
# Displays usage and exits

sub printUsage()
{
myprint("GOT COMMENT: @_") if @_;
   print <<EOF;

  *** $prog v.$version ***

  Options:
    -u <username>  <--- Specify username
    -p <password>  <--- Specify password
    -a             <--- Allow All--Creates open inbound and outbound rules
    -c             <--- Clears then creates initial rules:
                             Us to anywhere
                             valid responses back to us
    -i <ip>        <--- Specify remote IP (i.e. pitch) to allow inbound.
                        Use additional -R IP arguments to have several.
    -t <timeout>   <--- Specify timeout (in hours) [def: $TIMEOUT]
    -s             <--- Lists configured FW rules as well as duration
    -r             <--- Remove all rules

    -v             <--- Show version
    -h             <--- Show usage

  Usage:
     Create Default Rules (-i,-t optional):
         $prog -u <username> -p <password> -c [-i <ip>] [-t <timeout>]
     Create Allow All Rules (allows all both inbound and outbound to all):
         $prog -u <username> -p <password> -allowall [-t <timeout>]
     Allow Additional external IP (bi-directional):
         $prog -u <username> -p <password> -i <ip>
     Update Timeout Only (does not modify rules):
         $prog -u <username> -p <password> -t <timeout>
     Show Configured Rules and Duration:
         $prog -u <username> -p <password> -s
     Remove All Rules:
         $prog -u <username> -p <password> -r
	

  **NOTE:  Be sure your default gateway is set before running this script.

EOF
   exit -1;
}

####################################################################
# Performs initial connection to FW (connects, authenticates, and 
# gets auth cookie)

sub fwConnect()
{

   # Construct objects
   $useragent = LWP::UserAgent->new;
   $cookie_jar = HTTP::Cookies->new;

   # Give up on requests that don't answer within 15 seconds
   $useragent->timeout(15);

   # Send request for main FW page
   $request = new HTTP::Request('GET',"http://$GATEWAY");
   $response = $useragent->simple_request($request);
   if(not($response->is_success)) 
     {
       myprint("\n\n!! Could not get main FW page !!\n\n".
	   "Error reported:\n\t".
	   $response->status_line."\n\n");
       exit -1;
     }

   # Extract cookie from response header
   $cookie_jar->extract_cookies($response);

   # Login and get auth cookie
   $request = new HTTP::Request('GET',"http://$GATEWAY/session_login.cgi?page=%2F&user=$USERNAME&pass=$PASSWORD");
   $cookie_jar->add_cookie_header($request);
   $response = $useragent->simple_request($request);

   # Save that authenticated cookie
   $cookie_jar->extract_cookies($response);
}




####################################################################
# Lists configured rules

sub listRules()
{
   # **NOTE:  Assumes fwConnect() has already been run!!
   #
   # Get FW config HTML and parse out configured rules
   $request = new HTTP::Request('GET',"http://$GATEWAY/firewall/");
   $cookie_jar->add_cookie_header($request);
   $response = $useragent->simple_request($request);

   $firewall_html = $response->as_string;

   $firewall_html =~ s/(<b>)|(<\/b>)//gi;

   @FW_RULES = ($firewall_html =~ m/<td>(If (?:source|destination).*)<\/td>/g); 

   @DURATION = ($firewall_html =~ m/(?:Duration of rules.*Max.*duration value=(.*))/g);



   myprint("\n\nThe following ALLOW rules are defined:");

   myprint("\n\t!! NO RULES DEFINED !!") unless @FW_RULES;

   while(@FW_RULES)
   {
     myprint("\t** $FW_RULES[0]");
     shift(@FW_RULES);
   } 

   myprint("\n\t!! UNABLE TO DETERMINE DURATION !!\n\n") unless @DURATION;

   while(@DURATION)
   {
     myprint("\nDuration (min): $DURATION[0]\n\n");
     shift(@DURATION);
   }

}





####################################################################
# Creates default FW rules which perform the following:
# - Allow us to any
# - Allow specified IP (i.e. pitch) to us

sub InitialSetup()
{
   myprint("\nCreating Initial FW rules...\n");

   # Remove any existing rules
   removeRules();

   # Default number of hours to apply our firewall rules
   $TIMEOUT = 6 unless $TIMEOUT;

   # CREATE FW RULES AND CONFIGURE TIMEOUT

   # RULE #1:  Allow us to any
   $request = new HTTP::Request('POST',"http://$GATEWAY/firewall/save_rule.cgi");
   $cookie_jar->add_cookie_header($request);
   $request->referer("http://$GATEWAY/firewall/edit_rule.cgi?table=0&chain=FORWARD&modip=$OUR_IP&new=1");
   $request->content_type('application/x-ww-form-urlencoded');

   $request->content("table=0&idx=&new=1&chain=FORWARD&before=&after=&modip=$OUR_IP&cmt=&jump=ACCEPT&rwithdef=1&rwithtype=icmp-net-unreachable&source_radio=on&source_other=&source_mode=1&source=$OUR_IP&dest_radio=0&dest_other=&dest_mode=0&dest=$OURIP&frag=0&proto_mode=0&proto=tcp&proto_other=&sport_mode=0&sport_type=0&sport=&sport_from=&sport_to=&dport_mode=0&dport_type=0&dport=&dport_from=&dport_to=&show_adv=1&tcpflags_mode=0&tcpoption_mode=0&tcpoption=&icmptype_mode=0&icmptype=any&macsource_mode=0&macsource=&limit_mode=0&limit0=&limit1=second&limitburst_mode=0&limitburst=&state_mode=0&tos_mode=0&tos=Minimize-Delay");

   $response = $useragent->simple_request($request);



   # RULE #2:  Allow existing connections to return data to us (used in conjunction with us to any rule)
   $request = new HTTP::Request('POST',"http://$GATEWAY/firewall/save_rule.cgi");
   $cookie_jar->add_cookie_header($request);
   $request->referer("http://$GATEWAY/firewall/edit_rule.cgi?table=0&chain=FORWARD&modip=$OUR_IP&new=1");
   $request->content_type('application/x-ww-form-urlencoded');

   $request->content("table=0&idx=&new=1&chain=FORWARD&before=&after=&modip=$OUR_IP&cmt=&jump=ACCEPT&rwithdef=1&rwithtype=icmp-net-unreachable&source_radio=0&source_other=&source_mode=0&source=$OUR_IP&dest_radio=on&dest_other=&dest_mode=1&dest=$OUR_IP&frag=0&proto_mode=0&proto=tcp&proto_other=&sport_mode=0&sport_type=0&sport=&sport_from=&sport_to=&dport_mode=0&dport_type=0&dport=&dport_from=&dport_to=&show_adv=1&tcpflags_mode=0&tcpoption_mode=0&tcpoption=&icmptype_mode=0&icmptype=any&macsource_mode=0&macsource=&limit_mode=0&limit0=&limit1=second&limitburst_mode=0&limitburst=&state_mode=1&state=ESTABLISHED&tos_mode=0&tos=Minimize-Delay");

   $response = $useragent->simple_request($request);

   # Set the timeout 
   setTimeout($TIMEOUT);

}


####################################################################
# Configure new rule to allow inbound connections from specified IP

sub addIp()
{
   local(@ips) = @_;

   foreach my $ip (@ips) {
     # Allow IP to us
     $request = new HTTP::Request('POST',"http://$GATEWAY/firewall/save_rule.cgi");
     $cookie_jar->add_cookie_header($request);
     $request->referer("http://$GATEWAY/firewall/edit_rule.cgi?table=0&chain=FORWARD&modip=$OUR_IP&new=1");
     $request->content_type('application/x-ww-form-urlencoded');
     
     $request->content("table=0&idx=&new=1&chain=FORWARD&before=&after=&modip=$OUR_IP&cmt=&jump=ACCEPT&rwithdef=1&rwithtype=icmp-net-unreachable&source_radio=on&source_other=$ip&source_mode=1&source=$ip&dest_radio=on&dest_other=&dest_mode=1&dest=$OUR_IP&frag=0&proto_mode=0&proto=tcp&proto_other=&sport_mode=0&sport_type=0&sport=&sport_from=&sport_to=&dport_mode=0&dport_type=0&dport=&dport_from=&dport_to=&show_adv=0&tcpflags_mode=0&tcpoption_mode=0&tcpoption=&icmptype_mode=0&icmptype=any&macsource_mode=0&macsource=&limit_mode=0&limit0=&limit1=second&limitburst_mode=0&limitburst=&state_mode=0&tos_mode=0&tos=Minimize-Delay");
     
     $response = $useragent->simple_request($request);
   }
   setTimeout($TIMEOUT) unless $initialsetup or !$TIMEOUT;
   logaction("firewall opened allowed=@ips");
}



####################################################################
# Create default rules to allow all both inbound and outbound

sub allowAll()
{
   removeRules();

   myprint("\nCreating allow all rules..\n\n");

   # Allow us to any
   $request = new HTTP::Request('POST',"http://$GATEWAY/firewall/save_rule.cgi");
   $cookie_jar->add_cookie_header($request);
   $request->referer("http://$GATEWAY/firewall/edit_rule.cgi?table=0&chain=FORWARD&modip=$OUR_IP&new=1");
   $request->content_type('application/x-ww-form-urlencoded');

   $request->content("table=0&idx=&new=1&chain=FORWARD&before=&after=&modip=$OUR_IP&cmt=&jump=ACCEPT&rwithdef=1&rwithtype=icmp-net-unreachable&source_radio=on&source_other=&source_mode=1&source=$OUR_IP&dest_radio=0&dest_other=&dest_mode=0&dest=$OURIP&frag=0&proto_mode=0&proto=tcp&proto_other=&sport_mode=0&sport_type=0&sport=&sport_from=&sport_to=&dport_mode=0&dport_type=0&dport=&dport_from=&dport_to=&show_adv=1&tcpflags_mode=0&tcpoption_mode=0&tcpoption=&icmptype_mode=0&icmptype=any&macsource_mode=0&macsource=&limit_mode=0&limit0=&limit1=second&limitburst_mode=0&limitburst=&state_mode=0&tos_mode=0&tos=Minimize-Delay");

   $response = $useragent->simple_request($request);


   # Allow any to us
   $request = new HTTP::Request('POST',"http://$GATEWAY/firewall/save_rule.cgi");
   $cookie_jar->add_cookie_header($request);
   $request->referer("http://$GATEWAY/firewall/edit_rule.cgi?table=0&chain=FORWARD&modip=$OUR_IP&new=1");
   $request->content_type('application/x-ww-form-urlencoded');

   $request->content("table=0&idx=&new=1&chain=FORWARD&before=&after=&modip=$OUR_IP&cmt=&jump=ACCEPT&rwithdef=1&rwithtype=icmp-net-unreachable&source_radio=0&source_other=&source_mode=0&source=$OUR_IP&dest_radio=on&dest_other=&dest_mode=1&dest=$OUR_IP&frag=0&proto_mode=0&proto=tcp&proto_other=&sport_mode=0&sport_type=0&sport=&sport_from=&sport_to=&dport_mode=0&dport_type=0&dport=&dport_from=&dport_to=&show_adv=0&tcpflags_mode=0&tcpoption_mode=0&tcpoption=&icmptype_mode=0&icmptype=any&macsource_mode=0&macsource=&limit_mode=0&limit0=&limit1=second&limitburst_mode=0&limitburst=&state_mode=0&tos_mode=0&tos=Minimize-Delay");

   $response = $useragent->simple_request($request);

   $TIMEOUT = 6 unless $TIMEOUT;

   logaction("firewall opened allow all");
   setTimeout($TIMEOUT);

   listRules();
}




####################################################################
# Removes all FW rules

sub removeRules() 
{

  dbg("Sending:('GET',\"http://$GATEWAY/firewall/save_policy.cgi?table=0&modip=$OUR_IP&chain=FORWARD&clear=Clear+All+Rules\");");
   # Clear the rules
   $request = new HTTP::Request('GET',"http://$GATEWAY/firewall/save_policy.cgi?table=0&modip=$OUR_IP&chain=FORWARD&clear=Clear+All+Rules");
   $cookie_jar->add_cookie_header($request);
   $response = $useragent->simple_request($request);

   # Confirm we want to clear the rules
   $request = new HTTP::Request('GET',"http://$GATEWAY/firewall/save_policy.cgi?table=0&modip=$OUR_IP&chain=FORWARD&clear=1&confirm=Delete+Now");

   $cookie_jar->add_cookie_header($request);
	$response = $useragent->simple_request($request);

  logaction("firewall closed");

   # Set timeout
   setTimeout(1);
}


####################################################################
# Configures duration of FW rules

sub setTimeout()
{
   local($newtimeout) = @_;

   # Set the timeout 
   $request = new HTTP::Request('GET',"http://$GATEWAY/firewall/apply.cgi?table=0&modip=$OUR_IP&duration=$newtimeout&duration_units=60");

   $cookie_jar->add_cookie_header($request);
   $response = $useragent->simple_request($request);
}

sub dbg {
  open(FWLOG,">>/current/tmp/fwlog.txt") or return;
  print FWLOG gmtime()." @_\n";
  close(FWLOG);
}

sub mydie {
  die "@_\n";
}

sub myprint {
  dbg(@_);
  print "@_\n";
}

sub logaction {
  preservefile("$opdown/fw_setup.log");
  open(LOG,">$opdown/fw_setup.log") or return;
  print LOG gmtime()." @_\n";
  close(LOG);
}
