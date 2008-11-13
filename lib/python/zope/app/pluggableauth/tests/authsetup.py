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
"""Setup local Pluggable Authentication for tests

This setup class can be used, if a set of local principals are required for a
test.

$Id: authsetup.py 29143 2005-02-14 22:43:16Z srichter $
"""
import base64
from zope.publisher.browser import TestRequest as Request

from zope.app.testing import ztapi, setup
from zope.app.component.testing import PlacefulSetup
from zope.publisher.interfaces.http import IHTTPCredentials
from zope.app.security.interfaces import ILoginPassword, IAuthentication
from zope.app.security.basicauthadapter import BasicAuthAdapter
from zope.app.pluggableauth import \
     PrincipalAuthenticationView, PluggableAuthentication, \
     BTreePrincipalSource, SimplePrincipal
from zope.app.pluggableauth.interfaces import IPrincipalSource

class AuthSetup(PlacefulSetup):

    def setUp(self):
        sm = PlacefulSetup.setUp(self, site=True)
        ztapi.provideAdapter(IHTTPCredentials, ILoginPassword, BasicAuthAdapter)

        ztapi.browserView(IPrincipalSource, "login",
                          PrincipalAuthenticationView)

        auth = setup.addUtility(sm, '', IAuthentication,
                                PluggableAuthentication(None, True))

        one = BTreePrincipalSource()
        two = BTreePrincipalSource()
        self._one = one
        self._two = two

        auth.addPrincipalSource('one', one)
        auth.addPrincipalSource('two', two)
        self._auth = auth
        self.createUsers()

    def createUsers(self):

        self._srichter = SimplePrincipal('srichter', 'hello',
                                         'Stephan', 'Richter')
        self._srichter.id = 'srichter'
        self._jim = SimplePrincipal('jim', 'hello2',
                                    'Jim', 'Fulton')
        self._jim.id = 'jim'
        self._stevea = SimplePrincipal('stevea', 'hello3',
                                       'Steve', 'Alenxander')
        self._stevea.id = 'stevea'
        self._one['srichter'] = self._srichter
        self._one['jim'] = self._jim
        self._two['stevea'] = self._stevea

    def getRequest(self, uid=None, passwd=None):
        if uid is None:
            return Request()
        if passwd is None:
            passwd = ''
        dict =  {
            'HTTP_AUTHORIZATION':
            "Basic %s" % base64.encodestring('%s:%s' % (uid, passwd))
         }
        return Request(**dict)
