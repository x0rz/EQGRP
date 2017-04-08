# .bashrc

# User specific aliases and functions

alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi
stty erase ^?


alias scriptme='cd /current/down;  SCRIPTME=2 /usr/bin/script -af script.$$'

##add for all the xterm aliases a scriptme option
alias s1x='SCRIPTME=1 1x'
alias s1xs='SCRIPTME=1 1xs'
alias s1xw='SCRIPTME=1 1xw'
alias s2x='SCRIPTME=1 2x'
alias s2xs='SCRIPTME=1 2xs'
alias s2xw='SCRIPTME=1 2xw'
alias s3x='SCRIPTME=1 3x'
alias s3xs='SCRIPTME=1 3xs'
alias s3xw='SCRIPTME=1 3xw'
alias s4x='SCRIPTME=1 4x'
alias s4xs='SCRIPTME=1 4xs'
alias s4xw='SCRIPTME=1 4xw'

##myenv directly embedded, no longer need to set DISPLAY, also hardcoded to /current instead of /home/black/tmp
if [ ${SCRIPTME:-0} == 2 ]; then
        export SCRIPTME=0
        cd /current/bin
        PS1="\t \h \w> "
        export NHOME=/current
        PATH=/usr/java/jre1.6.0_03/bin:/home/black/tmp/20120914-1311/bin:/usr/local/sbin:/usr/local/bin:/bin:/usr/bin:/sbin:/usr/sbin:/opt/ActivePerl-5.10/site/bin:/opt/ActivePerl-5.10/bin:/usr/src/firefox:/current/bin:/current/op2/bin:/current/op3/bin:/usr/X11R6/bin:/usr/games:/root/bin
        export PS1 PATH; date; pwd; uname -a; netstat -rn ; ifconfig -a ; env | grep PATH
fi

if [ ${SCRIPTME:-0} == 1 ]; then
        export SCRIPTME=2
        cd /current/down
        /usr/bin/script -af script.$$
fi

