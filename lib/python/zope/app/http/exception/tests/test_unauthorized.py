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
"""Unauthorized Exception Test

$Id: test_unauthorized.py 41033 2005-12-24 16:57:05Z jim $
"""
from unittest import TestCase, main, makeSuite
from zope.publisher.browser import TestRequest
from zope.app.http.interfaces import IHTTPException

class Test(TestCase):

    def testbasicauth(self):
        from zope.app.http.exception.unauthorized import Unauthorized
        exception = Exception()
        try:
            raise exception
        except:
            pass
        request = TestRequest()
        u = Unauthorized(exception, request)

        # Chech that we implement the right interface
        self.failUnless(IHTTPException.providedBy(u))
        
        # Call the view
        u()
        
        # Make sure the response status was set
        self.assertEqual(request.response.getStatus(), 401)
        self.failUnless(request.response.getHeader('WWW-Authenticate', '', True).startswith('basic'))

def test_suite():
    return makeSuite(Test)

if __name__=='__main__':
    main(defaultTest='test_suite')
