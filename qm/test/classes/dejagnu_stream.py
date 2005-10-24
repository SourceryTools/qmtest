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

import cgi
from   dejagnu_test import DejaGNUTest
import qm.fields
from   qm.test.file_result_stream import FileResultStream
from   qm.test.result import Result
from   qm.test.file_result_reader import FileResultReader
import re
from   sets import Set

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



class DejaGNUReader(FileResultReader):
    """A 'DejaGNUReader' reads a DejaGNU log file.

    The DejaGNU log file may then be processed by QMTest.  For
    example, QMTest may generate results in an alternative format, or
    display them in the QMTest GUI.  Therefore, this reader may be
    used to obtain the benefits of QMTest's reporting characteristics,
    when using a legacy DejaGNU testsuite.

    Unfortunately, DejaGNU log files are relativley unstructured.
    Therefore, this result reader uses heuristics that may not always
    be 100% robust.  Therefore, for optimal behavior, DejaGNU
    testsuites should be converted to QMTest testsuites."""

    arguments = [
        qm.fields.BooleanField(
            name = "is_combined",
            title = "Combined Format?",
            description=\
            """True if multiple results for the same test should be combined.

            DejaGNU will sometimes print multiple results for the same
            test.  For example, when testing a compiler, DejaGNU may
            issue one result indicating whether or not a file was
            successfully compiled and another result indicating
            whether or not the file was successfully executed.  When
            using the combined format, these two results will be treated as
            subparts of a single test.  When not using the combined
            format, these results will be treated as separate
            tests.

            The combined format is the default.  However, if you want
            to see statistics that precisely match DejaGNU, you should
            not use the combined format.""",
            default_value="true",
            ),
        qm.fields.BooleanField(
            name = "expectations",
            title = "GenerateExpectations?",
            description=\
            """True if expected (not actual) results should be generated.

            In this mode, the actual results will be ignored.
            Instead, a results file indicated expected failures as
            actual failures will be generated.""",
            default_value="false",
            ),
        ]
            
    __id_regexp = re.compile("^[^:]*:[\\s]*(?P<id>[^\\s]*)")
    """A regular expression for determining test names.

    When applied to an outcome line from DejaGNU, this regular
    expression's 'id' field gives the name of the test, in the
    combined mode."""
    
    __cause_regexp = re.compile("\\((?P<cause>.*)\\)\\s*$")
    """A regular expression for determining failure causes.

    When applied to an outcome line from DejaGNU, this regular
    expression's 'cause' field gives the cause of the failure."""
    
    def __init__(self, arguments):

        # Initialize the base class.
        super(DejaGNUReader, self).__init__(arguments)
        # DejaGNU files start with "Test Run".
        if self.file.read(len("Test Run")) != "Test Run":
            raise FileResultReader.InvalidFile, \
                  "file is not a DejaGNU result stream"
        self.file.seek(0)
        self.test_ids = Set()
        if self.__UseCombinedMode():
            test_id, dejagnu_outcome, cause = self.__NextOutcome()
            if test_id:
                self.__next_result = Result(Result.TEST, test_id)
                self.__UpdateResult(self.__next_result,
                                    dejagnu_outcome,
                                    cause)


    def GetResult(self):

        if self.__UseCombinedMode():
            result = self.__next_result
            if not result:
                return None
            self.__next_result = None
        else:
            result = None
        while True:
            test_id, dejagnu_outcome, cause = self.__NextOutcome()
            # If there are no more results, stop.
            if not test_id:
                break
            if self.__UseCombinedMode() and test_id != result.GetId():
                self.__next_result = Result(Result.TEST, test_id)
                self.__UpdateResult(self.__next_result,
                                    dejagnu_outcome,
                                    cause)
                break
            elif not self.__UseCombinedMode():
                result = Result(Result.TEST, test_id)
            self.__UpdateResult(result, dejagnu_outcome, cause)
            if not self.__UseCombinedMode():
                break
        return result


    def __NextOutcome(self):
        """The next DejaGNU outcome in the file.

        returns -- A triplet ('test_id', 'outcome', 'cause').  The
        'test_id' is the name of the test.  The 'outcome' is the
        DejaGNU outcome (one of the 'DejaGNUTest.dejagnu_outcomes').
        The 'cause' is a string giving the cause (if known) of
        failure, if the test did not pass."""

        # Assume that there are no more results in the file.
        dejagnu_outcome = None
        # Scan ahead until we find a line that gives data about the
        # next result.
        while self.file:
            # Read the next line of the file.
            line = self.file.next()
            # Each test result is printed on a line by itself,
            # beginning with the DejaGNU outcome.  For example:
            #   PASS: g++.dg/compat/eh/template1 cp_compat_y_tst.o compile
            dejagnu_outcome = None
            for o in DejaGNUTest.dejagnu_outcomes:
                # Ignore WARNING; those are not really test results.
                if o != DejaGNUTest.WARNING and line.startswith(o):
                    o_len = len(o)
                    if line[o_len:o_len + 2] == ": ":
                        dejagnu_outcome = o
                    break
            if dejagnu_outcome:
                break
        # If we could not find any more result lines, then we have
        # read all of the results in the file.
        if not dejagnu_outcome:
            return None, None, None
        # Extract the name of the test.
        if self.__UseCombinedMode():
            match = self.__id_regexp.search(line)
            test_id = match.group("id")
        else:
            test_id = line[len(dejagnu_outcome) + 2:].strip()
        # Extract the cause of faiulre.
        cause = None
        if "execution test" in line:
            cause = "Compiled program behaved incorrectly."
        else:
            match = self.__cause_regexp.search(line)
            if match:
                cause = match.group("cause").capitalize()
                if cause and cause[-1] != ".":
                    cause += "."
            elif dejagnu_outcome == DejaGNUTest.UNSUPPORTED:
                cause = "Test is not applicable on this platform."
        return test_id, dejagnu_outcome, cause
        
    
    def __UpdateResult(self, result, dejagnu_outcome, cause):
        """Update 'result' as indicated.

        'result' -  A 'Result', which may contain information from
        previous DejaGNU tests, in the combined mode.

        'dejagnu_outcome' -- The DejaGNU outcome (one of the
        'DejaGNUTest.dejagnu_outcomes') that applies to this
        'result'.

        'cause' -- The cause of failure, if known.

        The 'result' is modified to reflect the new outcome and
        cause.  Results can only get worse, in the sense that if
        reuslt has an outcome of 'Result.FAIL' upon entry to this
        return, it will never have an outcome of 'Result.PASS' upon
        return."""
                       
        # Translate the DejaGNU outcome into a QMTest outcome.
        if self.__GenerateExpectations():
            if dejagnu_outcome in (DejaGNUTest.XFAIL,
                                   DejaGNUTest.XPASS):
                qmtest_outcome = Result.FAIL
            elif dejagnu_outcome == DejaGNUTest.UNSUPPORTED:
                qmtest_outcome = Result.UNTESTED
            else:
                qmtest_outcome = Result.PASS
        else:
            qmtest_outcome = DejaGNUTest.outcome_map[dejagnu_outcome]
        # Update the QMTest result for this test, based on the
        # DejaGNU result.
        if qmtest_outcome == Result.ERROR:
            result.SetOutcome(Result.ERROR)
        elif (qmtest_outcome == Result.UNTESTED
              and result.GetOutcome() != Result.ERROR):
            result.SetOutcome(Result.UNTESTED)
        elif (qmtest_outcome == Result.FAIL
              and result.GetOutcome() not in (Result.ERROR,
                                              Result.UNTESTED)):
            result.SetOutcome(Result.FAIL)
        if qmtest_outcome != Result.PASS and cause:
            old_cause = result.GetCause()
            if old_cause:
                old_cause += "  "
            old_cause += cgi.escape(cause)
            result.SetCause(old_cause)


    def __UseCombinedMode(self):
        """Returns true in the combined mode.

        returns -- True iff results should be read in the combined
        mode."""

        return self.is_combined == "true"


    def __GenerateExpectations(self):
        """Returns true if expected results should be generated.

        returns -- True iff the results generated should reflect
        expectations, rather than actual results."""

        return self.expectations == "true"

########################################################################
# Miscellaneous
########################################################################

__all__ = ["DejaGNUStream", "DejaGNUReader"]
