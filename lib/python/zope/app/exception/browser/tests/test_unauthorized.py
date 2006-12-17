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
"""Test Unauthorized Exception Views

$Id: test_unauthorized.py 41171 2006-01-06 20:04:44Z poster $
"""
from unittest import TestCase, main, makeSuite
from zope import component, interface
import zope.formlib.namedtemplate
from zope.publisher.browser import TestRequest
import zope.publisher.interfaces.browser
from zope.app.testing import ztapi
from zope.app.security.interfaces import IAuthentication, IPrincipal
from zope.app.exception.browser.unauthorized import Unauthorized
from zope.app.testing.placelesssetup import PlacelessSetup

class DummyPrincipal(object):
    interface.implements(IPrincipal)  # this is a lie

    def __init__(self, id):
        self.id = id

    def getId(self):
        return self.id

class DummyAuthUtility(object):
    interface.implements(IAuthentication)  # this is a lie

    status = None

    def unauthorized(self, principal_id, request):
        self.principal_id = principal_id
        self.request = request
        if self.status is not None:
            self.request.response.setStatus(self.status)

class DummyTemplate (object):

    def __init__(self, context):
        self.context = context

    component.adapts(Unauthorized)
    interface.implements(zope.formlib.namedtemplate.INamedTemplate)

    def __call__(self):
        return 'You are not authorized'

class Test(PlacelessSetup, TestCase):

    def setUp(self):
        super(Test, self).setUp()
        self.auth = DummyAuthUtility()
        ztapi.provideUtility(IAuthentication, self.auth)

    def tearDown(self):
        super(Test, self).tearDown()

    def testUnauthorized(self):
        component.provideAdapter(DummyTemplate, name="default")
        exception = Exception()
        try:
            raise exception
        except:
            pass
        request = TestRequest()
        request.setPrincipal(DummyPrincipal(23))
        u = Unauthorized(exception, request)
        res = u()

        # Make sure that we rendered the expected template
        self.assertEqual("You are not authorized", res)

        # Make sure the response status was set
        self.assertEqual(request.response.getStatus(), 403)

        # Make sure the auth utility was called
        self.failUnless(self.auth.request is request)
        self.assertEqual(self.auth.principal_id, 23)

    def testRedirect(self):
        exception= Exception()
        try:
            raise exception
        except:
            pass
        request = TestRequest()
        request.setPrincipal(DummyPrincipal(23))
        u = Unauthorized(exception, request)
        
        self.auth.status = 303
        
        res = u()

        # Make sure that the template was not rendered
        self.assert_(res is None)

        # Make sure the auth's redirect is honored
        self.assertEqual(request.response.getStatus(), 303)

        # Make sure the auth utility was called
        self.failUnless(self.auth.request is request)
        self.assertEqual(self.auth.principal_id, 23)

def test_suite():
    return makeSuite(Test)

if __name__=='__main__':
    main(defaultTest='test_suite')
