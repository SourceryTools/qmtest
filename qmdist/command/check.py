########################################################################
#
# File:   check.py
# Author: Stefan Seefeld
# Date:   2003-09-01
#
# Contents:
#   command to run tests on QMTest itself
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

from distutils.cmd import Command
from distutils.spawn import spawn, find_executable
from distutils.dep_util import newer, newer_group
from distutils.dir_util import copy_tree, remove_tree
from distutils.file_util import copy_file
import os
import os.path
import string
import glob

norm = os.path.normpath

def remove_if_exists(file): os.path.exists(file) and os.remove(file)

class check(Command):
    """Defines the testing procedure for QMTest itself."""

    description = "run internal tests on QMTest"

    user_options = [('serial', 's',
                     "perform serial tests"),
                    ('threads', 't',
                     "perform threaded tests"),
                    ('processes', 'p',
                     "perform sub-processed tests"),
                    ('rsh', 'r',
                     "perform tests over remote-shell"),
                    ('all', 'a',
                     "perform all tests"),
                    ]
    boolean_options = ['serial', 'threads', 'processes', 'rsh']

    def initialize_options (self):
        self.serial = 0
        self.threads = 0
        self.processes = 0
        self.rsh = 0
        self.all = None

        self.build_scripts = None


    def finalize_options (self):
        """Compute what tests to execute.
        If no option is specified test everything.
        Else only run the tests that are chosen."""
        if self.all == None and not (self.serial or self.threads or self.processes or self.rsh):
            self.all = 1
        if (self.all):
            self.serial = 1
            self.threads = 1
            self.processes = 1
            self.rsh = 1
        # Pick up the build scripts directory from the 'build' command.
        self.set_undefined_options("build",
                                   ("build_scripts", "build_scripts"))


    def check_serial(self, qmtest, options):
        """Perform serial tests."""

        cmd = [qmtest] + options + \
              ['-D', 'tests', 'run', '-c',
               norm('qmtest_path=' + qmtest)]
        spawn(cmd)

    def check_threads(self, qmtest, options):
        """Perform threaded tests."""

        remove_if_exists(norm('tests/QMTest/thread_target'))
        cmd = [qmtest,
               '-D', 'tests', 'create-target', '-a', 'threads=4',
               '-T', norm('tests/QMTest/thread_target'),
               'thread', 'thread_target.ThreadTarget']
        spawn(cmd)
        cmd = [qmtest] + options + \
              ['-D', 'tests', 'run',
               '-T', norm('tests/QMTest/thread_target'),
               '-c', 'qmtest_path=%s' % norm(qmtest),
               '-c', 'qmtest_target=%s'%norm('tests/QMTest/thread_target')]
        spawn(cmd)

    def check_processes(self, qmtest, options):
        """Perform sub-processed tests."""

        remove_if_exists(norm('tests/QMTest/process_target'))
        cmd = [qmtest,
               '-D', 'tests', 'create-target', '-a', 'processes=4',
               '-T', norm('tests/QMTest/process_target'),
               'process', 'process_target.ProcessTarget']
        spawn(cmd)
        cmd = [qmtest] + options + \
              ['-D', 'tests', 'run',
               '-T', norm('tests/QMTest/process_target'),
               '-c', 'qmtest_path=%s' % norm(qmtest),
               '-c', 'qmtest_target=%s'%norm('tests/QMTest/process_target')]
        spawn(cmd)

    def check_rsh(self, qmtest, options):
        """Perform tests over a remote shell."""

        remove_if_exists(norm('tests/QMTest/rsh_target'))
        cmd = [qmtest,
              '-D', 'tests', 'create-target',
               '-a', 'host=localhost', '-a', 'remote_shell=ssh',
               '-T', norm('tests/QMTest/rsh_target'),
               'rsh', 'rsh_target.RSHTarget']
        spawn(cmd)
        abs_target = os.path.abspath("tests/QMTest/rsh_target")
        cmd = [qmtest] + options + \
              ['-D', 'tests', 'run',
               '-T', norm('tests/QMTest/rsh_target'),
               '-c', 'qmtest_path=%s' % norm(qmtest),
               '-c', 'qmtest_target=%s' % norm(abs_target)]
        spawn(cmd)


    def run(self):
        """Execute the various tests."""

        # Ensure that QMTest is already built.
        self.run_command("build")
        b = self.distribution.get_command_obj('build')
        python_path = b.build_lib + os.pathsep + os.environ['PYTHONPATH']
        os.environ['PYTHONPATH'] = python_path
        qmtest = os.path.abspath(os.path.join(self.build_scripts, 'qmtest'))
        if os.environ.has_key("QMTESTFLAGS"):
            options = os.environ["QMTESTFLAGS"].split()
        else:
            options = []
        if self.serial:
            self.check_serial(qmtest, options)
        if self.threads:
            self.check_threads(qmtest, options)
        if self.processes:
            self.check_processes(qmtest, options)
        if self.rsh:
            self.check_rsh(qmtest, options)
