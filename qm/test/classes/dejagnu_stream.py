########################################################################
#
# File:   dejagnu_stream.py
# Author: Mark Mitchell
# Date:   04/30/2003
#
# Contents:
#   DejaGNUStream
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from   dejagnu_test import DejaGNUTest
import qm.fields
from   qm.test.file_result_stream import FileResultStream

########################################################################
# Classes
########################################################################

class DejaGNUStream(FileResultStream):
    """A 'DejaGNUStream' formats its output like DejaGNU."""

    arguments = [
        qm.fields.BooleanField(
            name = "show_expected_outcomes",
            title = "Show Expected Outcomes",
            description = """True if expected outcomes should be displayed.

            By default, only information about unexpected outcomes is
            displayed.""",
            default_value = "false"
            )
        ]

    __summary_outcomes = [
        DejaGNUTest.PASS,
        DejaGNUTest.FAIL,
        DejaGNUTest.XPASS,
        DejaGNUTest.XFAIL,
        DejaGNUTest.UNRESOLVED,
        DejaGNUTest.UNTESTED,
        DejaGNUTest.UNSUPPORTED
        ]
    """The outcomes for which summary output should be produced."""
    
    __outcome_descs = {
        DejaGNUTest.PASS: "expected passes",
        DejaGNUTest.FAIL: "unexpected failures",
        DejaGNUTest.XPASS: "unexpected successes",
        DejaGNUTest.XFAIL: "expected failures",
        DejaGNUTest.UNRESOLVED: "unresolved testcases",
        DejaGNUTest.UNTESTED: "untested testcases",
        DejaGNUTest.UNSUPPORTED: "unsupported tests",
        }
    """A map from DejaGNU outcomes to descriptions.

    See 'init_testcounts' in the DejaGNU distribution for the code
    emulated by this table."""

    __expected_outcomes = (
        DejaGNUTest.PASS,
        DejaGNUTest.XFAIL,
        DejaGNUTest.UNRESOLVED,
        DejaGNUTest.UNSUPPORTED,
        DejaGNUTest.UNTESTED
        )
    """The DejaGNU outcomes that are considered "expected" results.

    DejaGNU results with these outcomes are not displayed unless
    'show_expected_outcomes' is true."""

    def __init__(self, arguments):

        super(DejaGNUStream, self).__init__(arguments)
        self.__outcomes = {}
        for o in DejaGNUTest.dejagnu_outcomes:
            self.__outcomes[o] = 0
            
            
    def WriteResult(self, result):

        # Get the DejaGNU annotations in sorted order.
        keys = filter(lambda k: k.startswith(DejaGNUTest.RESULT_PREFIX),
                      result.keys())
        keys.sort(lambda k1, k2: cmp(int(k1[len(DejaGNUTest.RESULT_PREFIX):]),
                                     int(k2[len(DejaGNUTest.RESULT_PREFIX):])))
        has_error = 0
        for k in keys:
            r = result[k]
            outcome = r[:r.find(":")]
            if (self.show_expected_outcomes == "true"
                or outcome not in self.__expected_outcomes):
                self.file.write(r + "\n")
            # Keep track of the outcomes.
            self.__outcomes[outcome] += 1
            if outcome == DejaGNUTest.ERROR:
                has_error = 1

        # If something went wrong running the test, emit an ERROR
        # message even if DejaGNU would not have.  These cases usually
        # indicate problems with the DejaGNU test itself.
        if not has_error and result.GetOutcome () == result.ERROR:
            self.file.write("ERROR: %s (%s)\n"
                            % (result.GetId(), result.GetCause()))
            self.__outcomes[DejaGNUTest.ERROR] += 1


    def Summarize(self):

        self.file.write("\n\t\t=== Summary ===\n\n")
        # This function emulates log_summary from the DejaGNU
        # distribution.
        for o in self.__summary_outcomes:
            if self.__outcomes[o]:
                desc = "# of %s" % self.__outcome_descs[o]
                self.file.write(desc)
                if len(desc) < 24:
                    self.file.write("\t")
                self.file.write("\t%d\n" % self.__outcomes[o])
