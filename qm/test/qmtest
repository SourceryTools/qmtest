#! /usr/bin/env python

########################################################################
#
# File:   qmtest
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

########################################################################
# Check Python Version
########################################################################

# Before doing anything else, check that the version of Python in use
# is sufficiently recent.  All code in this section should be portable
# even to old versions of Python.

import sys

def check_python_version():
    """Check to see if the Python interpreter in use is acceptable.

    If the Python interpreter is not sufficiently recent, issue an
    error message and exit."""

    required_python_version = (2, 2)

    # Get the version of Python in use.
    try:
        actual_version = sys.version_info
    except:
        # Older versions of Python do not have "sys.version_info".
        actual_version = (0, 0, 0, 0)

    old = 0
    for i in range(len(required_python_version)):
        if required_python_version[i] > actual_version[i]:
            old = 1

    if old:
        if len(required_python_version) == 2:
            version = "%d.%d" % required_python_version
        else:
            version = "%d.%d.%d" % required_python_version
        sys.stderr.write(
            ("QMTest requires Python %s or later.\n"
             "Set the QM_PYTHON environment variable to an appropriate "
             "Python interpreter.\n") % version)
        sys.exit(1)

check_python_version()

########################################################################
# Imports
########################################################################

import errno
import gc
import os
import os.path
import string
import traceback

# The Python interpreter will place the directory containing this
# script in the default path to search for modules.  That is
# unncessary for QMTest, and harmful, since then "import resource"
# imports the resource module in QMTest, not the global module of
# the same name.
sys.path = sys.path[1:]

rel_prefix = os.path.join(os.pardir, os.pardir)
"""The relative path to the installation prefix.

This string gives the relative path from the directory containing this
script to the installation directory.  The value above is correct when
QMTest is being run out of the source tree.  When QMTest is installed,
this value is updated appropriately."""

# Get the path to this script.
qm_path = os.path.abspath(sys.argv[0])

# Get the root of the QMTest installation.
qm_home = os.environ.get("QM_HOME")
if qm_home is None:
    # Get the path to the installation directory.
    qm_home = os.path.normpath(os.path.join(os.path.dirname(qm_path),
                                            rel_prefix))

# Update sys.path so that we can find the rest of QMTest.
if sys.platform != "win32":
    # Following logic stolen from distutils.command.build:
    import distutils.util
    plat_spec = "lib.%s-%s" % (distutils.util.get_platform(),
                               sys.version[0:3])
    rel_libdir = os.path.join("build", plat_spec)
    """The relative path from the prefix to the library directory.

    This path gives the relative path from the prefix to the library
    directory.  The value above is correct when QMTest is being run out of
    the source tree.  When QMTest is installed, this value is updated
    appropriately."""

    libdir = os.path.normpath(os.path.join(qm_home, rel_libdir))
    if libdir not in sys.path:
        sys.path.insert(0, libdir)
else:
    # On Windows, the value computed for rel_libdir is incorrect because
    # Distutils does a mock pre-installation using different directory
    # names than are used by the binary installer.  On Windows, however,
    # the QM module files are installed into a location that is already in
    # sys.path.
    pass

import qm

# Set the prefix variable so that the rest of QMTest can find
# documentation files, test classes, and so forth.
qm.prefix = qm_home

import qm.cmdline
import qm.diagnostic
import qm.platform
import qm.structured_text
import qm.test.cmdline
if sys.platform != "win32":
    import qm.sigmask

########################################################################
# Functions
########################################################################

def print_error_message(message):
    """Output an error message.

    'message' -- Structured text for the error message to emit.  The
    messing is emitted to the standard error stream with an
    identifying prefix."""
    
    prefix = "qmtest: error: "
    message = qm.structured_text.to_text(str(message),
                                         indent=len(prefix))
    message = prefix + message[len(prefix):]
    sys.stderr.write(message)


def main():
    """Run QMTest.

    returns -- The exit code that should be provided to the operating
    system."""
    
    # Save the initial signal mask, as early as possible.
    if sys.platform != "win32":
        qm.sigmask.save_mask()

    # Parse the command line.
    command = qm.test.cmdline.QMTest(sys.argv[1:], qm_path)

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
        raise
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
