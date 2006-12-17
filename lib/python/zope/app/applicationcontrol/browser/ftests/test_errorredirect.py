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
"""ZODB Control Tests

$Id: test_errorredirect.py 29946 2005-04-12 08:26:40Z hdima $
"""
import unittest

from zope.app.testing.functional import BrowserTestCase


class ErrorRedirectTest(BrowserTestCase):

    def testErrorRedirect(self):
        response = self.publish('/++etc++process/@@errorRedirect.html',
                                basic='globalmgr:globalmgrpw')
        self.failUnlessEqual('http://localhost/@@errorRedirect.html',
                             response.getHeader('Location'))
        self.failUnlessEqual(302, response.getStatus())


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ErrorRedirectTest))
    return suite

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
