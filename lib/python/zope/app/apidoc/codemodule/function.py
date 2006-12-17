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
"""Function representation for code browser 

$Id: __init__.py 29143 2005-02-14 22:43:16Z srichter $
"""
__docformat__ = 'restructuredtext'

from zope.interface import implements
from zope.location.interfaces import ILocation

from zope.app.apidoc.utilities import getFunctionSignature
from interfaces import IFunctionDocumentation

class Function(object):
    """This class represents a function declared in the module."""
    implements(ILocation, IFunctionDocumentation)

    def __init__(self, module, name, func):
        self.__parent__ = module
        self.__name__ = name
        self.__func = func

    def getPath(self):
        """See IFunctionDocumentation."""
        return self.__parent__.getPath() + '.' + self.__name__

    def getDocString(self):
        """See IFunctionDocumentation."""
        return self.__func.__doc__

    def getSignature(self):
        """See IFunctionDocumentation."""
        return getFunctionSignature(self.__func)

    def getAttributes(self):
        """See IClassDocumentation."""
        return self.__func.__dict__.items()
