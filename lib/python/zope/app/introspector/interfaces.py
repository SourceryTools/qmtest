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
"""Introspector interfaces

$Id: interfaces.py 29143 2005-02-14 22:43:16Z srichter $
"""
__docformat__ = 'restructuredtext'

from zope.interface import Interface

class IIntrospector(Interface):
    """An interface for introspecting a component"""

    def isInterface():
        "Checks if the context is class or interface"

    def setRequest(request):
        """sets the request"""

    def getClass():
        """Returns the class name"""

    def getBaseClassNames():
        """Returns the names of the classes"""

    def getModule():
        """Returns the module name of the class"""

    def getDocString():
        """Returns the description of the class"""

    def getInterfaces():
        """Returns interfaces implemented by this class"""

    def getInterfaceNames():
        """Returns the names of the interfaces implemented by this class"""

    def getDirectlyProvided():
        """Returns interfaces directly implemented by an object"""

    def getDirectlyProvidedNames():
        """Returns the names of the interfaces directly implemented by
        an object"""

    def getInterfaceDetails():
        """Returns the entire documentation in the interface"""

    def getExtends():
        """Returns all the class extended up to the top most level"""

    def getMarkerInterfaces():
        """Returns a list of marker interfaces available for this object"""

    def getMarkerInterfaceNames():
        """Returns a list of names of marker interfaces available for this
        object"""
