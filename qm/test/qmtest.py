#! /usr/bin/env python

########################################################################
#
# File:   qmtest.py
# Author: Alex Samuel
# Date:   2001-03-15
#
# Contents:
#   QMTest command line application.
#
# Copyright (c) 2001, 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

# Set up the Python module lookup path to find QM.

import errno
import os
import os.path
import sys
import string

# The Python interpreter will place the directory containing this
# script in the default path to search for modules.  That is
# unncessary for QMTest, and harmful, since then "import resource"
# imports the resource module in QMTest, not the global module of
# the same name.
sys.path = sys.path[1:]

########################################################################
# imports
########################################################################

import sys
import gc

# This executable is supposed to live in ${QM_HOME}/bin (posix)
# or ${QM_HOME}\Scripts (nt) so we deduce the QM_HOME variable
# by stripping off the last two components of the path.
#
_qm_home = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
os.environ['QM_HOME']=_qm_home

import qm

class config:
    pass
qm.config = config()
qm.config.data_dir = os.path.join(_qm_home, 'share', 'qm')

import qm.cmdline
import qm.diagnostic
import qm.platform
import qm.structured_text
import qm.test.cmdline
import traceback

########################################################################
# functions
########################################################################

def print_error_message(message):
    prefix = "qmtest: error: "
    message = qm.structured_text.to_text(str(message),
                                         indent=len(prefix))
    message = prefix + message[len(prefix):]
    sys.stderr.write(message)


_required_python_version = (2, 2)
def check_python_version():
    """Check to see if the Python interpreter in use is acceptable.

    If the Python interpreter is not sufficiently recent, issue an
    error message and exit."""

    version_str = ".".join([str(num) for num in _required_python_version])
    message = "Python " + version_str + " or higher is required.\n"
    message += "Set QM_PYTHON to an appropriate Python interpreter.\n"
    try:
        if sys.version_info < _required_python_version:
            print_error_message(message)
            sys.exit(1)
    except AttributeError:
        print_error_message(message)
        sys.exit(1)


def main():
    """Run QMTest.

    returns -- The exit code that should be provided to the operating
    system."""
    
    # Make sure our Python is recent enough.
    check_python_version()

    # Parse the command line.
    command = qm.test.cmdline.QMTest(sys.argv[1:])

    # Execute the command.
    exit_code = command.Execute()

    return exit_code
    
########################################################################
# script
########################################################################

# Assume that something will go wrong.
exit_code = 2

try:
    # Set the program name.
    qm.common.program_name = "QMTest"

    # Load messages.
    qm.diagnostic.load_messages("test")

    # Load RC options.
    qm.rc.Load("test")

    try:
        exit_code = main()
    except qm.cmdline.CommandError, msg:
        print_error_message(msg)
        sys.stderr.write(
            "Run 'qmtest --help' to get instructions about how to use QMTest.\n")
    except qm.common.QMException, msg:
        print_error_message(msg)
    except NotImplementedError:
        exc_info = sys.exc_info()
        method_name = traceback.extract_tb(exc_info[2])[-1][2]
        print_error_message(qm.message("not implemented",
                                       method_name = method_name))
        sys.stderr.write(qm.common.format_traceback(exc_info))
    except KeyboardInterrupt:
        sys.stderr.write("\nqmtest: Interrupted.\n")
    except qm.platform.SignalException, se:
        # SIGTERM indicates a request to shut down.  Other signals
        # should be handled earlier.
        if se.GetSignalNumber() != signal.SIGTERM:
            raise
finally:
    # Collect garbage so that any "__del__" methods with externally
    # visible side-effects are executed.
    del qm.test.cmdline._the_qmtest
    gc.collect()

# End the program.
sys.exit(exit_code)

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
