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
"""
$Id: test_logout.py 39687 2005-10-28 10:14:24Z hdima $
"""
import unittest

from zope.testing import doctest
from zope.interface import implements
from zope.component import provideAdapter, adapts
from zope.publisher.tests.httprequest import TestRequest

from zope.app.testing import placelesssetup
from zope.app.security import interfaces


def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite(
            '../logout.txt',
            globs={'provideAdapter': provideAdapter,
                   'TestRequest': TestRequest,
                   'implements': implements,
                   'adapts': adapts,
                   'IAuthentication': interfaces.IAuthentication
                  },
            setUp=placelesssetup.setUp,
            tearDown=placelesssetup.tearDown,
            ),
        ))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
