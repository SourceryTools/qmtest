##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Test for PrincipalLogging.

$Id: test_principallogging.py 26551 2004-07-15 07:06:37Z srichter $
"""
import unittest
from zope.interface.verify import verifyObject

class PrincipalStub(object):

    id = 42


class TestPrincipalLogging(unittest.TestCase):

    def test_interface(self):
        from zope.app.security.principallogging import PrincipalLogging
        from zope.publisher.interfaces.logginginfo import ILoggingInfo
        principal = PrincipalStub()
        pl = PrincipalLogging(principal)
        verifyObject(ILoggingInfo, pl)

    def test_getLogMessage(self):
        from zope.app.security.principallogging import PrincipalLogging
        principal = PrincipalStub()
        pl = PrincipalLogging(principal)
        self.assertEquals(pl.getLogMessage(), "42")


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestPrincipalLogging))
    return suite


if __name__ == '__main__':
    unittest.main()
