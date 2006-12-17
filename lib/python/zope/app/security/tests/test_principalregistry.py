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
"""Global Authentication Serive or Principal Registry Tests

$Id: test_principalregistry.py 69465 2006-08-14 12:49:46Z ctheune $
"""
import unittest
from zope.interface import implements
from zope.app.security.interfaces import PrincipalLookupError
from zope.publisher.interfaces.http import IHTTPCredentials

from zope.app import zapi
from zope.app.testing import ztapi
from zope.app.component.testing import PlacefulSetup

from zope.app.security.basicauthadapter import BasicAuthAdapter
from zope.app.security.interfaces import ILoginPassword
from zope.app.security.principalregistry import PrincipalRegistry
from zope.app.security.principalregistry import DuplicateLogin, DuplicateId


class Request(object):

    implements(IHTTPCredentials)

    def __init__(self, lpw):
        self.__lpw = lpw

    def _authUserPW(self):
        return self.__lpw

    challenge = None
    def unauthorized(self, challenge):
        self.challenge = challenge


class Test(PlacefulSetup, unittest.TestCase):

    def setUp(self):
        PlacefulSetup.setUp(self)

        ztapi.provideAdapter(
            IHTTPCredentials, ILoginPassword, BasicAuthAdapter)

        self.reg = PrincipalRegistry()

        self.reg.definePrincipal('1', 'Tim Peters', 'Sir Tim Peters',
                                 'tim', '123')
        self.reg.definePrincipal('2', 'Jim Fulton', 'Sir Jim Fulton',
                                 'jim', '456')

    def testRegistered(self):
        p = self.reg.getPrincipal('1')
        self.assertEqual(p.id, '1')
        self.assertEqual(p.title, 'Tim Peters')
        self.assertEqual(p.description, 'Sir Tim Peters')
        p = self.reg.getPrincipal('2')
        self.assertEqual(p.id, '2')
        self.assertEqual(p.title, 'Jim Fulton')
        self.assertEqual(p.description, 'Sir Jim Fulton')

        self.assertEqual(len(self.reg.getPrincipals('')), 2)

    def testUnRegistered(self):
        self.assertRaises(PrincipalLookupError, self.reg.getPrincipal, '3')

    def testDup(self):
        self.assertRaises(DuplicateId,
                          self.reg.definePrincipal,
                          '1', 'Tim Peters', 'Sir Tim Peters',
                          'tim2', '123')
        self.assertRaises(DuplicateLogin,
                          self.reg.definePrincipal,
                          '3', 'Tim Peters', 'Sir Tim Peters',
                          'tim', '123')
        self.assertRaises(PrincipalLookupError, self.reg.getPrincipal, '3')
        self.assertEqual(len(self.reg.getPrincipals('')), 2)

    def testSearch(self):
        r = self.reg.getPrincipals('J')
        self.assertEquals(len(r), 1)
        self.failUnless(r[0] is self.reg.getPrincipal('2'))

    def testByLogin(self):
        tim = self.reg.getPrincipalByLogin('tim')
        self.assertEquals(tim.getLogin(), 'tim')
        jim = self.reg.getPrincipalByLogin('jim')
        self.assertEquals(jim.getLogin(), 'jim')
        self.assertRaises(KeyError,
                          self.reg.getPrincipalByLogin, 'kim')

    def testValidation(self):
        tim = self.reg.getPrincipalByLogin('tim')
        self.assert_(tim.validate('123'))
        self.failIf(tim.validate('456'))
        self.failIf(tim.validate(''))
        self.failIf(tim.validate('1234'))
        self.failIf(tim.validate('12'))

    def testAuthenticate(self):
        req = Request(('tim', '123'))
        pid = self.reg.authenticate(req).id
        self.assertEquals(pid, '1')
        req = Request(('tim', '1234'))
        p = self.reg.authenticate(req)
        self.assertEquals(p, None)
        req = Request(('kim', '123'))
        p = self.reg.authenticate(req)
        self.assertEquals(p, None)

    def testUnauthorized(self):
        request = Request(None)
        self.reg.unauthorized(self.reg.unauthenticatedPrincipal(), request)
        self.assertEquals(request.challenge, 'basic realm="Zope"')
        request = Request(None)
        self.reg.unauthorized(None, request)
        self.assertEquals(request.challenge, 'basic realm="Zope"')
        request = Request(None)
        self.reg.unauthorized("1", request)
        self.assertEquals(request.challenge, None)

    def testDefaultPrincipal(self):
        self.assertEquals(self.reg.unauthenticatedPrincipal(), None)
        self.assertRaises(DuplicateId, self.reg.defineDefaultPrincipal,
                          "1", "tim")
        self.reg.defineDefaultPrincipal("everybody", "Default Principal")
        self.assertEquals(self.reg.unauthenticatedPrincipal().id, "everybody")
        self.reg.defineDefaultPrincipal("anybody", "Default Principal",
                                        "This is the default headmaster")
        self.assertEquals(self.reg.unauthenticatedPrincipal().id, "anybody")
        self.assertRaises(PrincipalLookupError,
                          self.reg.getPrincipal, "everybody")
        p = self.reg.getPrincipal("anybody")
        self.assertEquals(p.id, "anybody")
        self.assertEquals(p.title, "Default Principal")
        self.assertRaises(DuplicateId, self.reg.definePrincipal,
                          "anybody", "title")


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(Test),
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
