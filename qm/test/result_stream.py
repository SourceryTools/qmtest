########################################################################
#
# File:   result_stream.py
# Author: Mark Mitchell
# Date:   2001-10-10
#
# Contents:
#   QMTest ResultStream class.
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

import qm

########################################################################
# classes
########################################################################

class ResultStream:
    """A 'ResultStream' displays test results.

    A 'ResultStream' is responsible for displaying test results for
    the user as they arrive.  It may also display summary information
    when the results are complete.  The 'ResultStream' may also
    choose to write the results to a file for permanent storage.

    'ResultStream' is an abstract class.
    
    QMTest does not presently have a mechanism for extension in this
    area.  However, in a future release of QMTest, you will be able to
    define your own 'ResultStream'.  A typical reason to extend
    'ResultStream' would be to write out test results in alternative
    file format."""

    def __init__(self):
        """Construct a 'ResultStream'.

        Derived class '__init__' methods must invoke this method."""
        
        pass


    def WriteResult(self, result):
        """Output a test result.

        'result' -- A 'Result'."""

        raise qm.MethodShouldBeOverriddenError, 'ResultStream.WriteResult'


    def Summarize(self):
        """Output summary information about the results.

        When this method is called, the test run is complete.  Summary
        information should be displayed for the user, if appropriate.
        Any finalization, such as the closing of open files, should
        also be performed at this point.

        Derived class methods may override this method.  They should,
        however, invoke this version before returning."""
        
        pass
        
