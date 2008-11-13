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
"""BTree Container Tests

$Id: test_btree.py 77225 2007-06-29 09:20:13Z dobe $
"""
from unittest import TestCase, main, makeSuite, TestSuite
from zope.testing.doctestunit import DocTestSuite
from zope.app.testing import placelesssetup
from test_icontainer import TestSampleContainer
from zope.app.container.btree import BTreeContainer

class TestBTreeContainer(TestSampleContainer, TestCase):

    def makeTestObject(self):
        return BTreeContainer()

class TestBTreeLength(TestCase):

    def testStoredLength(self):
        #This is lazy for backward compatibility. If the len is not
        #stored already we set it to the length of the underlying
        #btree.
        bc = BTreeContainer()
        self.assertEqual(bc.__dict__['_BTreeContainer__len'](), 0)
        del bc.__dict__['_BTreeContainer__len']
        self.failIf(bc.__dict__.has_key('_BTreeContainer__len'))
        bc['1'] = 1
        self.assertEqual(len(bc), 1)
        self.assertEqual(bc.__dict__['_BTreeContainer__len'](), 1)


def test_suite():
    return TestSuite((
        makeSuite(TestBTreeContainer),
        makeSuite(TestBTreeLength),
        DocTestSuite('zope.app.container.btree',
                     setUp=placelesssetup.setUp,
                     tearDown=placelesssetup.tearDown),
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')
