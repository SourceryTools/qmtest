########################################################################
#
# File:   platform.py
# Author: Alex Samuel
# Date:   2001-04-30
#
# Contents:
#   Platform-specific code.
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
import string
import sys

########################################################################
# classes
########################################################################

class MailError(RuntimeError):

    pass



########################################################################
# Linux
########################################################################

if sys.platform[:5] == "linux":

    ####################################################################
    # classes
    ####################################################################

    # Place class definitions here.

    ####################################################################
    # functions
    ####################################################################

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


########################################################################
# Win32
########################################################################

elif sys.platform == "win32":

    ####################################################################
    # classes
    ####################################################################

    # Place class definitions here.

    ####################################################################
    # functions
    ####################################################################

    def open_in_browser(url):
        # FIXME.
        raise NotImplementedError, "open_in_browser on win32"


########################################################################

else:
    raise RuntimeError, "unsupported platform: %s" % sys.platform

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
