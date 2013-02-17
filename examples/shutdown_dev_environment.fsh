#!/usr/bin/fsh
#
# This shuts down all dev servers where no people have interactive sessions

+ *devapp*;*devdb*

@who

# who always returns 0, so check for non-empty output
- x[1] =~ /../

# Of course you first do a dryrun, then you uncomment the last line :-)
=
#shutdown -h now
