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

    """

    # TET result codes:
    PASS = (0, "PASS")
    FAIL = (1, "FAIL")
    UNRESOLVED = (2, "UNRESOLVED")
    NOTINUSE = (3, "NOTINUSE")
    UNSUPPORTED = (4, "UNSUPPORTED")
    UNTESTED = (5, "UNTESTED")
    UNINITIATED = (6, "UNINITIATED")
    NORESULT = (7, "NORESULT")


    def __init__(self, arguments):

        super(TETStream, self).__init__(arguments)
        
        self._start_time = "<unknown_start_time>"
        self._finish_time = "<unknown_finish_time>"
        self._aborted = False
        self._user = "<unknown_user>"
        self._version = "<unknown_version>"
        self._uname = "<unknown_uname>"
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


    def WriteAnnotation(self, key, value):

        if key == "qmtest.run.start_time":
            self._start_time, self._start_date \
                              = self._TETFormatTime(value)
        elif key == "qmtest.run.end_time":
            self._finish_time, self._finish_data \
                               = self._TETFormatTime(value)
        elif key == "qmtest.run.aborted" and value == "true":
            self._aborted = True
        elif key == "qmtest.run.user":
            self._user = value
        elif key == "qmtest.run.version":
            self._version = "qmtest-" + value
        elif key == "qmtest.run.uname":
            self._uname = value
        else:
            self._settings[key] = value


    def _WriteInitialStuff(self):
        """Print TET header information, but only on first call.

        Second and later calls are no-ops."""

        if self._printed_initial_stuff:
            return

        # Test case controller start
        # 0 | version time date | who
        self._WriteLine(0,
                        "%s %s %s" % (self._version,
                                      self._start_time,
                                      self._start_date),
                        "User: " + qm.common.get_username())
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
        self._WriteLine(10,
                        "%i %s 00:00:00"
                        % (self._tcc_number, result.GetId()),
                        "")

    def _WriteResultAnnotations(self, result, seq_start=1):
        """Writes out annotations for a 'result' in TET format.

        Annotations are represented as (sequences of) "test case
        information" lines.

        'result' -- The 'Result' whose annotations should be written.

        'seq_start' -- The TET test case information sequence number to
        start with."""

        seqnum = seq_start
        for key, value in result.items():
            for line in value.split("\n"):
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
                                "%i 0 0 1 %i" % (self._tcc_number, seqnum),
                                "%s: %s" % (key, line))
                seqnum += 1


    def _WriteDejaGNUResult(self, result):
        """Write out a result that has DejaGNU subtest information."""

        self._WriteTCStart(result)
        
        # Get the DejaGNU annotations in sorted order.
        keys = filter(lambda k: k.startswith(DejaGNUTest.RESULT_PREFIX),
                      result.keys())
        keys.sort(lambda k1, k2: cmp(int(k1[len(DejaGNUTest.RESULT_PREFIX):]),
                                     int(k2[len(DejaGNUTest.RESULT_PREFIX):])))

        self._WriteResultAnnotations(result)
                
        purpose = 1
        for k in keys:
            r = result[k]
            outcome = r[:r.find(":")]
            # Test purpose start
            # 200 | activity_number test_purpose_number time | text
            self._WriteLine(200,
                            "%i %i 00:00:00"
                            % (self._tcc_number, purpose),
                            "")
            outcome_num, outcome_name \
                         = { DejaGNUTest.PASS: self.PASS,
                             DejaGNUTest.XPASS: self.PASS,
                             DejaGNUTest.FAIL: self.FAIL,
                             DejaGNUTest.XFAIL: self.FAIL,
                             DejaGNUTest.WARNING: self.NORESULT,
                             DejaGNUTest.ERROR: self.NORESULT,
                             DejaGNUTest.UNTESTED: self.UNTESTED,
                             DejaGNUTest.UNRESOLVED: self.UNRESOLVED,
                             DejaGNUTest.UNSUPPORTED: self.UNSUPPORTED,
                           }[outcome]
            # Test purpose result
            # 220 | activity_number tp_number result time | result-name
            self._WriteLine(220,
                            "%i %i %i 00:00:00"
                            % (self._tcc_number, purpose, outcome_num),
                            outcome_name)
            if outcome == DejaGNUTest.WARNING:
                # Test case information
                # 520 | activity_num tp_num context block sequence | text
                # (see _WriteResultAnnotations for details)
                self._WriteLine(520,
                                "%i %i 0 1 1" % (self._tcc_number,
                                                 purpose),
                                "WARNING")
            if outcome == DejaGNUTest.ERROR:
                # Test case controller message
                # 50 || text describing problem
                # (see _WriteResultAnnotations for details)
                self._WriteLine(520,
                                "%i %i 0 1 1" % (self._tcc_number,
                                                 purpose),
                                "ERROR")

            purpose += 1
            
        # Test case end
        # 80 | activity_number completion_status time | text
        # "completion status" appears undocumented; it is zero in all of
        # the documented examples.
        self._WriteLine(80,
                        "%i 0 00:00:00" % self._tcc_number,
                        "")

            
    def _WriteTestResult(self, result):
        """Write out a result that does not have DejaGNU annotations."""

        self._WriteTCStart(result)
        # Test purpose start
        # 200 | activity_number test_purpose_number time | text
        self._WriteLine(200, "%i 0 00:00:00" % self._tcc_number, "")

        outcome_num, outcome_name = { Result.FAIL: self.FAIL,
                                      Result.PASS: self.PASS,
                                      Result.UNTESTED: self.UNTESTED,
                                      Result.ERROR: self.NORESULT,
                                    }[result.GetOutcome()]
        # Test purpose result
        # 220 | activity_number tp_number result time | result-name
        self._WriteLine(220,
                        "%i 0 %i 00:00:00"
                        % (self._tcc_number, outcome_num),
                        outcome_name)

        if result.GetOutcome() == Result.ERROR:
            # Test case controller message
            # 50 || text describing problem
            # (see _WriteResultAnnotations for details)
            self._WriteLine(520,
                            "%i 0 0 1 1" % self._tcc_number,
                            "ERROR in test " + result.GetId())
            self._WriteResultAnnotations(result, 2)
        else:
            self._WriteResultAnnotations(result)

        # Test case end
        # 80 | activity_number completion_status time | text
        # "completion status" appears undocumented; it is zero in all of
        # the documented examples.
        self._WriteLine(80,
                        "%i 0 00:00:00" % self._tcc_number,
                        "")


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
