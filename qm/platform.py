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
# initialization
########################################################################

if sys.platform[:5] == "linux" \
   or  sys.platform[:4] == "irix":
    from platform_unix import *

elif sys.platform == "win32":
    from platform_win32 import *

    def open_in_browser(url):
        # FIXME.
        raise NotImplementedError, "open_in_browser on win32"

else:
    raise RuntimeError, "unsupported platform: %s" % sys.platform

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
