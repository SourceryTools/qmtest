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

$Id: tests.py 80055 2007-09-25 21:28:54Z rogerineichen $
"""
from cStringIO import StringIO
import unittest, os, os.path

import zope.component
from zope.testing import doctest
from zope.app.testing import placelesssetup
import transaction

from zope.component import provideHandler, getGlobalSiteManager
from zope.session.interfaces import IClientId, IClientIdManager, ISession
from zope.session.interfaces import ISessionDataContainer
from zope.session.interfaces import ISessionPkgData, ISessionData
from zope.session.session import ClientId, Session
from zope.session.session import PersistentSessionDataContainer
from zope.session.session import RAMSessionDataContainer
from zope.session.http import CookieClientIdManager
from zope.session.bootstrap import bootStrapSubscriber as \
     sessionBootstrapSubscriber

from zope.publisher.interfaces import IRequest
from zope.publisher.http import HTTPRequest

from zope.app.appsetup.tests import TestBootstrapSubscriber, EventStub
from zope.app.appsetup.bootstrap import bootStrapSubscriber


def setUp(session_data_container_class=PersistentSessionDataContainer):
    placelesssetup.setUp()
    zope.component.provideAdapter(ClientId, (IRequest,), IClientId)
    zope.component.provideAdapter(Session, (IRequest,), ISession)
    zope.component.provideUtility(CookieClientIdManager(), IClientIdManager)
    sdc = session_data_container_class()
    for product_id in ('', 'products.foo', 'products.bar', 'products.baz'):
        zope.component.provideUtility(sdc, ISessionDataContainer, product_id)
    request = HTTPRequest(StringIO(), {}, None)
    return request

def tearDown():
    placelesssetup.tearDown()

class TestBootstrap(TestBootstrapSubscriber):

    def test_bootstrapSusbcriber(self):
        bootStrapSubscriber(EventStub(self.db))

        sessionBootstrapSubscriber(EventStub(self.db))

        import zope.component
        from zope.app.publication.zopepublication import ZopePublication
        from zope.app.component.hooks import setSite

        cx = self.db.open()
        root = cx.root()
        root_folder = root[ZopePublication.root_name]
        setSite(root_folder)

        zope.component.getUtility(IClientIdManager)
        zope.component.getUtility(ISessionDataContainer)

        cx.close()

# Test the code in our API documentation is correct
def test_documentation():
    pass
test_documentation.__doc__ = '''
    >>> request = setUp(RAMSessionDataContainer)

    %s

    >>> tearDown()

    ''' % (open(os.path.join(os.path.dirname(__file__), 'api.txt')).read(),)


def tearDownTransaction(test):
    transaction.abort()



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBootstrap))
    suite.addTest(doctest.DocTestSuite())
    suite.addTest(doctest.DocTestSuite('zope.session.session',
        tearDown=tearDownTransaction))
    suite.addTest(doctest.DocTestSuite('zope.session.http',
        optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS,)
        )
    return suite


if __name__ == '__main__':
    unittest.main()
