########################################################################
#
# File:   tet_stream.py
# Author: Nathaniel Smith
# Date:   2004-02-11
#
# Contents:
#   TETStream
#
# Copyright (c) 2004 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from   dejagnu_test import DejaGNUTest
import qm.fields
import qm.common
from   qm.test.file_result_stream import FileResultStream
from   qm.test.result import Result
import time

########################################################################
# Classes
########################################################################

class TETStream(FileResultStream):
    """A 'TETStream' formats results as a TET journal.
    
    Provides special handling for 'DejaGNUTest' results.

    TET: http://tetworks.opengroup.org/
    TET journal format: see appendix C and D of
       http://tetworks.opengroup.org/documents/3.7/uguide.pdf

    For the meaning of TET result codes, we use as guidelines the LSB
    test faq, question Q1.11:
        * PASS - a test result belonging to this group is considered to
          be a pass for compliance testing purposes:
              o Pass - the test has been executed correctly and to
                completion without any kind of problem
              o Warning - the functionality is acceptable, but you
                should be aware that later revisions of the relevant
                standards or specification may change the requirements
                in this area.
              o FIP - additional information is provided which needs to
                be checked manually.
              o Unsupported - an optional feature is not available or
                not supported in the implementation under test.
              o Not in Use - some tests may not be required in certain
                test modes or when an interface can be implemented by a
                macro or function and there are two versions of the test
                only one is used.
              o Untested - no test written to check a particular feature
                or an optional facility needed to perform a test is not
                available on the system.
          [There are also "notimp" and "unapproved" cases mentioned in
          the LSB-FHS README, but they are otherwise undocumented, and
          don't correspond to any DejaGNU or QMTest outcomes anyway.]
        * FAIL - a test result belonging to this group is considered to
          be a fail for compliance testing purposes (unless the failure
          has been waived by an agreed Problem Report in the
          Certification Problem Reporting database):
              o Fail - the interface did not behave as expected.
              o Uninitiated - the particular test in question did not
                start to execute.
              o Unresolved - the test started but did not reach the
                point where the test was able to report success or
                failure.
              o Unreported - a major error occurred during the testset
                execution.  (The TET manual calls this NORESULT.)
    (From http://www.linuxbase.org/test/lsb-runtime-test-faq.html )
    
    DejaGNU test results are described as:
        * PASS - A test has succeeded.
        * FAIL - A test has produced the bug it was intended to
          capture.
        * WARNING - Declares detection of a minor error in the test case
          itself.  Use WARNING rather than ERROR for cases (such as
          communication failure to be followed by a retry) where the
          test case can recover from the error.  Note that sufficient
          warnings will cause a test to go from PASS/FAIL to
          UNRESOLVED.
        * ERROR - Declares a severe error in the testing framework
          itself.  An ERROR also causes a test to go from PASS/FAIL to
          UNRESOLVED.
        * UNRESOLVED - A test produced indeterminate results.  Usually,
          this means the test executed in an unexpected fashion; this
          outcome requires that a human being go over results, to
          determine if the test should have passed or failed.  This
          message is also used for any test that requires human
          intervention because it is beyond the abilities of the testing
          framework.  Any unresolved test should be resolved to PASS or
          FAIL before a test run can be considered finished.

          Examples:
              - a test's execution is interrupted
              - a test does not produce a clear result (because of
                WARNING or ERROR messages)
              - a test depends on a previous test case which failed
        * UNTESTED - a test case that isn't run for some technical
          reason.  (E.g., a dummy test created as a placeholder for a
          test that is not yet written.)
        * UNSUPPORTED - Declares that a test case depends on some
          facility that does not exist in the testing environment; the
          test is simply meaningless.
    (From a combination of DejaGNU manual sections "Core Internal
    Procedures", "C Unit Testing API", and "A POSIX conforming test
    framework".)

    """
    
    # TET result codes:
    PASS = (0, "PASS")
    WARNING = (101, "WARNING")
    FIP = (102, "FIP")
    UNSUPPORTED = (4, "UNSUPPORTED")
    NOTINUSE = (3, "NOTINUSE")
    UNTESTED = (5, "UNTESTED")

    FAIL = (1, "FAIL")
    UNINITIATED = (6, "UNINITIATED")
    UNRESOLVED = (2, "UNRESOLVED")
    UNREPORTED = (7, "UNREPORTED")


    def __init__(self, arguments = None, **args):

        super(TETStream, self).__init__(arguments, **args)
        
        self._start_time = "<unknown_start_time>"
        self._finish_time = "<unknown_finish_time>"
        self._aborted = False
        self._username = "<unknown_user>"
        self._userid = "<unknown_user>"
        self._version = "<unknown_version>"
        self._uname = "<unknown_uname>"
        self._cmdline = "<unknown_command_line>"
        self._settings = {}

        self._tcc_number = 0
        self._printed_initial_stuff = False
            
            
    def _WriteLine(self, code, data, comment):
        """Write a line in TET journal format."""

        self.file.write("%i|%s|%s\n" % (code, data, comment))


    def _IsDejaGNUResult(self, result):
        """Returns 'True' if 'result' has DejaGNU subtests."""

        for key in result.keys():
            if key.startswith(DejaGNUTest.RESULT_PREFIX):
                return True
        return False


    def _TETFormatTime(self, time_string):
        """Converts an ISO-format date-time to a TET-format date-time.

        returns -- A 2-tuple whose first element is the time as a string,
        and whose second is the date as a string."""

        t = time.gmtime(qm.common.parse_time_iso(time_string))

        return (time.strftime("%H:%M:%S", t),
                time.strftime("%Y%m%d", t))


    def _ExtractTime(self, result, key):
        """Extracts the start time from a result."""

        if result.has_key(key):
            return self._TETFormatTime(result[key])[0]
        else:
            return "00:00:00"


    def WriteAnnotation(self, key, value):

        if key == "qmtest.run.start_time":
            self._start_time, self._start_date \
                              = self._TETFormatTime(value)
        elif key == "qmtest.run.end_time":
            self._finish_time, self._finish_data \
                               = self._TETFormatTime(value)
        elif key == "qmtest.run.aborted" and value == "true":
            self._aborted = True
        elif key == "qmtest.run.username":
            self._username = value
        elif key == "qmtest.run.userid":
            self._userid = value
        elif key == "qmtest.run.version":
            self._version = "qmtest-" + value
        elif key == "qmtest.run.uname":
            self._uname = value
        elif key == "qmtest.run.command_line":
            self._cmdline = value
        else:
            self._settings[key] = value


    def _WriteInitialStuff(self):
        """Print TET header information, but only on first call.

        Second and later calls are no-ops."""

        if self._printed_initial_stuff:
            return

        # Test case controller start
        # 0 | version time date | who
        # who is
        # "User: <username> (<numeric-id>) TCC Start, Command line: <cmdline>"
        data = "%s %s %s" % (self._version,
                             self._start_time,
                             self._start_date)
        who = "User: %s (%s) TCC Start, Command line: %s" \
              % (self._username, self._userid, self._cmdline)

        self._WriteLine(0, data, who)
        # Local system information
        # 5 | sysname nodename release version machine | text
        self._WriteLine(5, self._uname, "")
        # Local system configuration start
        # 20 | pathname mode | text
        self._WriteLine(20, "qmtest -1", "Config Start")
        for item in self._settings.iteritems():
            # Configuration variable setting
            # 30 || variable=value
            self._WriteLine(30, "", "%s=%s" % item)
        # Configuration end
        # 40 || text
        self._WriteLine(40, "", "Config End")
        
        self._printed_initial_stuff = True


    def WriteResult(self, result):

        self._WriteInitialStuff()
        if result.GetKind() == Result.TEST:
            self._tcc_number += 1
            if self._IsDejaGNUResult(result):
                self._WriteDejaGNUResult(result)
            else:
                self._WriteTestResult(result)
        else:
            # We have a resource result.
            self._WriteResourceResult(result)


    def _WriteTCStart(self, result):
        """Write a TET test case start line."""

        # Test case start
        # 10 | activity_number testcase_path time | invocable_components
        started = self._ExtractTime(result, Result.START_TIME)
        data = "%i %s %s" % (self._tcc_number,
                             "/" + result.GetId(),
                             started)
        self._WriteLine(10, data, "TC Start")


    def _WriteResultAnnotations(self, result, purpose,
                                num_restrict=None, seq_start=1):
        """Writes out annotations for a 'result' in TET format.

        Annotations are represented as (sequences of) "test case
        information" lines.

        'result' -- The 'Result' whose annotations should be written.

        'num_restrict' -- Only write out annotations that end with this
        number.  If the number is '1', also writes out all results that
        don't end in any number, with "INFO: " prefixed.  If 'None',
        writes out all annotations.

        'seq_start' -- The TET test case information sequence number to
        start with."""

        seqnum = seq_start
        keys = result.keys()
        keys.sort()
        for key in keys:
            value = result[key]
            prefix = ""
            if num_restrict is not None:
                if num_restrict == 1 and key[-1] not in "0123456789":
                    prefix = "INFO: "
                elif not key.endswith("_%i" % num_restrict):
                    continue
                    
            text = qm.common.html_to_text(value)
            for line in text.split("\n"):
                # Test case information
                # 520 | activity_num tp_num context block sequence | text
                #
                # We always set 'tp_num' to zero, because annotations
                #   for us are associated with test cases, not test
                #   purposes.
                # 'context' is to distinguish text coming from different
                #   subprocesses making up the test purpose; it's
                #   generally the pid.  For us, it's always zero.
                # 'block' is entirely undocumented, and the examples
                #   have it always set to one, so we simply set it to
                #   one as well.
                # 'sequence' appears to be incremented for each line
                #   within a single test purpose and context.
                self._WriteLine(520,
                                "%i %i 0 1 %i" % (self._tcc_number,
                                                  purpose,
                                                  seqnum),
                                "%s%s: %s" % (prefix, key, line))
                seqnum += 1


    def _WriteDejaGNUResult(self, result):
        """Write out a result that has DejaGNU subtest information."""

        self._WriteTCStart(result)
        
        # Get the DejaGNU annotations in sorted order.
        keys = filter(lambda k: k.startswith(DejaGNUTest.RESULT_PREFIX),
                      result.keys())
        keys.sort(lambda k1, k2: cmp(int(k1[len(DejaGNUTest.RESULT_PREFIX):]),
                                     int(k2[len(DejaGNUTest.RESULT_PREFIX):])))

        start_time = self._ExtractTime(result, Result.START_TIME)
        end_time = self._ExtractTime(result, Result.END_TIME)

        purpose = 1
        for k in keys:
            r = result[k]
            outcome = r[:r.find(":")]
            # Test purpose start
            # 200 | activity_number test_purpose_number time | text
            self._WriteLine(200,
                            "%i %i %s"
                            % (self._tcc_number, purpose, start_time),
                            "TP Start")

            outcome_num, outcome_name \
                = { DejaGNUTest.PASS: self.PASS,
                    DejaGNUTest.XPASS: self.PASS,
                    DejaGNUTest.FAIL: self.FAIL,
                    DejaGNUTest.XFAIL: self.FAIL,
                    DejaGNUTest.UNTESTED: self.UNTESTED,
                    DejaGNUTest.UNRESOLVED: self.UNRESOLVED,
                    DejaGNUTest.ERROR: self.UNRESOLVED,
                    DejaGNUTest.WARNING: self.WARNING,
                    # TET's UNSUPPORTED is like a FAIL for tests
                    # that check for optional features; UNTESTED is
                    # the correct correspondent for DejaGNU's
                    # UNSUPPORTED.
                    DejaGNUTest.UNSUPPORTED: self.UNTESTED,
                    }[outcome]
            # As a special case, check for magic annotation.
            if result.has_key("test_not_relevant_to_testing_mode"):
                outcome_num, outcome_name = self.NOTINUSE

            # Write per-purpose annotations:
            self._WriteResultAnnotations(result, purpose,
                                         num_restrict=purpose)

            # Test purpose result
            # 220 | activity_number tp_number result time | result-name
            data = "%i %i %i %s" % (self._tcc_number,
                                    purpose,
                                    outcome_num,
                                    end_time)
            self._WriteLine(220, data, outcome_name)

            purpose += 1
            
        # Test case end
        # 80 | activity_number completion_status time | text
        # "completion status" appears undocumented; it is zero in all of
        # the documented examples.
        self._WriteLine(80,
                        "%i 0 %s" % (self._tcc_number, end_time),
                        "TC End")

            
    def _WriteTestResult(self, result):
        """Write out a result that does not have DejaGNU annotations."""

        self._WriteTCStart(result)
        # Test purpose start
        # 200 | activity_number test_purpose_number time | text
        start_time = self._ExtractTime(result, Result.START_TIME)
        data = "%i 1 %s" % (self._tcc_number, start_time)
        self._WriteLine(200, data, "TP Start")

        outcome_num, outcome_name = { Result.FAIL: self.FAIL,
                                      Result.PASS: self.PASS,
                                      Result.UNTESTED: self.UNINITIATED,
                                      Result.ERROR: self.UNREPORTED,
                                    }[result.GetOutcome()]
        if result.GetOutcome() == Result.ERROR:
            # Test case information
            # 520 | activity_num tp_num context block sequence | text
            # (see _WriteResultAnnotations for details)
            self._WriteLine(520,
                            "%i 1 0 1 1" % self._tcc_number,
                            "QMTest ERROR in test " + result.GetId())
            self._WriteResultAnnotations(result, 1, seq_start=2)
        else:
            self._WriteResultAnnotations(result, 1)

        # Test purpose result
        # 220 | activity_number tp_number result time | result-name
        end_time = self._ExtractTime(result, Result.END_TIME)
        data = "%i 1 %i %s" % (self._tcc_number, outcome_num, end_time)
        self._WriteLine(220, data, outcome_name)

        # Test case end
        # 80 | activity_number completion_status time | text
        # "completion status" appears undocumented; it is zero in all of
        # the documented examples.
        self._WriteLine(80,
                        "%i 0 %s" % (self._tcc_number, end_time),
                        "TC End")


    def _WriteResourceResult(self, result):
        """Write out information on a resource result.

        TET has no concept of resources, so we ignore successful
        resources, and print out "test case controller messages" for
        ERRORs and FAILUREs."""

        if result.GetOutcome() in (Result.FAIL, Result.ERROR):
            if result.GetKind() == Result.RESOURCE_SETUP:
                verbing = "setting up"
            elif result.GetKind() == Result.RESOURCE_CLEANUP:
                verbing = "cleaning up"
            else:
                assert False, "Unexpected result kind"
            id = result.GetId()
            outcome = result.GetOutcome()
            # Test case controller message
            # 50 || text describing problem
            self._WriteLine(50, "", "Problem with %s resource %s: %s"
                                    % (verbing, id, outcome))

            for key, value in result.items():
                for line in value.split("\n"):
                    self._WriteLine(50, "", "%s: %s" % (key, line))


    def Summarize(self):

        self._WriteInitialStuff()
        
        if self._aborted:
            # User abort
            # 90 | time | text
            self._WriteLine(90, self._finish_time, "Aborted.")

        # Test case controller end
        # 900 | time | text
        self._WriteLine(900, self._finish_time, "Done.")
