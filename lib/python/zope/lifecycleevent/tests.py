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
"""Object Event Tests

$Id: tests.py 66903 2006-04-12 20:17:53Z philikon $
"""
import unittest
import zope.component.testing
from zope.testing import doctest
from zope.lifecycleevent import ObjectModifiedEvent

class TestObjectModifiedEvent(unittest.TestCase):

    klass = ObjectModifiedEvent
    object = object()

    def setUp(self):
        self.event = self.klass(self.object)

    def testGetObject(self):
        self.assertEqual(self.event.object, self.object)

def setUpDoctest(test):
    from zope.annotation.attribute import AttributeAnnotations
    from zope.dublincore.interfaces import IWriteZopeDublinCore
    from zope.dublincore.annotatableadapter import ZDCAnnotatableAdapter
    zope.component.provideAdapter(AttributeAnnotations)
    zope.component.provideAdapter(ZDCAnnotatableAdapter,
                                  provides=IWriteZopeDublinCore)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestObjectModifiedEvent),
        doctest.DocFileSuite('README.txt', setUp=setUpDoctest,
                             tearDown=zope.component.testing.tearDown),
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
