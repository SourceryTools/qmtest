########################################################################
#
# File:   trace.py
# Author: Mark Mitchell
# Date:   01/25/2002
#
# Contents:
#   Tracer
#
# Copyright (c) 2002 by CodeSourcery, LLC.  All rights reserved. 
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
# Imports
########################################################################

import os
import sys

########################################################################
# Classes
########################################################################

class Tracer:
    """A 'Tracer' outputs trace messages useful for debugging."""

    prefix = 'QM_THRESHOLD_'
    """The prefix for an environment variable that indicates a
    threshold for a particular trace category.  The string following
    the prefix gives the name of the trace category.  If the
    environment variable has no associated level, the associated level
    is one.  Otherwise, the associated level is given by the value of
    the environment variable."""
    
    def __init__(self, file=sys.stderr):
        """Construct a new 'Tracer'.

        'file' -- The file object to which output should be written."""

        self.__file = file
        self.__thresholds = {}

        # Take any environment variables that begin with QM_THRESHOLD_
        # as the initial values for thresholds.
        keys = filter (lambda key: (key[:len(Tracer.prefix)]
                                    == Tracer.prefix),
                       os.environ.keys())
        for key in keys:
            level = os.environ[key]
            if level:
                level = int(level)
            else:
                level = 1
            self.SetThreshold(key[len(Tracer.prefix):], level)
                              
                                    
    def Write(self, message, category, level=0):
        """Output a trace message.

        'message' -- A string giving the contents of the message.  The
        message should begin with a capital letter and end with a
        period.

        'category' -- A string indicating the category to which this
        message belongs.

        'level' -- A non-negative integer indicating the level at
        which the message should be output.

        Every category has an associated threshold.  If the level of
        the 'message' is less than the threshold, the mesage will be
        output."""

        if level < self.GetThreshold(category):
            self.__file.write("Trace [%s]: %s\n" % (category,
                                                    message))
            self.__file.flush()


    def GetThreshold(self, category):
        """Return the current threshold for 'category'.

        'category' -- A string giving a trace category.

        returns -- The threshold associated with 'category'.  If no
        threshold has been set, the threshold is considered to be
        zero."""

        return self.__thresholds.get(category, 0)


    def SetThreshold(self, category, level):
        """Set the threshold associated with 'category'.

        'category' --A string giving a trace category.

        'level' -- A non-negative integer indicating the threshold
        level for 'category'."""

        self.__thresholds[category] = level
