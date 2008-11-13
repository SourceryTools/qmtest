##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Sample package that knits in extra directories.

$Id: __init__.py 39695 2005-10-28 20:01:54Z jim $
"""

import os

__path__.append(
    os.path.join(
        os.path.dirname( # testing
            os.path.dirname( # testrunner-ex-knit-lib
                os.path.dirname( # sample4
                    os.path.dirname(__file__) # products
                    )
                )
            )
        , "testrunner-ex-pp-products"
        )
    )

