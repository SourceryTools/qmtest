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

class TextFile(object):
    """This class represents a function declared in the module."""
    implements(ILocation)

    def __init__(self, path, name, package):
        self.path = path
        self.__parent__ = package
        self.__name__ = name

    def getContent(self):
        file = open(self.path, 'rU')
        content = file.read()
        file.close()
        return content.decode('utf-8')
