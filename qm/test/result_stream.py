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
    
    """

    kind = "result_stream"

    arguments = [
        qm.fields.PythonField(
           name = "expected_outcomes"),
        qm.fields.PythonField(
           name = "database"),
        ]
    
    def WriteAnnotation(self, key, value):
        """Output an annotation for this run.

        Subclasses should override this if they want to store/display
        annotations; the default implementation simply discards them.

        'key' -- the key value as a string.

        'value' -- the value of this annotation as a string."""

        pass
    

    def WriteAllAnnotations(self, annotations):
        """Output all annotations in 'annotations' to this stream.

        Currently this is the same as making repeated calls to
        'WriteAnnotation', but in the future, as special annotation
        types like timestamps are added, this will do the work of
        dispatching to functions like 'WriteTimestamp'.

        Should not be overridden by subclasses."""

        for key, value in annotations.iteritems():
            self.WriteAnnotation(key, value)


    def WriteResult(self, result):
        """Output a test result.

        Subclasses must override this method; the default
        implementation raises a 'NotImplementedError'.

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
        
