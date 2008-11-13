##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Registration functional tests

$Id: tests.py 80836 2007-10-11 06:58:00Z srichter $
"""
import os.path
import unittest
import zope.app.testing.functional
from zope import interface
from zope.app.component.testing import AppComponentLayer
from zope.app.testing import functional
from zope.testing import doctest

AppComponentBrowserLayer = functional.ZCMLLayer(
    os.path.join(os.path.dirname(__file__), 'ftesting.zcml'),
    __name__, 'AppComponentBrowserLayer', allow_teardown=True)

class ISampleBase(interface.Interface):
    pass

class ISample(ISampleBase):
    pass

class Sample:
    interface.implements(ISample)


def test_suite():
    site = zope.app.testing.functional.FunctionalDocFileSuite(
        "site.txt",
        optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
    site.layer = AppComponentBrowserLayer
    reg = zope.app.testing.functional.FunctionalDocFileSuite(
        'registration.txt',
        optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
    reg.layer = AppComponentLayer
    return unittest.TestSuite((site, reg))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

