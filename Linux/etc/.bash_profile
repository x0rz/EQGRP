
export PATH=/usr/local/bin:/bin:/usr/bin:/sbin:/usr/sbin

if [ -f ~/.bashrc ] ; then
	source ~/.bashrc

fi

# Now started by gnome at login
#if [ ! -f /var/lock/op_prepped ] ; then
#	if [ -x /root/op_prep.py ] ; then
#		xterm -bg white -fg black -geometry 84x45+0+0 -hold -e /root/op_prep.py
#	fi
#	touch /var/lock/op_prepped
#fi
