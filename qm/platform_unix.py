########################################################################
#
# File:   platform_unix.py
# Author: Alex Samuel
# Date:   2001-05-13
#
# Contents:
#   Platform-specific function for UNIX and UNIX-like systems.
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
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
import MimeWriter
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
        message = "signal %d" % signal_number
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
    browser = common.rc.Get("browser", "netscape", "common")
    # Invoke the browser.
    os.system("%s '%s' &" % (browser, url))


def send_email(body_text,
               subject,
               recipients,
               ccs=[],
               bccs=[],
               from_address=None,
               attachments=[],
               headers={}):
    """Send an email message.

    'body_text' -- The message body text.

    'subject' -- The message subject.

    'recipients' -- A sequence of email addresses of message
    recipients.

    'ccs' -- A sequence of email addresses of recipients of carbon
    copies.

    'bccs' -- A sequence of email addresses of recipients of blind
    carbon copies.

    'from_address' -- The message's originating address.  If 'None',
    the system will fill in the sending user's address.

    'attachments' -- A sequence of email attachments.  Each attachment
    is a tuple containing '(description, mime_type, file_name,
    attachment_data)'.  An appropriate encoding is chosen for the data
    based on the MIME type.

    'headers' -- Additional RFC 822 headers in a map.  Keys are
    header names and values are corresponding header contents."""

    # Figure out which sendmail (or equivalent) to use.
    sendmail_path = common.rc.Get("sendmail", "/usr/lib/sendmail",
                                  "common")
    # Make sure it exists and is executable.
    if not os.access(sendmail_path, os.X_OK):
        raise common.QMException, \
              qm.error("sendmail error",
                       sendmail_path=sendmail_path)

    # Start a sendmail process.
    addresses = map(lambda a: "'%s'" % a, recipients + ccs + bccs)
    sendmail_command = sendmail_path + " " + string.join(addresses, " ")
    sendmail = os.popen(sendmail_command, "w")
    message = MimeWriter.MimeWriter(sendmail)

    # Construct mail headers.
    if from_address is not None:
        message.addheader("From", from_address)
    message.addheader("To", string.join(recipients, ", "))
    if len(ccs) > 0:
        message.addheader("CC", string.join(ccs, ", "))
    if len(bccs) > 0:
        message.addheader("BCC", string.join(bccs, ", "))
    for name, value in headers.items():
        message.addheader(name, value)
    message.addheader("Subject", subject)

    # Handle messages with attachments differently.
    if len(attachments) > 0:
        # Set the MIME version header.
        message.addheader("MIME-Version", "1.0")
        # A message with attachments has a content type
        # "multipart/mixed". 
        body = message.startmultipartbody("mixed")

        # The text of the message body goes in the first message part.
        body_part = message.nextpart()
        body_part.addheader("Content-Description", "message body text")
        body_part.addheader("Content-Transfer-Encoding", "7bit")
        body_part_body = body_part.startbody("text/plain")
        body_part_body.write(body_text)

        # Add the attachments, each in a separate message part.
        for attachment in attachments:
            # Unpack the attachment tuple.
            description, mime_type, file_name, data = attachment
            # Choose an encoding based on the MIME type.
            if mime_type == "text/plain":
                # Plain text encoded as-is.
                encoding = "7bit"
            elif mime_type[:4] == "text":
                # Other types of text are encoded quoted-printable.
                encoding = "quoted-printable"
            else:
                # Everything else is base 64-encoded.
                encoding = "base64"
            # Create a new message part for the attachment.
            part = message.nextpart()
            part.addheader("Content-Description", description)
            part.addheader("Content-Disposition",
                           'attachment; filename="%s"' % file_name)
            part.addheader("Content-Transfer-Encoding", encoding)
            part_body = part.startbody('%s; name="%s"'
                                       % (mime_type, file_name))
            # Write the attachment data, encoded appropriately.
            if encoding is "7bit":
                part_body.write(data)
            elif encoding is "quoted-printable":
                quopri.encode(cStringIO.StringIO(data), part_body, quotetabs=0)
            elif encoding is "base64":
                base64.encode(cStringIO.StringIO(data), part_body)

        # End the multipart message. 
        message.lastpart()

    else:
        # If the message has no attachments, don't use a multipart
        # format.  Instead, just write the essage bdoy.
        body = message.startbody("text/plain")
        body.write(body_text)

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


def get_temp_directory():
    """Return the full path to a directory for storing temporary files."""

    return "/var/tmp"


def get_user_name():
    """Return the name user running the current program."""

    # Get the numerical user ID.
    user_id = os.getuid()
    # To convert it to a name, we have to consult the system password file.
    for line in open("/etc/passwd", "r").readlines():
        # Each row is constructed of parts delimited by colons.
        parts = string.split(line, ":")
        # The third element is the user ID.  Does it match?
        if int(parts[2]) == user_id:
            # Yes.  Return the first part, the user name.
            return parts[0]
    # No match.
    raise common.QMException, "user not found in /etc/passwd"


def get_host_name():
    """Return the name of this computer."""

    return posix.uname()[1]

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

