##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Location framework interfaces

$Id: interfaces.py 30654 2005-06-06 08:17:36Z dominikhuber $
"""
__docformat__ = 'restructuredtext'

from zope.interface import Interface, Attribute
from zope import schema


class ILocation(Interface):
    """Objects that have a structural location"""

    __parent__ = Attribute("The parent in the location hierarchy")

    __name__ = schema.TextLine(
        title=u"The name within the parent",
        description=u"Traverse the parent with this name to get the object.",
        required=False,
        default=None)


class ISublocations(Interface):
    """Provide access to sublocations."""

    def sublocations():
        """Return sublocations

        An iterable of objects whose __parent__ is the object
        providing the interface is returned.
        """
