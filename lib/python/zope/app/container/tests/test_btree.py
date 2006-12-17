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

$Id: test_btree.py 29143 2005-02-14 22:43:16Z srichter $
"""
from unittest import TestCase, main, makeSuite, TestSuite
from zope.testing.doctestunit import DocTestSuite
from zope.app.testing import placelesssetup
from test_icontainer import TestSampleContainer

class TestBTreeContainer(TestSampleContainer, TestCase):

    def makeTestObject(self):
        from zope.app.container.btree import BTreeContainer
        return BTreeContainer()


def test_suite():
    return TestSuite((
        makeSuite(TestBTreeContainer),
        DocTestSuite('zope.app.container.btree',
                     setUp=placelesssetup.setUp,
                     tearDown=placelesssetup.tearDown),
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')
