#!/bin/sh
. /etc/rc.d/init.d/functions
INIT_VERSION=sysvinit-2.74 previous=N TERM=linux HOSTTYPE=i386 PATH=/sbin:/usr/sbin:/bin:/usr/bin:/usr/X11R6/bin CONSOLE=/dev/console HOME=/ PREVLEVEL=N RUNLEVEL=3 SHELL=/bin/bash runlevel=3 AUTOBOOT=YES BOOT_IMAGE=linux OSTYPE=Linux SHLVL=2 _=/bin/nice daemon rpc.statd
