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
"""Browser Views for Interface Types

$Id$
"""
__docformat__ = 'restructuredtext'
from type import TypeInterface

from zope.security.proxy import isinstance, removeSecurityProxy
from zope.traversing.api import getName

class Menu(object):
    """Menu View Helper Class"""

    def getMenuTitle(self, node):
        """Return the title of the node that is displayed in the menu."""
        if isinstance(node.context, TypeInterface):
            iface = node.context.interface
        else:
            iface = node.context
        # Interfaces have no security declarations, so we have to unwrap.
        return removeSecurityProxy(iface).getName()

    def getMenuLink(self, node):
        """Return the HTML link of the node that is displayed in the menu."""
        return '../Interface/%s/index.html' % getName(node.context)
