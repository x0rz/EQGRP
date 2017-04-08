### -*- mode: Perl -*-
######################################################################
### BER (Basic Encoding Rules) encoding and decoding.
######################################################################
### Copyright (c) 1995-2000, Simon Leinen.
###
### This program is free software; you can redistribute it under the
### "Artistic License" included in this distribution (file "Artistic").
######################################################################
### This module implements encoding and decoding of ASN.1-based data
### structures using the Basic Encoding Rules (BER).  Only the subset
### necessary for SNMP is implemented.
######################################################################
### Created by:  Simon Leinen  <simon@switch.ch>
###
### Contributions and fixes by:
###
### Andrzej Tobola <san@iem.pw.edu.pl>:  Added long String decode
### Tobias Oetiker <oetiker@ee.ethz.ch>:  Added 5 Byte Integer decode ...
### Dave Rand <dlr@Bungi.com>:  Added SysUpTime decode
### Philippe Simonet <sip00@vg.swissptt.ch>:  Support larger subids
### Yufang HU <yhu@casc.com>:  Support even larger subids
### Mike Mitchell <mcm@unx.sas.com>: New generalized encode_int()
### Mike Diehn <mdiehn@mindspring.net>: encode_ip_address()
### Rik Hoorelbeke <rik.hoorelbeke@pandora.be>: encode_oid() fix
### Brett T Warden <wardenb@eluminant.com>: pretty UInteger32
######################################################################

package BER;

require 5.002;

use strict;
use vars qw(@ISA @EXPORT $VERSION $pretty_print_timeticks $errmsg);
use Exporter;

$VERSION = '0.86';

@ISA = qw(Exporter);

@EXPORT = qw(context_flag constructor_flag
	     encode_int encode_int_0 encode_null encode_oid
	     encode_sequence encode_tagged_sequence
	     encode_string encode_ip_address encode_timeticks
	     encode_uinteger32 encode_counter32 encode_counter64
	     encode_gauge32 
	     decode_sequence decode_by_template
	     pretty_print pretty_print_timeticks
	     hex_string hex_string_of_type
	     encoded_oid_prefix_p errmsg);

### Variables

## Bind this to zero if you want to avoid that TimeTicks are converted
## into "human readable" strings containing days, hours, minutes and
## seconds.
##
## If the variable is zero, pretty_print will simply return an
## unsigned integer representing hundredths of seconds.
##
$pretty_print_timeticks = 1;

### Prototypes
sub encode_header ($$);
sub encode_int_0 ();
sub encode_int ($);
sub encode_oid (@);
sub encode_null ();
sub encode_sequence (@);
sub encode_tagged_sequence ($@);
sub encode_string ($);
sub encode_ip_address ($);
sub encode_timeticks ($);
sub pretty_print ($);
sub pretty_using_decoder ($$);
sub pretty_string ($);
sub pretty_intlike ($);
sub pretty_unsignedlike ($);
sub pretty_oid ($);
sub pretty_uptime ($);
sub pretty_uptime_value ($);
sub pretty_ip_address ($);
sub hex_string ($);
sub hex_string_of_type ($$);
sub decode_oid ($);
sub decode_by_template;
sub decode_by_template_2;
sub decode_sequence ($);
sub decode_int ($);
sub decode_intlike ($);
sub decode_unsignedlike ($);
sub decode_intlike_s ($$);
sub decode_string ($);
sub decode_length ($);
sub encoded_oid_prefix_p ($$);
sub decode_subid ($$$);
sub error (@);
sub template_error ($$$);

sub version () { $VERSION; }

### Flags for different types of tags

sub universal_flag	{ 0x00 }
sub application_flag	{ 0x40 }
sub context_flag	{ 0x80 }
sub private_flag	{ 0xc0 }

sub primitive_flag	{ 0x00 }
sub constructor_flag	{ 0x20 }

### Universal tags

sub boolean_tag		{ 0x01 }
sub int_tag		{ 0x02 }
sub bit_string_tag	{ 0x03 }
sub octet_string_tag	{ 0x04 }
sub null_tag		{ 0x05 }
sub object_id_tag	{ 0x06 }
sub sequence_tag	{ 0x10 }
sub set_tag		{ 0x11 }
sub uptime_tag		{ 0x43 }

### Flag for length octet announcing multi-byte length field

sub long_length		{ 0x80 }

### SNMP specific tags

sub snmp_ip_address_tag		{ 0x00 | application_flag }
sub snmp_counter32_tag		{ 0x01 | application_flag }
sub snmp_gauge32_tag		{ 0x02 | application_flag }
sub snmp_timeticks_tag		{ 0x03 | application_flag }
sub snmp_opaque_tag		{ 0x04 | application_flag }
sub snmp_nsap_address_tag	{ 0x05 | application_flag }
sub snmp_counter64_tag		{ 0x06 | application_flag }
sub snmp_uinteger32_tag		{ 0x07 | application_flag }

#### Encoding

sub encode_header ($$) {
    my ($type,$length) = @_;
    return pack ("C C", $type, $length) if $length < 128;
    return pack ("C C C", $type, long_length | 1, $length) if $length < 256;
    return pack ("C C n", $type, long_length | 2, $length) if $length < 65536;
    return error ("Cannot encode length $length yet");
}

sub encode_int_0 () {
    return pack ("C C C", 2, 1, 0);
}

sub encode_int ($) {
    return encode_intlike ($_[0], int_tag);
}

sub encode_uinteger32 ($) {
    return encode_intlike ($_[0], snmp_uinteger32_tag);
}

sub encode_counter32 ($) {
    return encode_intlike ($_[0], snmp_counter32_tag);
}

sub encode_counter64 ($) {
    return encode_intlike ($_[0], snmp_counter64_tag);
}

sub encode_gauge32 ($) {
    return encode_intlike ($_[0], snmp_gauge32_tag);
}

sub encode_intlike ($$) {
    my ($int, $tag)=@_;
    my ($sign, $val, @vals);
    $sign = ($int >= 0) ? 0 : 0xff;
    if (ref $int && $int->isa ("Math::BigInt")) {
	for(;;) {
	    $val = $int->bmod (256);
	    unshift(@vals, $val);
	    return encode_header ($tag, $#vals + 1).pack ("C*", @vals)
		if ($int >= -128 && $int < 128);
	    $int = $int - $sign;
	    $int = $int / 256;
	}
    } else {
	for(;;) {
	    $val = $int & 0xff;
	    unshift(@vals, $val);
	    return encode_header ($tag, $#vals + 1).pack ("C*", @vals)
		if ($int >= -128 && $int < 128);
	    $int -= $sign;
	    $int = int($int / 256);
	}
    }
}

sub encode_oid (@) {
    my @oid = @_;
    my ($result,$subid);

    $result = '';
    ## Ignore leading empty sub-ID.  The favourite reason for
    ## those to occur is that people cut&paste numeric OIDs from
    ## CMU/UCD SNMP including the leading dot.
    shift @oid if $oid[0] eq '';

    return error ("Object ID too short: ", join('.',@oid))
	if $#oid < 1;
    ## The first two subids in an Object ID are encoded as a single
    ## byte in BER, according to a funny convention.  This poses
    ## restrictions on the ranges of those subids.  In the past, I
    ## didn't check for those.  But since so many people try to use
    ## OIDs in CMU/UCD SNMP's format and leave out the mib-2 or
    ## enterprises prefix, I introduced this check to catch those
    ## errors.
    ##
    return error ("first subid too big in Object ID ", join('.',@oid))
	if $oid[0] > 2;
    $result = shift (@oid) * 40;
    $result += shift @oid;
    return error ("second subid too big in Object ID ", join('.',@oid))
	if $result > 255;
    $result = pack ("C", $result);
    foreach $subid (@oid) {
	if ( ($subid>=0) && ($subid<128) ){ #7 bits long subid 
	    $result .= pack ("C", $subid);
	} elsif ( ($subid>=128) && ($subid<16384) ){ #14 bits long subid
	    $result .= pack ("CC", 0x80 | $subid >> 7, $subid & 0x7f);
	} 
	elsif ( ($subid>=16384) && ($subid<2097152) ) {#21 bits long subid
	    $result .= pack ("CCC",
			     0x80 | (($subid>>14) & 0x7f), 
			     0x80 | (($subid>>7) & 0x7f),
			     $subid & 0x7f); 
	} elsif ( ($subid>=2097152) && ($subid<268435456) ){ #28 bits long subid
	    $result .= pack ("CCCC", 
			     0x80 | (($subid>>21) & 0x7f),
			     0x80 | (($subid>>14) & 0x7f),
			     0x80 | (($subid>>7) & 0x7f),
			     $subid & 0x7f);
	} elsif ( ($subid>=268435456) && ($subid<4294967296) ){ #32 bits long subid
	    $result .= pack ("CCCCC", 
			     0x80 | (($subid>>28) & 0x0f), #mask the bits beyond 32 
			     0x80 | (($subid>>21) & 0x7f),
			     0x80 | (($subid>>14) & 0x7f),
			     0x80 | (($subid>>7) & 0x7f),
			     $subid & 0x7f);
	} else {
	    return error ("Cannot encode subid $subid");
	}
    }
    encode_header (object_id_tag, length $result).$result;
}

sub encode_null () { encode_header (null_tag, 0); }
sub encode_sequence (@) { encode_tagged_sequence (sequence_tag, @_); }

sub encode_tagged_sequence ($@) {
    my ($tag,$result);

    $tag = shift @_;
    $result = join '',@_;
    return encode_header ($tag | constructor_flag, length $result).$result;
}

sub encode_string ($) {
    my ($string)=@_;
    return encode_header (octet_string_tag, length $string).$string;
}

sub encode_ip_address ($) {
    my ($addr)=@_;
    my @octets;

    if (length $addr == 4) {
      ## Four bytes... let's suppose that this is a binary IP address
      ## in network byte order.
      return encode_header (snmp_ip_address_tag, length $addr).$addr;
    } elsif (@octets = ($addr =~ /^([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)$/)) {
      return encode_ip_address (pack ("CCCC", @octets));
    } else {
      return error ("IP address must be four bytes long or a dotted-quad");
    }
}

sub encode_timeticks ($) {
  my ($tt) = @_;
  return encode_intlike ($tt, snmp_timeticks_tag);
}

#### Decoding

sub pretty_print ($) {
    my ($packet) = @_;
    my ($type,$rest);
    return undef unless defined $packet;
    my $result = ord (substr ($packet, 0, 1));
    return pretty_intlike ($packet)
	if $result == int_tag;
    return pretty_unsignedlike ($packet)
	if $result == snmp_counter32_tag
	    || $result == snmp_gauge32_tag
	    || $result == snmp_counter64_tag
	    || $result == snmp_uinteger32_tag;
    return pretty_string ($packet) if $result == octet_string_tag;
    return pretty_oid ($packet) if $result == object_id_tag;
    return ($pretty_print_timeticks
	    ? pretty_uptime ($packet)
	    : pretty_unsignedlike ($packet))
	if $result == uptime_tag;
    return pretty_ip_address ($packet) if $result == snmp_ip_address_tag;
    return "(null)" if $result == null_tag;
    return sprintf("#<unprintable BER type 0x%x>", $result);
}

sub pretty_using_decoder ($$) {
    my ($decoder, $packet) = @_;
    my ($decoded,$rest);
    ($decoded,$rest) = &$decoder ($packet);
    return error ("Junk after object") unless $rest eq '';
    return $decoded;
}

sub pretty_string ($) {
    pretty_using_decoder (\&decode_string, $_[0]);
}

sub pretty_intlike ($) {
    my $decoded = pretty_using_decoder (\&decode_intlike, $_[0]);
    $decoded;
}

sub pretty_unsignedlike ($) {
    return pretty_using_decoder (\&decode_unsignedlike, $_[0]);
}

sub pretty_oid ($) {
    my ($oid) = shift;
    my ($result,$subid,$next);
    my (@oid);
    $result = ord (substr ($oid, 0, 1));
    return error ("Object ID expected") unless $result == object_id_tag;
    ($result, $oid) = decode_length (substr ($oid, 1));
    return error ("inconsistent length in OID") unless $result == length $oid;
    @oid = ();
    $subid = ord (substr ($oid, 0, 1));
    push @oid, int ($subid / 40);
    push @oid, $subid % 40;
    $oid = substr ($oid, 1);
    while ($oid ne '') {
	$subid = ord (substr ($oid, 0, 1));
	if ($subid < 128) {
	    $oid = substr ($oid, 1);
	    push @oid, $subid;
	} else {
	    $next = $subid;
	    $subid = 0;
	    while ($next >= 128) {
		$subid = ($subid << 7) + ($next & 0x7f);
		$oid = substr ($oid, 1);
		$next = ord (substr ($oid, 0, 1));
	    }
	    $subid = ($subid << 7) + $next;
	    $oid = substr ($oid, 1);
	    push @oid, $subid;
	}
    }
    join ('.', @oid);
}

sub pretty_uptime ($) {
    my ($packet,$uptime);

    ($uptime,$packet) = &decode_unsignedlike (@_);
    pretty_uptime_value ($uptime);
}

sub pretty_uptime_value ($) {
    my ($uptime) = @_;
    my ($seconds,$minutes,$hours,$days,$result);
    ## We divide the uptime by hundred since we're not interested in
    ## sub-second precision.
    $uptime = int ($uptime / 100);

    $days = int ($uptime / (60 * 60 * 24));
    $uptime %= (60 * 60 * 24);

    $hours = int ($uptime / (60 * 60));
    $uptime %= (60 * 60);

    $minutes = int ($uptime / 60);
    $seconds = $uptime % 60;

    if ($days == 0){
	$result = sprintf ("%d:%02d:%02d", $hours, $minutes, $seconds);
    } elsif ($days == 1) {
	$result = sprintf ("%d day, %d:%02d:%02d", 
			   $days, $hours, $minutes, $seconds);
    } else {
	$result = sprintf ("%d days, %d:%02d:%02d", 
			   $days, $hours, $minutes, $seconds);
    }
    return $result;
}


sub pretty_ip_address ($) {
    my $pdu = shift;
    my ($length, $rest);
    return error ("IP Address tag (".snmp_ip_address_tag.") expected")
	unless ord (substr ($pdu, 0, 1)) == snmp_ip_address_tag;
    $pdu = substr ($pdu, 1);
    ($length,$pdu) = decode_length ($pdu);
    return error ("Length of IP address should be four")
	unless $length == 4;
    sprintf "%d.%d.%d.%d", unpack ("CCCC", $pdu);
}

sub hex_string ($) {
    &hex_string_of_type ($_[0], octet_string_tag);
}

sub hex_string_of_type ($$) {
    my ($pdu, $wanted_type) = @_;
    my ($length);
    return error ("BER tag ".$wanted_type." expected")
	unless ord (substr ($pdu, 0, 1)) == $wanted_type;
    $pdu = substr ($pdu, 1);
    ($length,$pdu) = decode_length ($pdu);
    hex_string_aux ($pdu);
}

sub hex_string_aux ($) {
    my ($binary_string) = @_;
    my ($c, $result);
    $result = '';
    for $c (unpack "C*", $binary_string) {
	$result .= sprintf "%02x", $c;
    }
    $result;
}

sub decode_oid ($) {
    my ($pdu) = @_;
    my ($result,$pdu_rest);
    my (@result);
    $result = ord (substr ($pdu, 0, 1));
    return error ("Object ID expected") unless $result == object_id_tag;
    ($result, $pdu_rest) = decode_length (substr ($pdu, 1));
    @result = (substr ($pdu, 0, $result + (length ($pdu) - length ($pdu_rest))),
	       substr ($pdu_rest, $result));
    @result;
}

sub decode_by_template {
    my ($pdu) = shift;
    local ($_) = shift;
    return decode_by_template_2 ($pdu, $_, 0, 0, @_);
}

my $template_debug = 0;

sub decode_by_template_2 {
    my ($pdu, $template, $pdu_index, $template_index);
    local ($_);
    $pdu = shift;
    $template = $_ = shift;
    $pdu_index = shift;
    $template_index = shift;
    my (@results);
    my ($length,$expected,$read,$rest);
    while (0 < length ($_)) {
	if (substr ($_, 0, 1) eq '%') {
	    print STDERR "template $_ ", length $pdu," bytes remaining\n"
		if $template_debug;
	    $_ = substr ($_,1);
	    ++$template_index;
	    if (($expected) = /^(\d*|\*)\{(.*)/) {
		## %{
		$template_index += length ($expected) + 1;
		print STDERR "%{\n" if $template_debug;
		$_ = $2;
		$expected = shift | constructor_flag if ($expected eq '*');
		$expected = sequence_tag | constructor_flag
		    if $expected eq '';
		return template_error ("Expected sequence tag $expected, got ".
				       ord (substr ($pdu, 0, 1)),
				      $template,
				      $template_index)
		    unless (ord (substr ($pdu, 0, 1)) == $expected);
		$pdu = substr ($pdu,1);
		(($length,$pdu) = decode_length ($pdu))
		    || return template_error ("cannot read length",
					      $template, $template_index);
		return template_error ("Expected length $length, got ".length $pdu ,
				      $template, $template_index)
		  unless length $pdu == $length;
	    } elsif (($expected,$rest) = /^(\*|)s(.*)/) {
		## %s
		$template_index += length ($expected) + 1;
		($expected = shift) if $expected eq '*';
		(($read,$pdu) = decode_string ($pdu))
		    || return template_error ("cannot read string",
					      $template, $template_index);
		print STDERR "%s => $read\n" if $template_debug;
		if ($expected eq '') {
		    push @results, $read;
		} else {
		    return template_error ("Expected $expected, read $read",
					   $template, $template_index)
			unless $expected eq $read;
		}
		$_ = $rest;
	    } elsif (($rest) = /^A(.*)/) {
		## %A
		$template_index += 1;
		{
		    my ($tag, $length, $value);
		    $tag = ord (substr ($pdu, 0, 1));
		    return error ("Expected IP address, got tag ".$tag)
			unless $tag == snmp_ip_address_tag;
		    ($length, $pdu) = decode_length (substr ($pdu, 1));
		    return template_error ("IP address must be four bytes long",
					   $template, $template_index)
			unless $length == 4;
		    $read = substr ($pdu, 0, $length);
		    $pdu = substr ($pdu, $length);
		}
		print STDERR "%A => $read\n" if $template_debug;
		push @results, $read;
		$_ = $rest;
	    } elsif (/^O(.*)/) {
		## %O
		$template_index += 1;
		$_ = $1;
		(($read,$pdu) = decode_oid ($pdu))
		  || return template_error ("cannot read OID",
					    $template, $template_index);
		print STDERR "%O => ".pretty_oid ($read)."\n"
		    if $template_debug;
		push @results, $read;
	    } elsif (($expected,$rest) = /^(\d*|\*|)i(.*)/) {
		## %i
		$template_index += length ($expected) + 1;
		print STDERR "%i\n" if $template_debug;
		$_ = $rest;
		(($read,$pdu) = decode_int ($pdu))
		  || return template_error ("cannot read int",
					    $template, $template_index);
		if ($expected eq '') {
		    push @results, $read;
		} else {
		    $expected = int (shift) if $expected eq '*';
		    return template_error (sprintf ("Expected %d (0x%x), got %d (0x%x)",
						    $expected, $expected, $read, $read),
					   $template, $template_index)
			unless ($expected == $read)
		}
	    } elsif (($rest) = /^u(.*)/) {
		## %u
		$template_index += 1;
		print STDERR "%u\n" if $template_debug;
		$_ = $rest;
		(($read,$pdu) = decode_unsignedlike ($pdu))
		  || return template_error ("cannot read uptime",
					    $template, $template_index);
		push @results, $read;
	    } elsif (/^\@(.*)/) {
		## %@
		$template_index += 1;
		print STDERR "%@\n" if $template_debug;
		$_ = $1;
		push @results, $pdu;
		$pdu = '';
	    } else {
		return template_error ("Unknown decoding directive in template: $_",
				       $template, $template_index);
	    }
	} else {
	    if (substr ($_, 0, 1) ne substr ($pdu, 0, 1)) {
		return template_error ("Expected ".substr ($_, 0, 1).", got ".substr ($pdu, 0, 1),
				       $template, $template_index);
	    }
	    $_ = substr ($_,1);
	    $pdu = substr ($pdu,1);
	}
    }
    return template_error ("PDU too long", $template, $template_index)
      if length ($pdu) > 0;
    return template_error ("PDU too short", $template, $template_index)
      if length ($_) > 0;
    @results;
}

sub decode_sequence ($) {
    my ($pdu) = @_;
    my ($result);
    my (@result);
    $result = ord (substr ($pdu, 0, 1));
    return error ("Sequence expected") unless $result == sequence_tag | constructor_flag;
    ($result, $pdu) = decode_length (substr ($pdu, 1));
    @result = (substr ($pdu, 0, $result), substr ($pdu, $result));
    @result;
}

sub decode_int ($) {
    my ($pdu) = @_;
    my $tag = ord (substr ($pdu, 0, 1));
    return error ("Integer expected, found tag ".$tag)
	unless $tag == int_tag;
    decode_intlike ($pdu);
}

sub decode_intlike ($) {
    decode_intlike_s ($_[0], 1);
}

sub decode_unsignedlike ($) {
    decode_intlike_s ($_[0], 0);
}

my $have_math_bigint_p = 0;

sub decode_intlike_s ($$) {
    my ($pdu, $signedp) = @_;
    my ($length,$result);
    $length = ord (substr ($pdu, 1, 1));
    my $ptr = 2;
    $result = unpack ($signedp ? "c" : "C", substr ($pdu, $ptr++, 1));
    if ($length > 5 || ($length == 5 && $result > 0)) {
	require 'Math/BigInt.pm' unless $have_math_bigint_p++;
	$result = new Math::BigInt ($result);
    }
    while (--$length > 0) {
	$result *= 256;
	$result += unpack ("C", substr ($pdu, $ptr++, 1));
    }
    ($result, substr ($pdu, $ptr));
}

sub decode_string ($) {
    my ($pdu) = shift;
    my ($result);
    $result = ord (substr ($pdu, 0, 1));
    return error ("Expected octet string, got tag ".$result)
	unless $result == octet_string_tag;
    ($result, $pdu) = decode_length (substr ($pdu, 1));
    return (substr ($pdu, 0, $result), substr ($pdu, $result));
}

sub decode_length ($) {
    my ($pdu) = shift;
    my ($result);
    my (@result);
    $result = ord (substr ($pdu, 0, 1));
    if ($result & long_length) {
	if ($result == (long_length | 1)) {
	    @result = (ord (substr ($pdu, 1, 1)), substr ($pdu, 2));
	} elsif ($result == (long_length | 2)) {
	    @result = ((ord (substr ($pdu, 1, 1)) << 8)
		       + ord (substr ($pdu, 2, 1)), substr ($pdu, 3));
	} else {
	    return error ("Unsupported length");
	}
    } else {
	@result = ($result, substr ($pdu, 1));
    }
    @result;
}

#### OID prefix check

### encoded_oid_prefix_p OID1 OID2
###
### OID1 and OID2 should be BER-encoded OIDs.
### The function returns non-zero iff OID1 is a prefix of OID2.
### This can be used in the termination condition of a loop that walks
### a table using GetNext or GetBulk.
###
sub encoded_oid_prefix_p ($$) {
    my ($oid1, $oid2) = @_;
    my ($i1, $i2);
    my ($l1, $l2);
    my ($subid1, $subid2);
    return error ("OID tag expected") unless ord (substr ($oid1, 0, 1)) == object_id_tag;
    return error ("OID tag expected") unless ord (substr ($oid2, 0, 1)) == object_id_tag;
    ($l1,$oid1) = decode_length (substr ($oid1, 1));
    ($l2,$oid2) = decode_length (substr ($oid2, 1));
    for ($i1 = 0, $i2 = 0;
	 $i1 < $l1 && $i2 < $l2;
	 ++$i1, ++$i2) {
	($subid1,$i1) = &decode_subid ($oid1, $i1, $l1);
	($subid2,$i2) = &decode_subid ($oid2, $i2, $l2);
	return 0 unless $subid1 == $subid2;
    }
    return $i2 if $i1 == $l1;
    return 0;
}

### decode_subid OID INDEX
###
### Decodes a subid field from a BER-encoded object ID.
### Returns two values: the field, and the index of the last byte that
### was actually decoded.
###
sub decode_subid ($$$) {
    my ($oid, $i, $l) = @_;
    my $subid = 0;
    my $next;

    while (($next = ord (substr ($oid, $i, 1))) >= 128) {
	$subid = ($subid << 7) + ($next & 0x7f);
	++$i;
	return error ("decoding object ID: short field")
	    unless $i < $l;
    }
    return (($subid << 7) + $next, $i);
}

sub error (@) {
  $errmsg = join ("",@_);
  return undef;
}

sub template_error ($$$) {
  my ($errmsg, $template, $index) = @_;
  return error ($errmsg."\n  ".$template."\n  ".(' ' x $index)."^");
}

1;
