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
# Imports
########################################################################

from   qm.common import *
from   qm.diagnostic import error, warning, message
import string
import sys
import os

########################################################################
# Variables
########################################################################

try:
    # The config file is created during installation by distutils.
    from qm.config import version
    version_info = tuple(string.split(version, '.'))
    """The version of QM as a tuple of '(major, minor, release)'."""

    # Get the relative paths from the prefix where QMTest was
    # installed to the data directory (where documentation and such
    # is installed) and the library directory (where the Python
    # modules making up QMTest are installed).
    from qm.config import prefix
    from qm.config import data_dir
    from qm.config import doc_dir
    from qm.config import extension_path
except:
    # If qm.config was not available, we are running out of the source tree.
    from qm.__version import version, version_info
    data_dir = os.path.join('share', 'qmtest')
    doc_dir = os.path.join('share', 'doc', 'qmtest')
    extension_path = os.path.join('qm', 'test', 'classes')
    
########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
