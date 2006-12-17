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
"""Fake Traverser with interfaces.

$Id: sampleinterfaces.py 67630 2006-04-27 00:54:03Z jim $
"""
from zope.interface import Interface, implements
from zope.traversing.interfaces import ITraverser

class FakeTraverser(object):

    implements(ITraverser)

    def __init__(self, *args, **kw): pass

    def traverse(self, *args, **kw):
        return None


class I1(Interface): pass
class I2(I1): pass

class O1(object):
    implements(I1)

class O2(object):
    implements(I2)
