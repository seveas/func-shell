#!/usr/bin/fsh
#
# Find out what a user who is leaving is still running and kill it.
#
# This one was actually not scripted up, but done in an interactive shell,
# checking each step. This is the cleaned up shell session with a different
# loginname.

+ *

# First find the user
@ps -u dkaarsemaker
= [x for x in last_ok]
ps -u dkaarsemaker

# Ok, there are some perl scripts to kill
killall -u dkaarsemaker perl

# And all applications on gateway hosts
= *gateway*
@ps -u dkaarsemaker
= $ok
killall -u dkaarsemaker
