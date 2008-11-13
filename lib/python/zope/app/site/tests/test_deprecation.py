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
"""Test for https://bugs.launchpad.net/zope3/3.4/+bug/98535

$Id: test_deprecation.py 74318 2007-04-21 10:54:28Z baijum $
"""
import unittest
from zope.testing.doctestunit import DocTestSuite

__docformat__ = "reStructuredText"

def test_deprecation_of_placefulsetup():
    """
    >>> import warnings
    >>> showwarning = warnings.showwarning
    >>> warnings.showwarning = lambda *a, **k: None

    >>> import zope.app.site.tests.placefulsetup
    >>> placefulsetup = zope.app.site.tests.placefulsetup
    >>> placefulsetup.__name__
    'zope.app.site.tests.placefulsetup'
    >>> placefulsetup.PlacefulSetup
    <class 'zope.app.component.testing.PlacefulSetup'>

    >>> warnings.showwarning = showwarning
    """

def test_suite():
    return unittest.TestSuite([
            DocTestSuite(),
            ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
