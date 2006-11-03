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

from qm.common import *
from qm.diagnostic import error, warning, message
from qm.config import version
from qm.config import data_dir
from qm.config import doc_dir
from qm.config import extension_path
# The prefix variable is only available after QMTest is built.
# Compute it, if it isn't available.
try:
    from qm.config import prefix
except ImportError:
    import os
    prefix = os.path.join(os.path.dirname(__file__), os.path.pardir)

version_info = tuple(version.split('.'))

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:
