#!/usr/bin/python

from distutils.core import setup
from distutils.ccompiler import new_compiler
from distutils.command.build_scripts import build_scripts
from distutils.command.clean import clean
import os
import sys

def build_fsh():
    cc = new_compiler()
    opt_obj = cc.compile(['fsh.c'])
    cc.link_executable(opt_obj, 'fsh')
    os.unlink(opt_obj[0])

class my_build_scripts(build_scripts):
    def run(self):
        build_fsh()
        build_scripts.run(self)

class my_clean(clean):
    def run(self):
        clean.run(self)
        if os.path.exists('fsh'):
            os.unlink('fsh')

setup(name="func-shell",
    version="1.2",
    author="Dennis Kaarsemaker",
    author_email="dennis@kaarsemaker.net",
    url="http://github.com/seveas/func-shell",
    description="Parallel shell using Func",
    scripts=["fsh.py", "fsh"],
    cmdclass={
        'build_scripts': my_build_scripts,
        'clean': my_clean,
    },
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Topic :: Software Development :: Interpreters',
        'Topic :: System :: Systems Administration',
    ],
)
