########################################################################
#
# File:   result_reader.py
# Author: Nathaniel Smith
# Date:   2003-06-23
#
# Contents:
#   QMTest ResultReader class.
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

import qm.extension

########################################################################
# Classes
########################################################################

class ResultReader(qm.extension.Extension):
    """A 'ResultReader' provides access to stored test results.

    For instance, a 'ResultReader' may load 'Result's from a pickle
    file or an XML file.

    This is an abstract class.

    See also 'ResultStream'."""

    kind = "result_reader"

    def GetAnnotations(self):
        """Return this run's dictionary of annotations."""

        # For backwards compatibility, don't raise an exception.
        return {}


    def GetResult(self):
        """Return the next 'Result' from this reader.

        returns -- A 'Result', or 'None' if there are no more results.
        """

        raise NotImplementedError


    def __iter__(self):
        """A 'ResultReader' can be iterated over."""

        return iter(self.GetResult, None)

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
