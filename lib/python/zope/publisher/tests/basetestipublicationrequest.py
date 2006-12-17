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
"""IPublicationRequest base test

$Id: basetestipublicationrequest.py 65511 2006-02-27 05:24:24Z philikon $
"""
import sys

from zope.interface import Interface, directlyProvides, implements
from zope.interface.verify import verifyObject
from zope.publisher.interfaces import IPublicationRequest, IHeld
from zope.publisher.interfaces.browser import IBrowserSkinType

class Held:
    implements(IHeld)

    released = False

    def release(self):
        self.released = True


class BaseTestIPublicationRequest(object):
    def testVerifyIPublicationRequest(self):
        verifyObject(IPublicationRequest, self._Test__new())

    def testHaveCustomTestsForIPublicationRequest(self):
        # Make sure that tests are defined for things we can't test here
        self.test_IPublicationRequest_getPositionalArguments

    def testTraversalStack(self):
        request = self._Test__new()
        stack = ['Engineering', 'ZopeCorp']
        request.setTraversalStack(stack)
        self.assertEqual(list(request.getTraversalStack()), stack)

    def testHoldCloseAndGetResponse(self):
        request = self._Test__new()

        response = request.response
        rcresponse = sys.getrefcount(response)

        resource = object()
        rcresource = sys.getrefcount(resource)

        request.hold(resource)

        resource2 = Held()
        rcresource2 = sys.getrefcount(resource2)
        request.hold(resource2)

        self.failUnless(sys.getrefcount(resource) > rcresource)
        self.failUnless(sys.getrefcount(resource2) > rcresource2)
        self.failIf(resource2.released)

        request.close()

        self.failUnless(resource2.released)
        # Responses are not unreferenced during close()
        self.failUnless(sys.getrefcount(response) >= rcresponse)
        self.assertEqual(sys.getrefcount(resource), rcresource)
        self.assertEqual(sys.getrefcount(resource2), rcresource2)

    def testSkinManagement(self):
        request = self._Test__new()

        class IMoreFoo(Interface):
            pass
        directlyProvides(IMoreFoo, IBrowserSkinType)

        self.assertEqual(IMoreFoo.providedBy(request), False)
        directlyProvides(request, IMoreFoo)
        self.assertEqual(IMoreFoo.providedBy(request), True)

