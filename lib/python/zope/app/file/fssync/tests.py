##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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
"""Unit tests for the zope.app.file.file.File fssync adapter.

"""
__docformat__ = "reStructuredText"

import unittest

import zope.app.file.fssync.adapter


class FauxFile:

    def __init__(self, data, contentType=None):
        self.data = data
        self.contentType = contentType


class FileAdapterTestCase(unittest.TestCase):

    def setUp(self):
        self.ob = FauxFile("test data", "text/plain")
        self.adapter = zope.app.file.fssync.adapter.FileAdapter(self.ob)

    def test_extra(self):
        extra = self.adapter.extra()
        self.assertEqual(extra["contentType"], "text/plain")
        extra["contentType"] = "text/x-foo"
        self.assertEqual(extra["contentType"], "text/x-foo")
        self.assertEqual(self.ob.contentType, "text/x-foo")
        self.ob.contentType = "text/x-bar"
        self.assertEqual(extra["contentType"], "text/x-bar")

    def test_getBody(self):
        self.assertEqual(self.adapter.getBody(), "test data")
        self.ob.data = "other data"
        self.assertEqual(self.adapter.getBody(), "other data")

    def test_setBody(self):
        self.adapter.setBody("more text")
        self.assertEqual(self.ob.data, "more text")
        self.assertEqual(self.adapter.getBody(), "more text")


def test_suite():
    return unittest.makeSuite(FileAdapterTestCase)
