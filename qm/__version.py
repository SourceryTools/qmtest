########################################################################
#
# File:   __version.py.in
# Author: Nathaniel Smith
# Date:   2003-08-10
#
# Contents:
#   Variables to query the version of QM in use.
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Variables
########################################################################

version_info = (2, 1, 1)
"""The version of QM as a tuple of (major, minor, release)."""

version = "%d.%d" % version_info[:-1]
"""The version of QM as a string suitable for printing."""

if version_info[-1]:
    version += ".%d" % version_info[-1]

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
