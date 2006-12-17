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
"""Security Views Tests

$Id: tests.py 29143 2005-02-14 22:43:16Z srichter $
"""
__docformat__ = "reStructuredText"
import unittest
from zope.testing import doctest
from zope.app.testing import placelesssetup

def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite('authutilitysearchview.txt',
                             setUp=placelesssetup.setUp,
                             tearDown=placelesssetup.tearDown),
        doctest.DocFileSuite('principalterms.txt',
                             setUp=placelesssetup.setUp,
                             tearDown=placelesssetup.tearDown),
        doctest.DocFileSuite('loginlogout.txt',
                             setUp=placelesssetup.setUp,
                             tearDown=placelesssetup.tearDown),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

