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
"""Factory tests.

$Id: factory.py 26551 2004-07-15 07:06:37Z srichter $
"""
from zope.component.interfaces import IFactory
from zope.interface import Interface, implements, implementedBy

class IX(Interface):
    """the dummy interface which class X supposedly implements,
    according to the factory"""

class IFoo(Interface):
    """an even more dummy interface just for testing """

class X(object):
    implements(IX)
    def __init__(self, *args, **kwargs):
        self.args=args
        self.kwargs=kwargs


class ClassFactoryWrapper(object):
    implements(IFactory)
    def __init__(self, klass):
        self.__klass=klass
    def __call__(self, *args, **kwargs):
        return self.__klass(*args, **kwargs)
    def getInterfaces(self):
        return implementedBy(self.__klass)

f=ClassFactoryWrapper(X)
