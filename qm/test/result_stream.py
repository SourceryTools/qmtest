########################################################################
#
# File:   result_stream.py
# Author: Mark Mitchell
# Date:   2001-10-10
#
# Contents:
#   QMTest ResultStream class.
#
# Copyright (c) 2001, 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

import qm
import qm.extension
import qm.fields

########################################################################
# classes
########################################################################

class ResultStream(qm.extension.Extension):
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

    kind = "result_stream"

    arguments = [
        qm.fields.PythonField(
           name = "expected_outcomes"),
        qm.fields.PythonField(
           name = "database"),
        qm.fields.PythonField(
           name = "suite_ids"),
        ]
    
    def WriteResult(self, result):
        """Output a test result.

        'result' -- A 'Result'."""

        raise NotImplementedError


    def Summarize(self):
        """Output summary information about the results.

        When this method is called, the test run is complete.  Summary
        information should be displayed for the user, if appropriate.
        Any finalization, such as the closing of open files, should
        also be performed at this point.

        Derived class methods may override this method.  They should,
        however, invoke this version before returning."""
        
        pass
        
