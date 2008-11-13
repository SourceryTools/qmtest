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
"""Test Image Data handling

$Id: test_imagedata.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest

from zope.component import adapts, provideAdapter
from zope.component.testing import PlacelessSetup
from zope.interface import implements
from zope.app.file.image import Image
from zope.app.file.browser.image import ImageData
from zope.traversing.browser.interfaces import IAbsoluteURL

class FakeRequest(object):
    pass

class StubAbsoluteURL(object):
    adapts(Image, FakeRequest)
    implements(IAbsoluteURL)

    def __init__(self, *objects):
        pass

    def __str__(self):
        return '/img'

    __call__ = __str__

class ImageDataTest(PlacelessSetup, unittest.TestCase):

    def testData(self):
        image = Image('Data')
        id = ImageData()
        id.context = image
        id.request = None
        self.assertEqual(id(), 'Data')

    def testTag(self):
        provideAdapter(StubAbsoluteURL)
        image = Image()
        fe = ImageData()
        fe.context = image
        fe.request = FakeRequest()

        self.assertEqual(fe.tag(),
            '<img src="/img" alt="" height="-1" width="-1" border="0" />')
        self.assertEqual(fe.tag(alt="Test Image"),
            '<img src="/img" alt="Test Image" '
            'height="-1" width="-1" border="0" />')
        self.assertEqual(fe.tag(height=100, width=100),
            ('<img src="/img" alt="" height="100" '
                'width="100" border="0" />'))
        self.assertEqual(fe.tag(border=1),
            '<img src="/img" alt="" height="-1" width="-1" border="1" />')
        self.assertEqual(fe.tag(css_class="Image"),
            '<img src="/img" alt="" '
            'height="-1" width="-1" border="0" class="Image" />')
        self.assertEqual(fe.tag(height=100, width="100",
                        border=1, css_class="Image"),
            '<img src="/img" alt="" '
                'height="100" width="100" class="Image" border="1" />')

def test_suite():
    return unittest.makeSuite(ImageDataTest)

if __name__=='__main__':
    unittest.main()
