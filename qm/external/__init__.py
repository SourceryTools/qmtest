########################################################################
#
# File:   __init__.py
# Author: Nathaniel Smith
# Date:   2003-04-09
#
# Contents:
#   Empty file to make external packages importable.
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

# DocumentTemplate uses regex and regsub, which are obsolete.  Prevent
# Python from warning about these modules.
import warnings
warnings.filterwarnings("ignore",
                        r".*(regex|regsub).*",
                        DeprecationWarning,
                        r".*(DocumentTemplate|regsub).*")

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
