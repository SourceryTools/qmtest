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
"""Session tests

$Id: tests.py 69217 2006-07-20 03:56:26Z baijum $
"""
from cStringIO import StringIO
import unittest, os, os.path, sys
from zope.testing import doctest
from zope.app import zapi
from zope.app.testing import ztapi, placelesssetup

from zope.app.session.interfaces import IClientId, IClientIdManager, ISession
from zope.app.session.interfaces import ISessionDataContainer
from zope.app.session.interfaces import ISessionPkgData, ISessionData

from zope.app.session.session import ClientId, Session
from zope.app.session.session import PersistentSessionDataContainer
from zope.app.session.session import RAMSessionDataContainer

from zope.app.session.http import CookieClientIdManager

from zope.publisher.interfaces import IRequest
from zope.publisher.http import HTTPRequest

from zope.pagetemplate.pagetemplate import PageTemplate

from zope.app.appsetup.tests import TestBootstrapSubscriber, EventStub
from zope.app.appsetup.bootstrap import bootStrapSubscriber
from zope.app.session.bootstrap import bootStrapSubscriber as \
     sessionBootstrapSubscriber

def setUp(session_data_container_class=PersistentSessionDataContainer):
    placelesssetup.setUp()
    ztapi.provideAdapter(IRequest, IClientId, ClientId)
    ztapi.provideAdapter(IRequest, ISession, Session)
    ztapi.provideUtility(IClientIdManager, CookieClientIdManager())
    sdc = session_data_container_class()
    for product_id in ('', 'products.foo', 'products.bar', 'products.baz'):
        ztapi.provideUtility(ISessionDataContainer, sdc, product_id)
    request = HTTPRequest(StringIO(), {}, None)
    return request

def tearDown():
    placelesssetup.tearDown()

class TestBootstrap(TestBootstrapSubscriber):

    def test_bootstrapSusbcriber(self):
        bootStrapSubscriber(EventStub(self.db))

        sessionBootstrapSubscriber(EventStub(self.db))

        from zope.app.publication.zopepublication import ZopePublication
        from zope.app.component.hooks import setSite
        from zope.app import zapi

        cx = self.db.open()
        root = cx.root()
        root_folder = root[ZopePublication.root_name]
        setSite(root_folder)

        zapi.getUtility(IClientIdManager)
        zapi.getUtility(ISessionDataContainer)


        cx.close()

# Test the code in our API documentation is correct
def test_documentation():
    pass
test_documentation.__doc__ = '''
    >>> request = setUp(RAMSessionDataContainer)

    %s

    >>> tearDown()

    ''' % (open(os.path.join(os.path.dirname(__file__), 'api.txt')).read(),)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBootstrap))
    suite.addTest(doctest.DocTestSuite())
    suite.addTest(doctest.DocTestSuite('zope.app.session.session'))
    suite.addTest(doctest.DocTestSuite('zope.app.session.http'))
    return suite

if __name__ == '__main__':
    unittest.main()
