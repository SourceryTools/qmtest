########################################################################
#
# File:   platform_unix.py
# Author: Alex Samuel
# Date:   2001-05-13
#
# Contents:
#   Platform-specific function for UNIX and UNIX-like systems.
#
# Copyright (c) 2001, 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

import base64
import common
import cPickle
import cStringIO
import os
import posix
import qm
import quopri
import select
import signal
import string
import sys
import traceback

########################################################################
# constants
########################################################################

if sys.platform[:5] == "linux":
    # GNU/Linux systems generally use 'bash' as the default shell.
    # Invoke it with options to inhibit parsing of user startup files.
    default_shell = ["/bin/bash", "-norc", "-noprofile"]
else:
    # Other UNIX systems use the Bourne shell.
    default_shell = ["/bin/sh"]


########################################################################
# classes
########################################################################

class SignalException(common.QMException):
    """An exception raised in response to a signal."""

    def __init__(self, signal_number):
        """Create a new signal exception.

        'signal_number' -- The signal number."""

        # Construct a text argument for the exception.
        message = "Signal %d" % signal_number
        # Include the signal name, if available.
        signal_name = get_signal_name(signal_number)
        if signal_name is not None:
            message = message + " (%s)" % signal_name
        # Initialize the base class.
        common.QMException.__init__(self, message)
        # Store the signal number.
        self.__signal_number = signal_number


    def GetSignalNumber(self):
        """Return the number of the signal that caused this exception."""

        return self.__signal_number



########################################################################
# functions
########################################################################

def open_in_browser(url):
    """Open a browser window and point it at 'url'.

    The browser is run in a separate, independent process."""

    # Escape single quotes in the URL.
    url = string.replace(url, "'", "%27")
    # Which browser to use?
    browser = common.rc.Get("browser", "mozilla", "common")
    # Invoke the browser.
    os.system("%s '%s' &" % (browser, url))


def get_signal_name(signal_number):
    """Return the name for signal 'signal_number'.

    returns -- The signal's name, or 'None'."""

    # A hack: look for an attribute in the 'signal' module whose
    # name starts with "SIG" and whose value is the signal number.
    for attribute_name in dir(signal):
        if len(attribute_name) > 3 \
           and attribute_name[:3] == "SIG" \
           and getattr(signal, attribute_name) == signal_number:
            return attribute_name
    # No match.
    return None


def install_signal_handler(signal_number):
    """Install a handler to translate a signal into an exception.

    The signal handler raises a 'SignalException' exception in
    response to a signal."""

    signal.signal(signal_number, _signal_handler)


def _signal_handler(signal_number, execution_frame):
    """Generic signal handler that raises an exception."""

    raise SignalException(signal_number)


def get_host_name():
    """Return the name of this computer."""

    return posix.uname()[1]

########################################################################
# initialization
########################################################################

def _initialize():
    """Perform module initialization."""

    # Install signal handlers for several common signals.
    for s in (signal.SIGALRM,
              signal.SIGHUP,
              signal.SIGTERM,
              signal.SIGUSR1,
              signal.SIGUSR2):
        install_signal_handler(s)

_initialize()

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

