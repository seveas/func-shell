#!/usr/bin/fsh
#
# Update HP snmp agents on all G7 hardwars

+ *

@dmidecode -s system-product-name

# We only want G7
- $failed
= x[1] =~ /G7/

yum update hp-health hp-snmp-agents
