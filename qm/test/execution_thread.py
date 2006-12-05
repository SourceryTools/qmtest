########################################################################
#
# File:   execution_thread.py
# Author: Mark Mitchell
# Date:   2001-08-04
#
# Contents:
#   Code for coordinating the running of tests.
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
########################################################################

########################################################################
# Imports
########################################################################

import os
import qm.common
from   qm.test.base import *
from   qm.test.context import *
from   qm.test.execution_engine import *
import qm.xmlutil
import Queue
from   result import *
import sys
from   threading import *

########################################################################
# Classes
########################################################################

class ExecutionThread(Thread, ExecutionEngine):
    """A 'ExecutionThread' executes tests in a separate thread.

    A 'ExecutionThread' is an 'ExecutionEngine' that runs tests in a
    separate thread.

    This class schedules the tests, plus the setup and cleanup of any
    resources they require, across one or more targets.

    The shedule is determined dynamically as the tests are executed
    based on which targets are idle and which are not.  Therefore, the
    testing load should be reasonably well balanced, even across a
    heterogeneous network of testing machines."""
    
    def __init__(self,
                 database,
                 test_ids,
                 context,
                 targets,
                 result_streams = None):
        """Set up a test run.

        'database' -- The 'Database' containing the tests that will be
        run.
        
        'test_ids' -- A sequence of IDs of tests to run.  Where
        possible, the tests are started in the order specified.

        'context' -- The context object to use when running tests.

        'targets' -- A sequence of 'Target' objects, representing
        targets on which tests may be run.

        'result_streams' -- A sequence of 'ResultStream' objects.  Each
        stream will be provided with results as they are available.
        This thread will not perform any locking of these streams as
        they are written to; each stream must provide its own
        synchronization if it will be accessed before 'run' returns."""

        Thread.__init__(self, None, None, None)
        ExecutionEngine.__init__(self, database, test_ids, context,
                                 targets, result_streams)

        # This is a deamon thread; if the main QMTest thread exits,
        # this thread should not prolong the life of the process.
        # Because the daemon flag is inherited from the creating thread,
        # threads created by the targets will automatically be daemon
        # threads.
        self.setDaemon(1)

        # Access to __terminated is guarded with this lock.
        self.__lock = Lock()


    def run(self):
        """Run the tests.

        This method runs the tests specified in the __init__
        function."""
        self.Run()


    def RequestTermination(self):
        """Request termination.

        Request that the execution thread be terminated.  This may
        take some time; tests that are already running will continue
        to run, for example."""

        self.__lock.acquire()
        ExecutionEngine.RequestTermination(self)
        self.__lock.release()


    def IsTerminationRequested(self):
        """Returns true if termination has been requested.

        return -- True if Terminate has been called."""

        self.__lock.acquire()
        terminated = ExecutionEngine.IsTerminationRequested(self)
        self.__lock.release()
        return terminated

    
########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
