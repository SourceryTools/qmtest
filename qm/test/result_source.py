########################################################################
#
# File:   result_source.py
# Author: Nathaniel Smith
# Date:   2003-06-23
#
# Contents:
#   QMTest ResultSource class.
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

class ResultSource(qm.extension.Extension):
    """A 'ResultSource' provides access to stored test results.

    For instance, a 'ResultSource' may load 'Result's from a pickle
    file or an XML file.

    This is an abstract class.

    See also 'ResultStream'."""

    kind = "result_source"

    def GetResult(self):
        """Return the next 'Result' from this source.

        returns -- A 'Result', or 'None' if there are no more results.
        """

        raise NotImplementedError


    def __iter__(self):
        """A 'ResultSource' can be iterated over."""

        return iter(self.GetResult, None)

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
