########################################################################
#
# File:   regression_test.py
# Author: Alex Samuel
# Date:   2000-12-20
#
# Contents:
#   Very simple provisional regression test framework for qm components
#   to tie us over until qmtest is up and running.
#
# Copyright (c) 2000 by CodeSourcery, LLC.  All rights reserved. 
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
# imports
########################################################################

import getopt
import string
import sys
import traceback

########################################################################
# functions
########################################################################

def run_regression_test_driver(regression_tests):
    """Run regression tests and exit.

    Each regression test is a callable object that takes zero
    arguments, and returns a true value if the test passes or a false
    value if the test failes.  Exits the program with a zero exit code
    if all tests pass, or with a non-zero exit code if some tests
    fail.

    'regression_tests' -- A sequence of regression tests."""

    keep_going = 0
    verbosity = 0

    # Parse command-line options.
    options, args = getopt.getopt(sys.argv[1:], "kv")
    for option, option_arg in options:
        if option == "-k":
            keep_going = 1
        elif option == "-v":
            verbosity = verbosity + 1

    def message(min_verbosity, message_text, verbosity=verbosity):
        if verbosity >= min_verbosity:
            sys.stdout.write(message_text)

    # Count failures.
    failures = 0
    # Run tests.
    for test in regression_tests:
        # Invoke the test, handling all exceptions.
        try:
            result = apply(test, ())
            exception = None
        except:
            exception = sys.exc_info()
            
        # Print the result.
        message(1, "test %-40s: " % ('"' + test.__name__ + '"'))
        if exception != None:
            # The test raised an unhandled exception.  Print a
            # traceback and the exception info.
            message(1, "unhandled exception\n")
            message(2, "Traceback:\n"
                    + string.join(traceback.format_tb(exception[2]), "")
                    + "\n%s: %s\n" % (exception[0], exception[1]))
            failures = failures + 1
            # Don't continue past an exception, unless asked to.
            if not keep_going:
                break
        elif result:
            message(1, "passed\n")
        else:
            message(1, "failed\n")
            failures = failures + 1

    # Exit with a non-zero code if some tests failed.
    if failures > 0:
        exit_code = 1
    else:
        exit_code = 0
    sys.exit(exit_code)
        

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
