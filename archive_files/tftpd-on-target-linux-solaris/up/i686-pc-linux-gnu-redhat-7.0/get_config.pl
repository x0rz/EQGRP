#!/usr/bin/perl -w
#
#  get_config = a program using snmp_set to cause a cisco
#                router to tftp its config to tftp server specified.
#
#
require 5.002;
use strict;
use SNMP_Session;
use BER;

my %OIDS = (
            'writeNet'       => '1.3.6.1.4.1.9.2.1.55'
            

	 );
	 
my ($host, $oid, $community,$tftpserver, $response);
($host = shift) or die "usage: $0 <hostname> [<community>]";
$community = shift || 'public';

($tftpserver = shift) or die "usage: $0 <hostname> [<community>] <tftpserver>";
	
$oid = "writeNet.$tftpserver";

#print "Host is $host, tftpserver is $tftpserver, oid is $oid\n";


($response) = &snmpset($host, $community, $oid, 'string', 'ciscosupport.config');

if ($response) {
	print "$oid : $response\n";
} else {
	print "$host did not respond to SNMP query\n";
	exit;
}

sub snmpset {
	my($host,$community,@varList) = @_;
	my(@enoid, $response, $bindings, $binding, $inoid,$outoid,
		$upoid,$oid,@retvals);
  	my ($type,$value);
	while (@varList) {
		$oid   = toOID(shift @varList);
		$type  = shift @varList;
		$value = shift @varList;
		($type eq 'string') && do {
			$value = encode_string($value);
			push @enoid, [$oid,$value];
			next;
		};
		($type eq 'int') && do {
			$value = encode_int($value);
			push @enoid, [$oid,$value];
			next;
		};
		die "Unknown SNMP type: $type";
	}
	srand();
	my $session = SNMP_Session->open ($host , $community, 161);
	$session->set_timeout(60);
        $session->set_retries(1);
	if ($session->set_request_response(@enoid)) {
		$response = $session->pdu_buffer;
		($bindings) = $session->decode_get_response ($response);
		$session->close ();
		while ($bindings) {
			($binding,$bindings) = decode_sequence ($bindings);
			($oid,$value) = decode_by_template ($binding, "%O%@");
			my $tempo = pretty_print($value);
			$tempo=~s/\t/ /g;
			$tempo=~s/\n/ /g;
			$tempo=~s/^\s+//;
			$tempo=~s/\s+$//;
			push @retvals,  $tempo;
		}
		return (@retvals);
	} else {
		return (-1,-1);
	}
}
sub toOID {
	my $var = shift;
	if ($var =~ /^([a-z]+[^\.]*)/i) {
		my $oid = $OIDS{$1};
		if ($oid) {
			$var =~ s/$1/$oid/;
		} else {
			die "Unknown SNMP var $var\n"
		}
	}
	encode_oid((split /\./, $var));
}
