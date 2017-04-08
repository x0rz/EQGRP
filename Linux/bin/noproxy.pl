#!/usr/bin/perl 
$VER="1.2.0.1";

my $autoutils = "../etc/autoutils" ;
unless (-e $autoutils) {
  $autoutils = "/current/etc/autoutils" ;
}
require $autoutils;

myusage() if (! Getopts( "i:p:r:d:s:e:hH:F:tW:U:" ) ) ;
my $nopen_ip = $opt_i;
my $tunnel_port = $opt_p;
my $proxy_port = $opt_r;
my $dns_ip = $opt_d;
my $start_port = 40000;
$start_port = $opt_s if $opt_s > 0;
my $end_port = 60000;
$end_port = $opt_e if $opt_e > 0;
my $proxy_host = $opt_H;
my $log_file = $opt_F;
my $tcp = $opt_t;
my $whitelist = $opt_W;
my $useragent = $opt_U;
myusage() if ($opt_h or (!defined $opt_i or !defined $opt_p or !defined $opt_r or !defined $opt_d));

sub myusage {
  die "NOPROXY v.$VER\n\n".
    "Usage: noproxy.pl -i <nopen tunnel ip> -p <nopen -tunnel port> -r <proxy port> -d <dns ip>\n\n".
    "Optional Arguments\n".
    "-s <start ephemeral port, default 40000>\n".
    "-e <end ephemeral port, default 60000>\n".
    "-H <proxy host to bind on, default=any>\n".
    "-F <log file, default=stdout>\n".
    "-t <use tcp for nopen tunnel, default=udp>\n".
    "-W <whitelist> (Comma delimited list of IP/prefix entries in xxx.xxx.xxx.xxx/xx format\n".
    "   (note - the prefix is required--for one host, just use /32)\n".
    "-U <useragent>    (e.g., -U Mozilla/1.0)\n\n";
}

my @whitelist = split(/,+/,$whitelist);
my $network;
my $prefix;
my %allowed = ();		# key=$network value=$prefix
foreach $whitelist (@whitelist) {
  $network = `ipcalc -sn $whitelist`;
  $network =~ s/NETWORK=//g;
  chomp($network);
  $prefix = `ipcalc -ps $whitelist`;
  $prefix =~ s/PREFIX=//g;
  chomp($prefix);
  die "Invalid whitelist $whitelist\n"
    unless $prefix and $network;
  print "Whitelist: Allowing $network\n";
  $allowed{$network}=$prefix;
}
print "\n";
$proxy_host = "" unless (defined $opt_H);

my $log_fh = *STDOUT;
if (defined $log_file) {
  open $log_fh, ">$log_file" or die "Can't open log file: $log_file!";
}

use IO::Socket qw(:DEFAULT :crlf);
use HTTP::Proxy;
use HTTP::Proxy::HeaderFilter::simple;
use strict;
use Thread::Queue;

srand( time() ^ ($$ + ($$ << 15)) );
my $pcounter = pickport();

#initialize the connection to the nopen tunnel listener
print "Connecting to " . $nopen_ip . " on port " . $tunnel_port . " for nopen tunnel commands.\n";
my $socket;

if ($tcp) {
  $socket = IO::Socket::INET->new(PeerAddr =>$nopen_ip,PeerPort=>$tunnel_port,Proto=>"tcp",Type=>SOCK_STREAM) or die "couldn't connect to $nopen_ip : $tunnel_port $@\n";
} else {
  $socket = IO::Socket::INET->new(PeerAddr =>$nopen_ip,PeerPort=>$tunnel_port,Proto=>"udp",Type=>SOCK_DGRAM) or die "couldn't connect to $nopen_ip : $tunnel_port $@\n";
}
#setup one tunnel for dns
print "Opening DNS tunnel to " . $dns_ip . ".\nBe sure to set this box's IP address as your DNS!!\n"; 
print $socket "u 53 " . $dns_ip ."$CRLF";

#create an empty response to return when invalid/inaccessible requests are made
my $no = HTTP::Response->new ( 200 );
$no->content_type('text/plain');
$no->content('.');

#initialize the proxy
my $proxy = HTTP::Proxy->new( host => $proxy_host, port => $proxy_port, logfh => $log_fh, logmask  => 1);

#add our "filter" which handles the nopen stuff for each request
$proxy->push_filter( request => 
		     HTTP::Proxy::HeaderFilter::simple->new
		     (
		      sub {
			my ( $self, $headers, $message ) = @_;
			#modify the useragent if necessary
			
			if (defined $useragent) {
			  $message->headers->header( User_Agent => "$useragent" );
			}
			#pick a "random" port to listen on
			$pcounter = pickport();
			$proxy->log
			  ( 1,
			    " MESSAGE_URI: "    . $message->uri .
			    " PRE_FILTER".
			    " Host: "           . $message->uri->host .
			    " LOC_TUN_PORT: "        . $pcounter .
			    " Port: " . $message->uri->port #.
			  );
			
			#do a dns query
			my $ohost = $message->uri->host;
			if (my $nhost = gethostbyname($ohost)) {
			  $nhost = inet_ntoa($nhost);
			  $proxy->log( 32, "DNS", $message->uri->host . " resolves to " . $nhost . "$CRLF");
			  if ($whitelist) {
			    my $good = 0;
			    #check the whitelist
			    foreach my $network (keys %allowed) {
			      my $prefix = $allowed{$network};
			      my $whost = `ipcalc -sn $nhost/$prefix`;
			      $whost =~ s/NETWORK=//g;
			      chomp($whost);
			      if ($network eq $whost && $good == 0) {
				$good = 1;
				open_tunnel($nhost,$message);
			      }
			    }
				#if we haven't found a match on the whitelist, block the request
				if($good == 0){
				    my $blocked = $no;
				    $blocked->content("noproxy.pl: $nhost NOT ON WHITELIST");
				    $self->proxy->response( $blocked );
  
				    $message->uri->host('127.0.0.1');
				    $message->uri->port(pickport());
				
				    $proxy->log( 32, "WHITELIST", "$nhost not allowed by whitelist ($whitelist)");
				}
			  } else {
			    open_tunnel($nhost,$message) ;
			  }
			} else {
			  my $blocked = $no;
			  $blocked->content("noproxy.pl: $ohost DID NOT RESOLVE");
			  $self->proxy->response( $blocked );
			  $message->uri->host('127.0.0.1');
			  $message->uri->port(pickport());
			  
			  $proxy->log( 32, "DNS", "Couldn't resolve: " . $ohost . "$CRLF" );
			}
			$proxy->log( 1, "POST-FILTER", "Host: " . $message->uri->host . " Port: " . $message->uri->port . "$CRLF");
		      }
		     )
		   );

$proxy->start;

sub open_tunnel {
  my ($myhost,$message) = (@_);
  $proxy->log( 32, "TUNNEL", "Closing  tunnel$CRLF");

  #close any open listeners
  print $socket "c 2$CRLF";
  wait_for_close();


  $proxy->log( 32, "TUNNEL", "Opening tunnel: l " . $pcounter . " " . $myhost . " " . $message->uri->port . "$CRLF");

  #open the nopen tunnel
  print $socket "l " . $pcounter . " " . $myhost . " " . $message->uri->port . "$CRLF";
  wait_for_open();

  #rewrite the request to point to the local listener
  $message->uri->host($nopen_ip);
  $message->uri->port($pcounter);
}

sub wait_for_open{
  recv($socket,my $content1,2056,0);
  my $content;
  while (!($content1 =~ /channel 2 listen success/)) {
    recv($socket,$content,2056,0);
    $content1 .= $content;
    #print "Got $content1 from server\n";
    if ($content1 =~ /Address already in use/) {
      print "LISTEN PORT ALREADY IN USE!!!!!  IGNORING REQUEST!!!\n";
      last();
    }
  }
}

sub wait_for_close{
  recv($socket,my $content1,2056,0);
  my $content;
  while (! ($content1 =~ /(Closing Channel 2 is complete|Channel 2 is already closed)/)) {
    recv($socket,$content,2056,0);
    $content1 .= $content;
    #print "Got $content1 from server\n";
  }
}

sub pickport {
  #pick a random port to listen on locally
  #This works now because noclient is run locally.  It would be sketchy at best if noclient was running on a different box since we check our own netstat for ports.
  my $port ;
  while (1) {
    $port = int(rand ($end_port-$start_port)) + $start_port;
    my @test = grep /^\s*tcp\s.*\s\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:$port\s.*(LISTEN|\S*TIME|CLOSE|ESTAB|\S*WAIT)/, `netstat -an`;
    last unless @test;
    #tcp        0      0 127.0.0.1:631               0.0.0.0:*                   LISTEN      
  }
  return $port;
}
