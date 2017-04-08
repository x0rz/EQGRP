#!/bin/sh
. /etc/rc.d/init.d/functions
INIT_VERSION=sysvinit-2.78 previous=N TERM=linux HOSTTYPE=i386 PATH=/sbin:/usr/sbin:/bin:/usr/bin:/usr/X11R6/bin CONSOLE=/dev/console HOME=/ PREVLEVEL=N RUNLEVEL=5 SHELL=/bin/bash runlevel=5 AUTOBOOT=YES BOOT_IMAGE=linux OSTYPE=Linux SHLVL=1 _=/bin/nice daemon rpc.statd
