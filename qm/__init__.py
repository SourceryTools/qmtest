########################################################################
#
# File:   __init__.py
# Author: Alex Samuel
# Date:   2000-12-20
#
# Contents:
#   Initialization for module qm.
#
# Copyright (c) 2000 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

import string

try:
    # The config file is created during "make install" by setup.py.
    from qm.config import version
    version_info = tuple(string.split(version, '.'))
    """The version of QM as a tuple of '(major, minor, release)'."""
except:
    # If qm.config was not available, we are running out of the source tree.
    from qm.__version import version, version_info

from qm.common import *
from qm.diagnostic import error, warning, message

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
