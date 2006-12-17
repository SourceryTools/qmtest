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
"""Test HTTP Publication

$Id$
"""
from unittest import TestCase, TestSuite, main, makeSuite
from StringIO import StringIO

from zope.interface import Interface, implements
from zope.publisher.http import HTTPRequest
from zope.publisher.interfaces.http import IHTTPRequest

import zope.app.publication.http
from zope.app.testing import ztapi
from zope.app.testing.placelesssetup import PlacelessSetup

class I(Interface):
    pass

class C(object):
    spammed = 0
    implements(I)

class V(object):

    def __init__(self, context, request):
        self.context = context

    def SPAM(self):
        self.context.spammed += 1


class Test(PlacelessSetup, TestCase):
    # Note that zope publication tests cover all of the code but callObject

    def test_callObject(self):
        pub = zope.app.publication.http.HTTPPublication(None)
        request = HTTPRequest(StringIO(''), {})
        request.method = 'SPAM'

        ztapi.provideView(I, IHTTPRequest, Interface, 'SPAM', V)

        ob = C()
        pub.callObject(request, ob)
        self.assertEqual(ob.spammed, 1)


def test_suite():
    return TestSuite((
        makeSuite(Test),
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')
