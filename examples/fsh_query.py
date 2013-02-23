# Example of a custom host query mechanism: a django app
#
# At booking, all server informatin is in a Django app and this can be queried
# too. We'll add two roles to the host query grammar for django lookups:
#
# - foo__bar == "value" (can support ints etc. too)
# - foo__bar =~ /regex/
#
# The query method gets called before any other possibile query methods, so
# make sure we have a query we can handle.

import pyparsing as pp
import re
import os, sys
sys.path.insert(0, '/opt/sysadmin')
os.environ['DJANGO_SETTINGS_MODULE'] = 'serverdb2.settings'

def hostq(grammar):
    query = pp.Group(grammar.ident + ((pp.oneOf('== !=')  + grammar.val) | (pp.oneOf('=~ !~') + grammar.re_)))
    return query

def query(query):
    if isinstance(query, str) or len(query) != 3:
        return None

    attr, op, val = query
    if attr == 'x':
        return None

    from serverdb2.servers.models import Server
    if op == '==':
        servers = Server.objects.filter(**{attr: eval(val)})
    elif op == '!=':
        servers = Server.objects.exclude(**{attr: eval(val)})
    elif op == '=~':
        servers = Server.objects.filter(**{attr + '__regex': val})
    elif op == '!~':
        servers = Server.objects.exclude(**{attr + '__regex': val})
    return set(servers.distinct().values_list('name', flat=True))
