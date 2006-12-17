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
"""Tests for the ZCML Documentation Module

$Id: tests.py 29269 2005-02-23 22:22:48Z srichter $
"""
import os
import unittest
from zope.testing import doctest, doctestunit
from zope.app.testing import placelesssetup, ztapi

from zope.schema.interfaces import ITextLine
from zope.app.form.browser import TextWidget
from zope.app.form.interfaces import IInputWidget

def setUp(test):
    placelesssetup.setUp()
    ztapi.browserViewProviding(ITextLine, TextWidget, IInputWidget)


def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite('../form.txt',
                             setUp=setUp, tearDown=placelesssetup.tearDown,
                             globs={'pprint': doctestunit.pprint},
                             optionflags=doctest.NORMALIZE_WHITESPACE),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
