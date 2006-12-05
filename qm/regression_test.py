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
# For license terms see the file COPYING.
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
    """Run regression tests.

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

    return failures
        

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
