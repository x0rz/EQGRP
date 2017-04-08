#!/usr/bin/env perl
$VER="1.0.0.1" ;
$i=0;
if (@ARGV) {
	foreach (@ARGV) {
		if (@ARGV[$i] eq "-h") {
 			print "\n 
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #
  # Usage: auditcleaner [audit.log location] [-f] (If not specified will look for audit.log from where is was ran.)
  # Usage: auditcleaner -h 	(Gets this help)
  # Usage: auditcleaner -f	(Tells it to output lines ready for use on target)
  # Version ${VER}
  # # # # # 
  #
  # Auditcleaner will generate SED lines to clean audit.log files.
  #
  # The following MUST be done:
  # 
  # A.	You must get the audit.log from target or a portion of it to be the sample.
  # B.	Find your dirty lines from the audit.log and enter them via STDIN when prompted.
  #
  # # # # # 
  #
  # It will automatically pull valid crond session lines from a sample file.
  # The sample file can be entered on command line when calling the script or will by default use \"audit.log\" from where the script was ran.
  # With these sample lines it will generate pastables for the dirty lines entered via STDIN.
  #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

"			;
			exit;
		}
		$i++;
	}
	$i=0;
	foreach (@ARGV) {
		if (@ARGV[$i] eq "-f") {
			$final="/var/log/audit/audit.log";
		}
		$i++;
	}
	$i=0;
	foreach (@ARGV) {
		if (@ARGV[$i] ne "-f" ) {
			$filename=@ARGV[$i];
		} 
		$i++;
	}
} 
if ($filename) {
}else {
$filename ="audit.log";
}
print "Using this file to pull the template lines from: $filename\n";
my $pidline =`grep cron $filename | tail -5 | head -1`;
my ( $pid ) = ( $pidline =~ /\suser pid=(\d+)/) ;
my @good_lines =`grep "pid=$pid" $filename`;
@good_lines_count = @good_lines;
$good_lines_count = scalar(@good_lines_count)."";
$s=5;
$j=0;
while ($good_lines_count != 6 ) {
	$s=$s + 10;
	my $pidline =`grep cron $filename | tail -$s | head -1`;
	( $pid ) = ( $pidline =~ /\suser pid=(\d+)/) ;
	@good_lines =`grep pid=$pid $filename`;
	@good_lines_count = @good_lines;
	$good_lines_count = scalar(@good_lines_count)."";
	$j++;
	if ( $j > 5 ) {
		print "\n\n The sample data did not provide good lines. \n 	Please get more data and try again. \n\n\n ";
		exit;
	}
}
$i=0;
$k=0; 
 foreach $goodlines (@good_lines){
 	if ( @good_lines[$i] =~ /(.*new ses=\d+)/) {
 	$session_line = @good_lines[$i];
 	} else {
 	(@replace_lines[$k]) = @good_lines[$i];
	$k++;
	}
 $i++;
 }
print "\nPlease paste the bad lines that need to be cleaned. \n Press Ctrl <D> after last line is entered. .\n\n";
my @bad_lines =<STDIN>; 
print "\n \n     # # # # #     Working     # # # # #     \n\n";
sleep 1;
@bad_lines_count = @bad_lines;
$bad_lines_count = scalar(@bad_lines_count)."";
$i=0;
$j=0;
$k=0; 
$l=0;
 foreach $bad_lines (@bad_lines){
 	if ( @bad_lines[$i] =~ /(.*new ses=\d+)/) {
 	 @bad_lines_ses[$j]= @bad_lines[$i];
	$j++
 	} elsif ( @bad_lines[$i] =~ /(^$)/) {
	(@bad_lines_blank[$l]) = @bad_lines[$i];
	$l++;
	} else {
 	(@bad_lines_std[$k]) = @bad_lines[$i];
	$k++;
	}
 $i++;
 }
@bad_lines_count_ses = @bad_lines_ses;
$bad_lines_count_ses = scalar(@bad_lines_count_ses)."";
@bad_lines_count_std = @bad_lines_std;
$bad_lines_count_std = scalar(@bad_lines_count_std)."";
@bad_lines_blank_count = @bad_lines_blank;
$bad_lines_blank_count = scalar(@bad_lines_blank_count)."";
if ($bad_lines_count != $bad_lines_count_ses + $bad_lines_count_std + $bad_lines_blank_count) {
	die "Math doesnt line up";
}
if ($good_lines_count <  $bad_lines_count ) {
	$line_count_diff= ($bad_lines_count_ses + $bad_lines_count_std)  - $good_lines_count ;
	print "\nThere were $line_count_diff extra bad lines. Additional lines were generated.\n";
}
$i=0;
foreach $bad_pid_ses (@bad_lines_ses){
	( @bad_ses_pid[$i] ) = ( $bad_pid_ses =~ /\slogin pid=(\d+)/) ;
	$i++;
}
$i=0;
foreach $bad_pid_std (@bad_lines_std){
	( @bad_std_pid[$i] ) = ( $bad_pid_std =~ /\suser pid=(\d+)/) ;
	$i++;
}
$i = 0;
$bad_lines_count_std_diff = $bad_lines_count_std -5 ;
until ($i eq $bad_lines_count_std_diff) {
	$k=$i+5;
	@replace_lines[$k] = @replace_lines[$i];
	$i++;
}
$i = 0;
foreach $replace_lines (@replace_lines) {
	(@template_std_1[$i],@template_std_time[$i],@template_std_2[$i]) = split(/(\d*.\d\d\d:\d*)/, "$replace_lines" );
	$i++;
}
$i=0;
until ($i eq $bad_lines_count_ses) {
	@session_line[$i] = $session_line;
	$i++;
}
$i=0;
foreach $session_line (@session_line) {
	(@template_ses_1[$i],@template_ses_time[$i],@template_ses_2[$i]) = split(/(\d*.\d\d\d:\d*)/, "$session_line" );
	(@template_ses_2_a[$i],@template_ses_id[$i]) = split(/new ses=/, "@template_ses_2[$i]" );
	$i++;
}
$i = 0;
foreach $bad_lines_std (@bad_lines_std) {
	(@bad_std_1[$i],@replace_std_time[$i],@bad_std_2[$i] ) = split(/(\d*.\d\d\d:\d*)/, "$bad_lines_std");
	$i++;
}
$i=0;
foreach   (@template_std_2) {
	$_ = @template_std_2[$i];
	s/"/\\"/g;
	@template_std_2[$i] = $_;
	$i++;
}
$i=0;
foreach  $bad_std_pid (@bad_std_pid) {
	$_ = @template_std_2[$i];
	s/$pid/$bad_std_pid/g;
	@template_std_2[$i] = $_;
	$i++;
}
$i = 0;
foreach $bad_lines_ses (@bad_lines_ses) {
	(@bad_ses_1[$i],@replace_ses_time[$i],@bad_ses_2[$i]) = split(/(\d*.\d\d\d:\d*)/, "$bad_lines_ses" );
	(@bad_ses_2_a[$i],@bad_ses_id[$i]) = split(/new ses=/, "@bad_ses_2[$i]" );
	$i++;
}
$sed1='sed -e "s#^.*\(';
$sed2='\).*\$#';
$sed3='#g" | \\';
$sed4='new ses=';
$sed5='#g" > n ; \\';
$i = 0;
foreach (@bad_ses_id){
	chomp @bad_ses_id[$i];
	@sed_ses_line[$i]="$sed1@replace_ses_time[$i]$sed2@template_ses_1[$i]\\1@template_ses_2_a[$i]$sed4@bad_ses_id[$i]$sed3\n";
	$i++;
}
$i = 0;
foreach (@replace_std_time){
	chomp @template_std_2[$i];
	if ($i < ($bad_lines_count_std -1 )) {
		@sed_std_line[$i]="$sed1@replace_std_time[$i]$sed2@template_std_1[$i]\\1@template_std_2[$i]$sed3\n";
		$i++;
		} else {
		@sed_std_line[$i]="$sed1@replace_std_time[$i]$sed2@template_std_1[$i]\\1@template_std_2[$i]$sed5\n";
	}
}
print "\n#######################################\nCommands generated to test locally. You MUST test first locally.\n#######################################\n\n";
$i=0;
print "cp audit.log o ; cat o | \\\n";
foreach (@sed_ses_line) {
	print "@sed_ses_line[$i]";
	$i++
}
$i=0;
foreach (@sed_std_line) {
	print "@sed_std_line[$i]";
	$i++
}
print "diff audit.log n ; #cat n > audit.log\n";
print "\n#######################################\n";
if ($final) {
	print "Final Commands generated to run on target. \n#######################################\n";
	print "
-get /var/log/audit/audit.log
-shell
unset HISTFILE
unset HISTSIZE
unset HISTFILESIZE

 ";
	print "cp $final o ; cat o | \\\n";
	$i=0;
	foreach (@sed_ses_line) {
		print "@sed_ses_line[$i]";
		$i++
	}
	## Print std lines
	$i=0;
	foreach (@sed_std_line) {
		print "@sed_std_line[$i]";
		$i++
	}
	
	print "diff $final n ; cat n > $final\n";
	print "\n#######################################\n\n";
} else {
print "Will need to mod those lines to run on target or run this again with \"-f\" option.\n\n";
}
