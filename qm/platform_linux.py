########################################################################
#
# File:   platform_linux.py
# Author: Alex Samuel
# Date:   2001-05-13
#
# Contents:
#   Platform-specific function for Linux.
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

class SignalException(Exception):
    """An exception raised in response to a signal."""

    def __init__(self, signal_number):
        """Create a new signal exception.

        'signal_number' -- The signal number."""

        # Construct a text argument for the exception.
        message = "signal %d" % signal_number
        # Include the signal name, if available.
        signal_name = get_signal_name(signal_number)
        if signal_name is not None:
            message = message + " (%s)" % signal_name
        # Initialize the base class.
        RuntimeError.__init__(self, message)
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
    url = string.replace(url, "'", r"\'")
    # Which browser to use?
    browser = common.rc.Get("browser", "netscape", "common")
    if not os.access(browser, os.X_OK):
        raise RuntimeError, \
              qm.error("browser error", browser_path=browser)
    # Invoke the browser.
    exit_code = os.system("%s '%s' &" % (browser, url))


def send_email(body,
               subject,
               recipients,
               ccs=[],
               bccs=[],
               from_address=None,
               attachments=[],
               headers={}):
    """Send an email message.

    'body' -- The message body text.

    'subject' -- The message subject.

    'recipients' -- A sequence of email addresses of message
    recipients.

    'ccs' -- A sequence of email addresses of recipients of carbon
    copies.

    'bccs' -- A sequence of email addresses of recipients of blind
    carbon copies.

    'from_address' -- The message's originating address.  If 'None',
    the system will fill in the sending user's address.

    'attachments' -- A sequence of email attachments.  Each
    attachment is a triplet of '(description, MIME type,
    attachment_data)'. 

    'headers' -- Additional RFC 822 headers in a map.  Keys are
    header names and values are corresponding header contents."""

    if len(attachments) > 0:
        # FIXME: implement this.
        raise NotImplementedError, "attachments not implemented"

    # Figure out which sendmail (or equivalent) to use.
    sendmail_path = common.rc.Get("sendmail", "/usr/sbin/sendmail",
                                  "common")
    # Make sure it exists and is executable.
    if not os.access(sendmail_path, os.X_OK):
        raise RuntimeError, \
              qm.error("sendmail error",
                       sendmail_path=sendmail_path)

    # Start a sendmail process.
    addresses = map(lambda a: "'%s'" % a, recipients + ccs + bccs)
    sendmail_command = sendmail_path + " " + string.join(addresses, " ")
    sendmail = os.popen(sendmail_command, "w")

    # Construct and send the entire RFC 822 message.
    if from_address is not None:
        sendmail.write("From: %s\n" % from_address)
    sendmail.write("To: %s\n" % string.join(recipients, ", "))
    if len(ccs) > 0:
        sendmail.write("Cc: %s\n" % string.join(ccs, ", "))
    if len(bccs) > 0:
        sendmail.write("Bcc: %s\n" % string.join(bccs, ", "))
    for name, value in headers.items():
        sendmail.write("%s: %s\n" % (name, value))
    sendmail.write("Subject: %s\n" % subject)
    sendmail.write("\n")
    sendmail.write(body)

    # Finish up.
    exit_code = sendmail.close()
    if exit_code is not None:
        raise MailError, "%s returned with exit code %d" \
              % (sendmail_path, exit_code)


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


########################################################################
# initialization
########################################################################

def _initialize():
    """Perform module initialization."""

    # Install signal handlers for several common signals.
    map(install_signal_handler,
        [
        signal.SIGALRM,
        signal.SIGHUP,
        signal.SIGTERM,
        signal.SIGUSR1,
        signal.SIGUSR2,
        ])
        

_initialize()

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
