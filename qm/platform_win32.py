########################################################################
#
# File:   platform_win32.py
# Author: Alex Samuel
# Date:   2001-05-13
#
# Contents:
#   Platform-specific function for Win32.
#
# Copyright (c) 2001 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

import common
import os
import qm
import signal
import string
import sys

########################################################################
# constants
########################################################################

default_shell = [os.environ.get("COMPSPEC", r"C:\WINNT\SYSTEM32\CMD.EXE")]

########################################################################
# classes
########################################################################

# Win32 doesn't provide signals, but we include this anyway so that code
# may attempt to catch this exception without conditionalizing.

class SignalException(Exception):

    def __init__(self, *args):
        raise NotImplementedError, "No 'SignalException' on Win32."



########################################################################
# functions
########################################################################

def get_user_name():
    """Return the name user running the current program."""

    return os.environ["USERNAME"]


def get_host_name():
    """Return the name of this computer."""

    # This function caches the result of '_get_host_name' by replacing
    # itself with a lambda that returns the cached value.
    global get_host_name
    get_host_name = lambda host_name=_get_host_name(): host_name


def _get_host_name():
    """Return the name of this computer."""

    # First try to look up our own address in DNS.
    try:
        return socket.gethostbyname_ex(socket.gethostname())[0]
    except socket.error:
        pass

    # That didn't work.  Just use the local name.
    try:
        return socket.gethostname()
    except socket.error:
        pass

    # That didn't work either.  Check if the host name is stored in the
    # environment.
    try:
        return os.environ["HOSTNAME"]
    except KeyError:
        pass

    # We're stumped.  Use something dumb.
    return "localhost"


def open_in_browser(url):
    """Open a browser window and point it at 'url'.

    The browser is run in a separate, independent process."""

    os.startfile(url)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
