########################################################################
#
# File:   testsuite/QMTest/database.py
# Author: Zack Weinberg
# Date:   2002-08-05
#
# Contents:
#   Test database specific to QMTest self-test suite.
#
# Copyright (c) 2002 by CodeSourcery, LLC.  All rights reserved.
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

class RegTest(Test):
    """A 'RegTest' performs a regression test on QMTest itself.

    Each regression test is stored as a subdirectory of the 'regress'
    directory.  Each such subdirectory is a complete test database in
    itself, such that running "qmtest -D . run -O results.qmr" in that
    directory should succeed, reporting all tests completed as
    expected.  The test is judged to have succeeded if so."""

    arguments = [
        qm.fields.TextField(
            name        = "path",
            title       = "Path to test",
            verbatim    = "true",
            multiline   = "false",
            description = """The pathname of the test.

            This is a path to a directory in the file system containing
            a complete, self-contained test database.  All the tests in
            this database will be executed to perform the regression test."""
            )
        ]

    # This pattern is matched against the output of a QMTest subprocess
    # to determine if there were any unexpected outcomes.
    good_outcome_pat = re.compile(
        r"^-+\s+TESTS\s+WITH\s+UNEXPECTED\s+OUTCOMES\s+-+\s+None",
        re.MULTILINE)

    def Run(self, context, result):
        path = self.path
        results = os.path.join(path, "results.qmr")
        output = os.path.join(path, "output.qmr")

        # Sanity check the target location.
        assert os.path.isdir(os.path.join(path, "QMTest"))
        assert os.path.isfile(results)
        
        # The QMTest binary to test is specified as a context variable.
        qmtest = context['qmtest_path']

        argv = (qmtest, "-D", path, "run", "-O", results, "-o", output)

        e = qm.executable.RedirectedExecutable()
        status = e.Run(argv)
        stdout = e.stdout
        stderr = e.stderr

        result.Annotate({
            "selftest.RegTest.cmdline"  : ' '.join(argv),
            "selftest.RegTest.exitcode" : ("%d" % status),
            "selftest.RegTest.stdout"   : '<pre>' + stdout + '</pre>',
            "selftest.RegTest.stderr"   : '<pre>' + stderr + '</pre>'
            })

        if stderr != '':
            # Printing anything to stderr is a failure.
            result.Fail("Child process reported errors")
        elif status:
            # Unsuccessful termination is a failure.  This is checked
            # second because output on stderr should come along with
            # an unsuccessful exit, and we want to pick the more specific
            # failure cause.
            result.Fail("Child process exited unsuccessfully")
        elif self.good_outcome_pat.search(stdout) is None:
            # If there were unexpected outcomes, it's a failure.
            result.Fail("Unexpected outcomes reported")
        else:
            # Success.  Delete the uninteresting output file.
            os.remove(output)


        
