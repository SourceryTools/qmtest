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

import common
import os
import qm
import signal
import string
import sys

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

    # FIXME: Security.
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
