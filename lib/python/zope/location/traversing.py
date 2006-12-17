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
"""Classes to support implenting IContained

$Id: traversing.py 66596 2006-04-06 17:12:03Z philikon $
"""
import zope.component
import zope.interface
from zope.traversing.interfaces import IPhysicallyLocatable
from zope.traversing.interfaces import IContainmentRoot, ITraverser
from zope.traversing.api import getParents
from zope.location.interfaces import ILocation
from zope.location.location import Location
from zope.app.component.interfaces import ISite

class LocationPhysicallyLocatable(object):
    """Provide location information for location objects
    """
    zope.component.adapts(ILocation)
    zope.interface.implements(IPhysicallyLocatable)

    def __init__(self, context):
        self.context = context

    def getRoot(self):
        """Get the root location for a location.

        See IPhysicallyLocatable

        The root location is a location that contains the given
        location and that implements IContainmentRoot.

        >>> root = Location()
        >>> zope.interface.directlyProvides(root, IContainmentRoot)
        >>> LocationPhysicallyLocatable(root).getRoot() is root
        1

        >>> o1 = Location(); o1.__parent__ = root
        >>> LocationPhysicallyLocatable(o1).getRoot() is root
        1

        >>> o2 = Location(); o2.__parent__ = o1
        >>> LocationPhysicallyLocatable(o2).getRoot() is root
        1

        We'll get a TypeError if we try to get the location fo a
        rootless object:

        >>> o1.__parent__ = None
        >>> LocationPhysicallyLocatable(o1).getRoot()
        Traceback (most recent call last):
        ...
        TypeError: Not enough context to determine location root
        >>> LocationPhysicallyLocatable(o2).getRoot()
        Traceback (most recent call last):
        ...
        TypeError: Not enough context to determine location root

        If we screw up and create a location cycle, it will be caught:

        >>> o1.__parent__ = o2
        >>> LocationPhysicallyLocatable(o1).getRoot()
        Traceback (most recent call last):
        ...
        TypeError: Maximum location depth exceeded, """ \
                """probably due to a a location cycle.
        """
        context = self.context
        max = 9999
        while context is not None:
            if IContainmentRoot.providedBy(context):
                return context
            context = context.__parent__
            max -= 1
            if max < 1:
                raise TypeError("Maximum location depth exceeded, "
                                "probably due to a a location cycle.")

        raise TypeError("Not enough context to determine location root")

    def getPath(self):
        """Get the path of a location.

        See IPhysicallyLocatable

        This is an "absolute path", rooted at a root object.

        >>> root = Location()
        >>> zope.interface.directlyProvides(root, IContainmentRoot)
        >>> LocationPhysicallyLocatable(root).getPath()
        u'/'

        >>> o1 = Location(); o1.__parent__ = root; o1.__name__ = 'o1'
        >>> LocationPhysicallyLocatable(o1).getPath()
        u'/o1'

        >>> o2 = Location(); o2.__parent__ = o1; o2.__name__ = u'o2'
        >>> LocationPhysicallyLocatable(o2).getPath()
        u'/o1/o2'

        It is an error to get the path of a rootless location:

        >>> o1.__parent__ = None
        >>> LocationPhysicallyLocatable(o1).getPath()
        Traceback (most recent call last):
        ...
        TypeError: Not enough context to determine location root

        >>> LocationPhysicallyLocatable(o2).getPath()
        Traceback (most recent call last):
        ...
        TypeError: Not enough context to determine location root

        If we screw up and create a location cycle, it will be caught:

        >>> o1.__parent__ = o2
        >>> LocationPhysicallyLocatable(o1).getPath()
        Traceback (most recent call last):
        ...
        TypeError: Maximum location depth exceeded, """ \
                """probably due to a a location cycle.

        """

        path = []
        context = self.context
        max = 9999
        while context is not None:
            if IContainmentRoot.providedBy(context):
                if path:
                    path.append('')
                    path.reverse()
                    return u'/'.join(path)
                else:
                    return u'/'
            path.append(context.__name__)
            context = context.__parent__
            max -= 1
            if max < 1:
                raise TypeError("Maximum location depth exceeded, "
                                "probably due to a a location cycle.")

        raise TypeError("Not enough context to determine location root")

    def getName(self):
        """Get a location name

        See IPhysicallyLocatable.

        >>> o1 = Location(); o1.__name__ = 'o1'
        >>> LocationPhysicallyLocatable(o1).getName()
        'o1'

        """
        return self.context.__name__

    def getNearestSite(self):
        """return the nearest site, see IPhysicallyLocatable"""
        if ISite.providedBy(self.context):
            return self.context
        for parent in getParents(self.context):
            if ISite.providedBy(parent):
                return parent
        return self.getRoot()
