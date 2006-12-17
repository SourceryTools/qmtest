##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""Define view component for ZPT page eval results.

$Id: browser.py 26731 2004-07-23 21:27:21Z pruggera $
"""
__docformat__ = 'restructuredtext'

class DTMLPageEval(object):

    def index(self, REQUEST=None, **kw):
        """Call a Page Template"""

        template = self.context
        return template.render(REQUEST, **kw)
