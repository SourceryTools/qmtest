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
"""Tests for HTTP error views

$Id: test_methodnotallowed.py 38357 2005-09-07 20:14:34Z srichter $
"""
from unittest import TestCase, TestSuite, main, makeSuite
from StringIO import StringIO

from zope.interface import Interface, implements
from zope.publisher.http import HTTPRequest
from zope.publisher.interfaces.http import IHTTPRequest

from zope.app.testing import ztapi
from zope.app.testing.placelesssetup import PlacelessSetup


class I(Interface):
    pass


class C(object):
    implements(I)


class GetView(object):
    def __init__(self, context, request):
        pass
    def GET(self):
        pass


class DeleteView(object):
    def __init__(self, context, request):
        pass
    def DELETE(self):
        pass


class TestMethodNotAllowedView(PlacelessSetup, TestCase):

    def setUp(self):
        from zope.publisher.interfaces.http import IHTTPRequest
        PlacelessSetup.setUp(self)
        ztapi.provideView(I, IHTTPRequest, Interface, 'GET', GetView)
        ztapi.provideView(I, IHTTPRequest, Interface, 'DELETE', DeleteView)
        ztapi.provideView(I, IHTTPRequest, Interface, 'irrelevant', GetView)
        ztapi.provideView(I, IHTTPRequest, Interface, 'also_irr.', DeleteView)

    def test(self):
        from zope.app.publication.http import MethodNotAllowed
        from zope.app.http.exception.methodnotallowed \
             import MethodNotAllowedView
        from zope.publisher.http import HTTPRequest

        context = C()
        request = HTTPRequest(StringIO('PUT /bla/bla HTTP/1.1\n\n'), {})
        error = MethodNotAllowed(context, request)
        view = MethodNotAllowedView(error, request)

        result = view()

        self.assertEqual(request.response.getStatus(), 405)
        self.assertEqual(request.response.getHeader('Allow'), 'DELETE, GET')
        self.assertEqual(result, 'Method Not Allowed')


def test_suite():
    return TestSuite((
        makeSuite(TestMethodNotAllowedView),
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')
