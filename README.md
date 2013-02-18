fsh - The func shell
====================

Func is a remote execution framework that allows you to execute python code or
shell commands on as many servers as you want. You can extend it with your own
modules and use the overlord api or a shell command to execute these.

What's missing is an interactive shell and way to create simple scripts without
resorting to python. I quite often use func to troubleshoot, a typical session
goes like this:

- Check the {contents of a file, status of a service, age of a cache}
- On machines where it's wrong, run a command to fix it
- Lather, rinse repeat

Installing
----------
This package requires func, which is not installable from PyPI, and pyparsing
(which is). Once func is installed and configured, installing func-shell is as
simple as:

    $ pip install pyparsing func-shell

Example
-------

fsh has been built to make this a lot easier. Here's a typical session, I
needed to restart puppet on servers where it hung, with comments to explain:

Add all machines with 'lhr1' in their hostname to the current list of machines

    fsh> + *lhr1*

Test reachability

    fsh> @test.ping()

Use only reachable hosts

    fsh> = $ok

Tail the puppet log log

    fsh> @tail /var/log/puppet/puppetd.log

Filter out hosts that have todays date in the log, they're not hung

    fsh> - x[1] =~ /2013-02-02/

And restart the puppet service

    fsh> service.restart('puppet')
    test1-lhr1.kaarsemaker.net
    0
    test2-lhr1.kaarsemaker.net
    0
    test3-lhr1.kaarsemaker.net
    0

To write that as a one-off python script, or in the python interactive
interpreter is error-prone and tedious.

While you could do all this in python, fsh makes it easier and clearer with
more concise syntax and easier to understand output.

Syntax
------
There are 4 types of input:

- Commands to modify the list of hosts
- Calls to func modules, such as test.ping()
- Shell commands to be executed via the command module
- Comments, which are lines starting with a # character (leading whitespace is
  allowed and ignored)

All these commands can be entered in an interactive shell, or in a file to be
executed by the shell.

The list of hosts
-----------------
 - `+ hostspec` (add host to the set)
 - `- hostspec` (remove hosts from the set)
 - `= hostspec` (reset the current set)
 - `? [hostspec]` (display the expansion of `hostspec`, or the current hosts)

These commands all manipulate the list of hosts that subsequent commands run
on. A `hostspec` can take 2 forms: a hostname or glob, such as:

    = dbserver-*
    + webapp-*.*
    - webapp-101.kaarsemaker.net

Or a filter expression that matches the results of the last executed command:

    - x[0] == 0
    - x[1] =~ /my-test-string/

You can also use the special strings `$ok` and `$failed` to refer to the hosts
the last command succesfully ran on or failed to run. A succesful run is one
that does not raise a python error and (in the case of a shell command) exited
with status code 0.

Func parameters
---------------

fsh has a few internal variables you can set in the shell:

How many hosts to do in parallel:

    set parallel 20

The timeout for commands:

    set timeout 30

Verbosity (like in bash):

    set +x
    set -x

Calling func module functions
-----------------------------
Anything that looks like a function call to a func method, `module.method(...)`,
will be interpreted as such. Arguments to the method can only be literals.
Examples:

    test.ping()
    service.stop('named')
    mymodule.mymethod(["foo", "bar", {"baz": "quux"}])

The result of the command will be displayed. To suppress the displaying, prefix the call
with an @ sign. This is useful if the result is only used for filtering hosts.

    @test.ping()

Shell commands
--------------
Anything that does not look like administrativa or func call will be executed
as a shell command on the remote servers in the current host list. As with
calls to func modules, the output is shown on screen unless you prefix the call
with an @ sign. To see what's in `/srv/www`, if it exists:

    @test -e /srv/www
    - $failed
    ls -la /srv/www | grep html

Examples
--------
The examples directory has examples with comments. If you have a neat example,
submit a pull request on https://github.com/seveas/func-shell :-)
