########################################################################
#
# File:   results_file_test.py
# Author: Nathaniel Smith
# Date:   2003-08-08
#
# Contents:
#   ResultsFileTest
#
# Copyright (c) 2002, 2003 by CodeSourcery, LLC.  All rights reserved.
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

import os
import re
import qm.executable
from   qm.test.test import *
from   qm.test.result import *

########################################################################
# classes
########################################################################

class ResultsFileTest(Test):
    """A 'ResultsFileTest' tests that QMTest can load a results file.
    """

    arguments = [
        qm.fields.TextField(
            name        = "results_file",
            title       = "Path to results file.",
            verbatim    = "true",
            multiline   = "false",
            description = """The pathname of the results file."""
            ),
        qm.fields.TextField(
            name        = "tdb",
            title       = "Path to test database.",
            verbatim    = "true",
            multiline   = "false",
            description = """The pathname of the test database file.

            All tests in this database will be run, and the outcomes
            compared to those stored in the results file."""
            ),
        ]

    def Run(self, context, result):

        # Sanity check the arguments.
        assert os.path.isfile(self.results_file)
        assert os.path.isdir(self.tdb)
        
        # The QMTest binary to test is specified as a context variable.
        qmtest = context['qmtest_path']

        argv = (qmtest, "-D", self.tdb,
                "run", "-O", self.results_file, "--no-output")

        e = qm.executable.RedirectedExecutable()
        status = e.Run(argv)

        result.Annotate({
            "selftest.RegTest.cmdline"  : ' '.join(argv),
            "selftest.RegTest.exitcode" : ("%d" % status),
            "selftest.RegTest.stdout"   : '<pre>' + e.stdout + '</pre>',
            "selftest.RegTest.stderr"   : '<pre>' + e.stderr + '</pre>',
            })

        if e.stderr != '':
            # Printing anything to stderr is a failure.
            result.Fail("Child process reported errors")
        elif status:
            # Unsuccessful termination is a failure.  This is checked
            # second because output on stderr should come along with
            # an unsuccessful exit, and we want to pick the more specific
            # failure cause.
            result.Fail("Child process exited unsuccessfully")
        
