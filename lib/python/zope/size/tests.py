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
"""Test ISized Adapter

$Id$
"""
import unittest
from zope.size.interfaces import ISized

class DummyObject(object):

    def __init__(self, size):
        self._size = size

    def getSize(self):
        return self._size

class Test(unittest.TestCase):

    def testImplementsISized(self):
        from zope.size import DefaultSized
        sized = DefaultSized(object())
        self.assert_(ISized.providedBy(sized))

    def testSizeWithBytes(self):
        from zope.size import DefaultSized
        obj = DummyObject(1023)
        sized = DefaultSized(obj)
        self.assertEqual(sized.sizeForSorting(), ('byte', 1023))
        self.assertEqual(sized.sizeForDisplay(), u'1 KB')

    def testSizeWithNone(self):
        from zope.size import DefaultSized
        obj = DummyObject(None)
        sized = DefaultSized(obj)
        self.assertEqual(sized.sizeForSorting(), (None, None))
        self.assertEqual(sized.sizeForDisplay(), u'not-available')

    def testSizeNotAvailable(self):
        from zope.size import DefaultSized
        sized = DefaultSized(object())
        self.assertEqual(sized.sizeForSorting(), (None, None))
        self.assertEqual(sized.sizeForDisplay(), u'not-available')

    def testVariousSizes(self):
        from zope.size import DefaultSized

        sized = DefaultSized(DummyObject(0))
        self.assertEqual(sized.sizeForSorting(), ('byte', 0))
        self.assertEqual(sized.sizeForDisplay(), u'0 KB')

        sized = DefaultSized(DummyObject(1))
        self.assertEqual(sized.sizeForSorting(), ('byte', 1))
        self.assertEqual(sized.sizeForDisplay(), u'1 KB')

        sized = DefaultSized(DummyObject(2048))
        self.assertEqual(sized.sizeForSorting(), ('byte', 2048))
        self.assertEqual(sized.sizeForDisplay(), u'${size} KB')
        self.assertEqual(sized.sizeForDisplay().mapping, {'size': '2'})

        sized = DefaultSized(DummyObject(2000000))
        self.assertEqual(sized.sizeForSorting(), ('byte', 2000000))
        self.assertEqual(sized.sizeForDisplay(), u'${size} MB')
        self.assertEqual(sized.sizeForDisplay().mapping, {'size': '1.91'})

    def test_byteDisplay(self):
        from zope.size import byteDisplay
        self.assertEqual(byteDisplay(0), u'0 KB')
        self.assertEqual(byteDisplay(1), u'1 KB')
        self.assertEqual(byteDisplay(2048), u'${size} KB')
        self.assertEqual(byteDisplay(2048).mapping, {'size': '2'})
        self.assertEqual(byteDisplay(2000000), u'${size} MB')
        self.assertEqual(byteDisplay(2000000).mapping, {'size': '1.91'})

def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(Test)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
