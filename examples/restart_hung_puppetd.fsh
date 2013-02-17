#!/usr/bin/fsh
#
# Restart all puppet daemons that didn't log anything today

+ *

# Filter out servers where puppet is not running, we don't want to start it there
@service.status('puppet')
= $ok

# And filter out servers where puppet logged today
@tail /var/log/puppet/puppetd.log
- x[1] =~ /2013-02-17/

# Restart puppet
service.restart('puppet')
