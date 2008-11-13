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
"""Pluggable Authentication Service Tests

$Id: tests.py 80053 2007-09-25 21:28:25Z rogerineichen $
"""
__docformat__ = "reStructuredText"

import unittest

from zope.testing import doctest
from zope.interface import implements
from zope.component import provideUtility, provideAdapter
from zope.component.eventtesting import getEvents, clearEvents
from zope.publisher.interfaces import IRequest

from zope.app.testing import placelesssetup, ztapi
from zope.app.testing.setup import placefulSetUp, placefulTearDown
from zope.session.interfaces import \
        IClientId, IClientIdManager, ISession, ISessionDataContainer
from zope.session.session import \
        ClientId, Session, PersistentSessionDataContainer
from zope.session.http import CookieClientIdManager

from zope.publisher import base
from zope.app.authentication.session import SessionCredentialsPlugin


class TestClientId(object):
    implements(IClientId)
    def __new__(cls, request):
        return 'dummyclientidfortesting'

def siteSetUp(test):
    placefulSetUp(site=True)

def siteTearDown(test):
    placefulTearDown()

def sessionSetUp(session_data_container_class=PersistentSessionDataContainer):
    placelesssetup.setUp()
    ztapi.provideAdapter(IRequest, IClientId, TestClientId)
    ztapi.provideAdapter(IRequest, ISession, Session)
    ztapi.provideUtility(IClientIdManager, CookieClientIdManager())
    sdc = session_data_container_class()
    ztapi.provideUtility(ISessionDataContainer, sdc, '')

def nonHTTPSessionTestCaseSetUp(sdc_class=PersistentSessionDataContainer):
    # I am getting an error with ClientId and not TestClientId
    placelesssetup.setUp()
    ztapi.provideAdapter(IRequest, IClientId, ClientId)
    ztapi.provideAdapter(IRequest, ISession, Session)
    ztapi.provideUtility(IClientIdManager, CookieClientIdManager())
    sdc = sdc_class()
    ztapi.provideUtility(ISessionDataContainer, sdc, '')


class NonHTTPSessionTestCase(unittest.TestCase):
    # Small test suite to catch an error with non HTTP protocols, like FTP
    # and SessionCredentialsPlugin.
    def setUp(self):
        nonHTTPSessionTestCaseSetUp()

    def tearDown(self):
        placefulTearDown()

    def test_exeractCredentials(self):
        plugin = SessionCredentialsPlugin()

        self.assertEqual(plugin.extractCredentials(base.TestRequest('/')), None)

    def test_challenge(self):
        plugin = SessionCredentialsPlugin()

        self.assertEqual(plugin.challenge(base.TestRequest('/')), False)

    def test_logout(self):
        plugin = SessionCredentialsPlugin()

        self.assertEqual(plugin.logout(base.TestRequest('/')), False)


def test_suite():
    return unittest.TestSuite((
        doctest.DocTestSuite('zope.app.authentication.interfaces'),
        doctest.DocTestSuite('zope.app.authentication.password'),
        doctest.DocTestSuite('zope.app.authentication.generic'),
        doctest.DocTestSuite('zope.app.authentication.httpplugins'),
        doctest.DocTestSuite('zope.app.authentication.ftpplugins'),
        doctest.DocTestSuite('zope.app.authentication.groupfolder'),
        doctest.DocFileSuite('principalfolder.txt',
                             setUp=placelesssetup.setUp,
                             tearDown=placelesssetup.tearDown),
        doctest.DocTestSuite('zope.app.authentication.principalfolder',
                             setUp=placelesssetup.setUp,
                             tearDown=placelesssetup.tearDown),
        doctest.DocTestSuite('zope.app.authentication.idpicker'),
        doctest.DocTestSuite('zope.app.authentication.session',
                             setUp=siteSetUp,
                             tearDown=siteTearDown),
        doctest.DocFileSuite('README.txt',
                             setUp=siteSetUp,
                             tearDown=siteTearDown,
                             globs={'provideUtility': provideUtility,
                                    'provideAdapter': provideAdapter,
                                    'getEvents': getEvents,
                                    'clearEvents': clearEvents,
                                    'subscribe': ztapi.subscribe,
                                    }),
        doctest.DocFileSuite('groupfolder.txt',
                             setUp=placelesssetup.setUp,
                             tearDown=placelesssetup.tearDown,
                             ),
        doctest.DocFileSuite('vocabulary.txt',
                             setUp=placelesssetup.setUp,
                             tearDown=placelesssetup.tearDown,
                             ),
        unittest.makeSuite(NonHTTPSessionTestCase),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
