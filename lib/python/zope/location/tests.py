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
"""Location support tests

$Id: tests.py 66534 2006-04-05 14:09:33Z philikon $
"""
import unittest
import zope.interface
from zope.traversing.interfaces import ITraverser
from zope.testing.doctestunit import DocTestSuite
from zope.location.location import Location

class TLocation(Location):
    """Simple traversable location used in examples."""

    zope.interface.implements(ITraverser)

    def traverse(self, path, default=None, request=None):
        o = self
        for name in path.split(u'/'):
           o = getattr(o, name)
        return o

def test_suite():
    return unittest.TestSuite((
        DocTestSuite('zope.location.location'),
        DocTestSuite('zope.location.traversing'),
        DocTestSuite('zope.location.pickling'),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
