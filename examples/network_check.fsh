#!/usr/bin/fsh
#
# Check whether certain holes in the firewall exist, report failing IP addresses

+ appserver-*
nc -w3 -vz databaseserver1.int.kaarsemaker.net
- $ok
ip a l eth0 | grep "inet "
