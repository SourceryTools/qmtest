##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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
"""Browser Simulator for Functional DocTests

$Id: __init__.py 41678 2006-02-18 20:59:24Z benji_york $
"""

try:
    from testing import Browser
    from zope.deprecation import deprecated
    deprecated('Browser',
        'importing Browser from zope.testbrowser has been deprecated and will'
        ' be removed in 3.5; import Browser from zope.testbrowser.testing'
        ' instead')
except ImportError:
    # This is really ugly, but non-Zope code needs to be able to import this
    # and the testing module depends on Zope 3
    pass
