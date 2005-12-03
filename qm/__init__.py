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
    if sys.platform != "win32":
        # On non-Windows platforms, the values written out at
        # installation time are accurate.
        from qm.config import data_dir
        from qm.config import extension_path
    else:
        # On Windows, Distutils does a mock installation and then
        # creates a binary installer.  Unfortunately, at the time
        # the mock installation is performed there is no way to know
        # the eventual paths.  Therefore, the value indicated in
        # config.py are incorrect.  The value given below corresponds
        # to the behavior of the binary installer.
        data_dir = os.path.join("share", "qm")
        extension_path = os.path.join("share", "qm", "site-extensions")
except:
    # If qm.config was not available, we are running out of the source tree.
    common.is_installed = 0
    from qm.__version import version, version_info
    data_dir = "share"
    extension_path = os.path.join("test", "classes")
    
########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
