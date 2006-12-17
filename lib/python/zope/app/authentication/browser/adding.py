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
"""Adding that redirects to plugins.html.

$Id: adding.py 69215 2006-07-19 22:00:21Z jim $
"""

from zope.app import zapi

import zope.app.container.browser.adding

class Adding(zope.app.container.browser.adding.Adding):
    
    def nextURL(self):
        return zapi.absoluteURL(self.context, self.request
                                ) + '/@@contents.html'
