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
"""Binding Tests

$Id: test_binding.py 73618 2007-03-26 11:18:56Z dobe $
"""
import unittest

from zope.app.pagetemplate.tests.testpackage.content \
     import Content, PTComponent

from zope.app.testing import setup, placelesssetup


class BindingTestCase(placelesssetup.PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(BindingTestCase, self).setUp()
        setup.setUpTraversal()

    def test_binding(self):
        from zope.publisher.browser import TestRequest
        comp = PTComponent(Content(), TestRequest())
        self.assertEqual(comp.index(), "42\n")
        self.assertEqual(comp.nothing(), "\n")
        self.assertEqual(comp.default(), "42\n")

def test_suite():
    return unittest.makeSuite(BindingTestCase)

if __name__=='__main__':
    unittest.main()
