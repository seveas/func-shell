#!/usr/bin/python
#
# fsh - The func shell
#
# (c) 2012-2013 Dennis Kaarsemaker <dennis@kaarsemaker.net>
# see COPYING for license details

import fcntl
from func.overlord.client import Overlord, DEFAULT_MAPLOC
import optparse
import os
import pprint
import pyparsing
import re
import readline
import struct
import sys
import termios

def shell():
    p = optparse.OptionParser(usage="%prog [opts] [scripts]")
    p.add_option('-v', '--verbose', dest="verbose", action="store_true", default=False,
                 help="Print all commands before executing")
    p.add_option('-i', '--interactive', dest="interactive", action="store_true", default=False,
                 help="Start an interactive shell after processing all files")
    opts, files = p.parse_args()

    if not files or opts.interactive:
        files.append(sys.stdin)
    FuncShell(files, opts).run_shell()

class FuncShell(object):
    def __init__(self, files, opts):
        self.hosts = set()
        self.parallel = 50
        self.timeout = 10
        self.verbose = opts.verbose
        self.ps4 = os.environ.get('PS4', '+ ')
        self.files = [hasattr(f, 'readline') and ('-', f) or (f, open(f)) for f in files]
        self.last_result = {}
        self.last_ok = set()
        self.grammar = FuncShellGrammar()

    def run_shell(self):
        do_readline = sys.stdin.isatty() and ('-', sys.stdin) in self.files
        if do_readline and os.path.exists(os.path.expanduser('~/.fsh_history')):
            readline.read_history_file(os.path.expanduser('~/.fsh_history'))

        for file in self.files:
            self.curfile = file[0]
            self.curline = 0
            if self.verbose:
                print "%s(Now processing %s)" % (self.ps4, file[0])
            try:
                while True:
                    line = self.get_input(file[1])
                    if not line:
                        break
                    if self.verbose:
                        print '%s%s (%s, line %d)' % (self.ps4, line, self.curfile, self.curline)
                    self.parse_and_run(line)

            except:
                if do_readline:
                    readline.write_history_file(os.path.expanduser('~/.fsh_history'))
                raise

        if do_readline:
            readline.write_history_file(os.path.expanduser('~/.fsh_history'))

    def get_input(self, file):
        while True:
            self.curline += 1
            try:
                if file.isatty():
                    line = raw_input('fsh> ')
                else:
                    line = file.readline()
            except KeyboardInterrupt:
                print >>sys.stderr, "KeyboardInterrupt (Use ^D or exit to exit)"
                continue
            except EOFError:
                if file.isatty():
                    print ""
                break
            if line == '':
                if not file.isatty():
                    break
            if not line or line.startswith('#'):
                continue

            line = line.strip()
            return line

    def parse_and_run(self, line):
        try:
            line = self.grammar.admin.parseString(line)
            return self.run_admin_command(line)
        except pyparsing.ParseException:
            pass

        try:
            line = self.grammar.call.parseString(line)
            return self.run_func_call(line)
        except pyparsing.ParseException:
            pass

        try:
            line = self.grammar.command.parseString(line)
            return self.run_shell_command(line)
        except pyparsing.ParseException:
            pass

        print >>sys.stderr, "Unrecognized input: %s" % line
        return

    def run_admin_command(self, line):
        if len(line) == 1 and line[0]  == '?':
            pprint.pprint(sorted(self.hosts), width=self.get_columns())
            print "Running commands on %d/%d hosts(s) in parallel" % (min(self.parallel, len(self.hosts)), len(self.hosts))
            print "Timeout: %d seconds" % (self.timeout,)
            return

        if len(line) != 2:
            raise RuntimeError("Internal error")
        op = line[0]

        matches = self.parse_hosts(line[1])
        if op == '?':
            pprint.pprint(sorted(matches))
        elif op == '=':
            self.hosts = matches
        else:
            getattr(self.hosts, {'-': 'difference_update', '+': 'update'}[op])(matches)

    def parse_hosts(self, query):
        ret = set()
        if not isinstance(query, str):
            query = ''.join(query)
        if query == '$ok':
            return set(self.last_ok)
        if query == '$failed':
            return self.hosts - self.last_ok
        if '==' in query:
            query = eval('lambda x: ' + query)
            try:
                return set([x for x in self.last_result if query(self.last_result[x])])
            except Exception, e:
                print str(e)
                return set()
        if '=~' in query:
            getval = eval('lambda x: ' + query[:query.find('=~')])
            rx = re.compile(query[query.find('=~')+2:])
            try:
                return set([x for x in self.last_result if rx.search(getval(self.last_result[x]))])
            except Exception, e:
                print str(e)
                return set()

        # And now we finally get to the func map
        try:
            return set(Overlord(query, delegate=os.path.exists(DEFAULT_MAPLOC)).list_minions())
        except Exception, e:
            print str(e)
            return set()

    def run_func_call(self, line):
        quiet = line[0] == '@' and line.pop(0)
        if len(line) != 3:
            raise RuntimeError("Internal error")
        args = eval(''.join(line[2])[:-1] + ",)")
        return self.run(line[0], line[1], args, quiet)

    def run_shell_command(self, line):
        quiet = line[0] == '@' and line.pop(0)
        command = line[0]
        meth = getattr(self, 'run_' + command, None)
        if meth:
            return meth(line[1:])
        return self.run('command', 'run', [' '.join(line)], quiet)

    def run_set(self, args):
        if not args:
            print >>sys.stderr, "Usage: set <param> [<val>]"
            return
        if args[0] in ('timeout', 'parallel'):
            if len(args) != 2 or not args[1].isdigit():
                print >>sys.stderr, args[0] + " requires an integer value"
            setattr(self, args[0], int(args[1]))
        elif args[0] == '-x':
            self.verbose = True
        elif args[0] == '+x':
            self.verbose = False
        else:
            print >>sys.stderr, "Unrecognized variable: %s" % args[0]

    def run_quit(self, args):
        raise SystemExit()

    def run_exit(self, args):
        raise SystemExit()

    def run_help(self, args):
        print """Func shell 1.1

Basic commands:
   ?            Displays current settings
   = hostspec   Sets the hosts to use
   + hostspec   Adds to the hosts
   - hostspec   Removes from the hosts
   ? hostspec   See what matches the hostspec

   hostspecs can be hostnames, globs or filters that match the output of the
   last commands run.

Calling func methods:

   module.method(args)

Running shell commands:

   command arg1 arg2 arg3
"""

    def run(self, module, method, args, quiet):
        if not self.hosts:
            print >>sys.stderr, "Cannot run command on 0 hosts"
            return

        try:
            client = Overlord(';'.join(self.hosts), delegate=os.path.exists(DEFAULT_MAPLOC), timeout=self.timeout, nforks = self.parallel)
            module_ = getattr(client, module)
            method_ = getattr(module_, method)
            self.last_result = res = method_(*args)
            self.last_ok = set([x for x in res if not is_error(res[x], module, method)])
        except KeyboardInterrupt:
            print >>sys.stderr, "KeyboardInterrupt"
            return
        except Exception:
            print >>sys.stderr, wrap("Couldn't process command", attr.bright, fgcolor.red)
            import traceback
            traceback.print_exc()
            return

        if not quiet:
            self.display_result(module, method, res)

    def display_result(self, module, method, res):
        l = max([len(x) for x in res])
        width = self.get_columns()
        for host, out in sorted(res.items()):
            print wrap(host, attr.bright, (is_error(out, module, method) and fgcolor.red or fgcolor.green))
            if is_error(out):
                print "%s\n%s: %s" % (out[3].rstrip(), out[1], out[2])
            elif (module, method) == ('command', 'run'):
                print "Exitcode: %d\n%s\n%s\n%s\n%s" % (out[0], '-' * 20, out[1].rstrip(), '-' * 20, out[2].rstrip())
            else:
                pprint.pprint(out, width=width)

    def get_columns(self):
        columns = 80
        if 'COLUMNS' in os.environ:
            columns = int(os.environ['COLUMNS'])
        else:
            rows, columns = struct.unpack('hh', fcntl.ioctl(sys.stdin, termios.TIOCGWINSZ, '1234'))
        return columns

class FuncShellGrammar(object):
    def __init__(self):
        pp = pyparsing

        # Basic types
        int_   = pp.Word("0123456789")
        real_  = pp.Combine(int_ + pp.Literal('.') + int_)
        num    = int_ | real_
        str_   = pp.quotedString
        re_    = pp.QuotedString(quoteChar='/', escChar='\\')
        none   = pp.Keyword("None")
        const  = num | str_ | none
        ident  = pp.Word(pp.srange("[a-zA-Z_]"), pp.srange("[a-zA-Z0-9_]"))

        # Combined types
        val    = pp.Forward()
        tuple_ = pp.Literal('(') + pp.Optional(val + pp.ZeroOrMore(pp.Literal(',') + val)) + pp.Literal(')')
        list_  = pp.Literal('[') + pp.Optional(val + pp.ZeroOrMore(pp.Literal(',') + val)) + pp.Literal(']')
        delt   = const + pp.Literal(':') + val
        dict_  = pp.Literal('{') + pp.Optional(delt + pp.ZeroOrMore(pp.Literal(',') + delt)) + pp.Literal('}')
        val << (const | tuple_ | dict_ | list_)

        # Function call or shell command
        self.call = pp.Optional('@') + ident + pp.Literal('.').suppress() + ident + pp.Group(tuple_) + pp.LineEnd()
        shell     = pp.Word(pp.srange("[-_a-zA-Z0-9.+/=~|;]"))
        self.command = pp.Optional('@') + pp.OneOrMore(str_ | shell) + pp.LineEnd()

        # Admin commands
        results = pp.Literal('$ok') | pp.Literal('$failed')
        hname  = pp.Word(pp.srange("[-a-zA-Z0-9_*]"))
        fqdn   = pp.Group(hname + pp.ZeroOrMore(pp.Literal('.') + hname))
        attr   = pp.Literal('.') + ident
        elt    = pp.Literal('[') + const + pp.Literal(']')
        expr   = pp.Group(pp.Literal('x') + pp.ZeroOrMore(attr|elt) + (pp.Literal('==') + val | pp.Literal('=~') + re_))
        hostq  = (results | expr | str_ | num | fqdn)
        self.admin = (pp.oneOf('?') + pp.Optional(hostq) | pp.oneOf('= + -') + hostq) + pp.LineEnd()

is_error = lambda x, module=None, method=None: isinstance(x, list) and (x[0] == 'REMOTE_ERROR' or ((module, method) == ('command', 'run') and x[0] != 0))

class Attr(object):
    def __init__(self, **attr):
        for k, v in attr.items():
            setattr(self, k, v)

fgcolor = Attr(black=30, red=31, green=32, yellow=33, blue=34, magenta=35, cyan=36, white=37, none=None)
bgcolor = Attr(black=40, red=41, green=42, yellow=43, blue=44, magenta=45, cyan=46, white=47, none=None)
attr    = Attr(normal=0, bright=1, faint=2, underline=4, negative=7, conceal=8, crossed=9, none=None)

esc = '\033'
mode = lambda *args: "%s[%sm" % (esc, ';'.join([str(x) for x in args if x is not None]))
reset = mode(attr.normal)
wrap = lambda text, *args: sys.stdout.isatty() and "%s%s%s" % (mode(*args), text, reset) or text

if __name__ == '__main__':
    shell()
