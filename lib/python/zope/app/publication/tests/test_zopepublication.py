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
"""Zope Publication Tests

$Id$
"""
import unittest
import sys
from cStringIO import StringIO

from persistent import Persistent
from ZODB.DB import DB
from ZODB.DemoStorage import DemoStorage
import transaction

import zope.component
from zope.interface.verify import verifyClass
from zope.interface import implements, classImplements, implementedBy
from zope.i18n.interfaces import IUserPreferredCharsets
from zope.component.interfaces import ComponentLookupError
from zope.publisher.base import TestPublication, TestRequest
from zope.publisher.http import IHTTPRequest, HTTPCharsets
from zope.publisher.interfaces import IRequest, IPublishTraverse
from zope.security import simplepolicies
from zope.security.management import setSecurityPolicy, queryInteraction
from zope.security.management import endInteraction
from zope.traversing.interfaces import IPhysicallyLocatable
from zope.location.interfaces import ILocation

from zope.app.testing.placelesssetup import PlacelessSetup
from zope.app.testing import setup, ztapi

from zope.app.error.interfaces import IErrorReportingUtility
from zope.app.security.principalregistry import principalRegistry
from zope.app.security.interfaces import IUnauthenticatedPrincipal, IPrincipal
from zope.app.publication.zopepublication import ZopePublication
from zope.app.folder import Folder, rootFolder
from zope.location import Location
from zope.app.security.interfaces import IAuthenticationUtility

class Principal(object):
    implements(IPrincipal)
    def __init__(self, id):
        self.id = id
        self.title = ''
        self.description = ''

class UnauthenticatedPrincipal(Principal):
    implements(IUnauthenticatedPrincipal)

class AuthUtility1(object):

    def authenticate(self, request):
        return None

    def unauthenticatedPrincipal(self):
        return UnauthenticatedPrincipal('test.anonymous')

    def unauthorized(self, id, request):
        pass

    def getPrincipal(self, id):
        return UnauthenticatedPrincipal(id)

class AuthUtility2(AuthUtility1):

    def authenticate(self, request):
        return Principal('test.bob')

    def getPrincipal(self, id):
        return Principal(id)

class ErrorReportingUtility(object):
    implements(IErrorReportingUtility)

    def __init__(self):
        self.exceptions = []

    def raising(self, info, request=None):
        self.exceptions.append([info, request])

class LocatableObject(Location):

    def foo(self):
        pass

class TestRequest(TestRequest):
    URL='http://test.url'

class BasePublicationTests(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(BasePublicationTests, self).setUp()
        from zope.security.management import endInteraction
        endInteraction()
        ztapi.provideAdapter(IHTTPRequest, IUserPreferredCharsets,
                             HTTPCharsets)
        self.policy = setSecurityPolicy(
            simplepolicies.PermissiveSecurityPolicy
            )
        self.storage = DemoStorage('test_storage')
        self.db = db = DB(self.storage)

        connection = db.open()
        root = connection.root()
        app = getattr(root, ZopePublication.root_name, None)

        if app is None:
            from zope.app.folder import rootFolder
            app = rootFolder()
            root[ZopePublication.root_name] = app
            transaction.commit()

        connection.close()
        self.app = app

        from zope.traversing.namespace import view, resource, etc
        ztapi.provideNamespaceHandler('view', view)
        ztapi.provideNamespaceHandler('resource', resource)
        ztapi.provideNamespaceHandler('etc', etc)

        self.request = TestRequest('/f1/f2')
        self.user = Principal('test.principal')
        self.request.setPrincipal(self.user)
        from zope.interface import Interface
        self.presentation_type = Interface
        self.request._presentation_type = self.presentation_type
        self.object = object()
        self.publication = ZopePublication(self.db)

    def tearDown(self):
        super(BasePublicationTests, self).tearDown()

    def testInterfacesVerify(self):
        for interface in implementedBy(ZopePublication):
            verifyClass(interface, TestPublication)


class ZopePublicationErrorHandling(BasePublicationTests):

    def testRetryAllowed(self):
        from ZODB.POSException import ConflictError
        from zope.publisher.interfaces import Retry
        try:
            raise ConflictError
        except:
            self.assertRaises(Retry, self.publication.handleException,
                self.object, self.request, sys.exc_info(), retry_allowed=True)

        try:
            raise Retry(sys.exc_info())
        except:
            self.assertRaises(Retry, self.publication.handleException,
                self.object, self.request, sys.exc_info(), retry_allowed=True)

    def testRetryNotAllowed(self):
        from ZODB.POSException import ConflictError
        from zope.publisher.interfaces import Retry
        try:
            raise ConflictError
        except:
            self.publication.handleException(
                self.object, self.request, sys.exc_info(), retry_allowed=False)
        value = ''.join(self.request.response._result).split()
        self.assertEqual(' '.join(value[:6]),
                         'Traceback (most recent call last): File')
        self.assertEqual(' '.join(value[-8:]),
                         'in testRetryNotAllowed raise ConflictError'
                         ' ConflictError: database conflict error')

        try:
            raise Retry(sys.exc_info())
        except:
            self.publication.handleException(
                self.object, self.request, sys.exc_info(), retry_allowed=False)
        value = ''.join(self.request.response._result).split()
        self.assertEqual(' '.join(value[:6]),
                         'Traceback (most recent call last): File')
        self.assertEqual(' '.join(value[-8:]),
                         'in testRetryNotAllowed raise Retry(sys.exc_info())'
                         ' Retry: database conflict error')

        try:
            raise Retry
        except:
            self.publication.handleException(
                self.object, self.request, sys.exc_info(), retry_allowed=False)
        value = ''.join(self.request.response._result).split()
        self.assertEqual(' '.join(value[:6]),
                         'Traceback (most recent call last): File')
        self.assertEqual(' '.join(value[-6:]),
                         'in testRetryNotAllowed raise Retry'
                         ' Retry: None')



    def testViewOnException(self):
        from zope.interface import Interface
        class E1(Exception):
            pass

        ztapi.setDefaultViewName(E1, 'name',
                                 layer=None,
                                 type=self.presentation_type)
        view_text = 'You had a conflict error'
        ztapi.provideView(E1, self.presentation_type, Interface,
                          'name', lambda obj, request: lambda: view_text)
        try:
            raise E1
        except:
            pass
        self.publication.handleException(
            self.object, self.request, sys.exc_info(), retry_allowed=False)
        self.assertEqual(self.request.response._result, view_text)

    def testHandlingSystemErrors(self):

        # Generally, when there is a view for an excepton, we assume
        # it is a user error, not a system error and we don't log it.

        from zope.testing import loggingsupport
        handler = loggingsupport.InstalledHandler('SiteError')

        self.testViewOnException()

        self.assertEqual(
            str(handler),
            'SiteError ERROR\n'
            '  Error while reporting an error to the Error Reporting utility')

        # Here we got a single log record, because we havdn't
        # installed an error reporting utility.  That's OK.

        handler.uninstall()
        handler = loggingsupport.InstalledHandler('SiteError')

        # Now, we'll register an exception view that indicates that we
        # have a system error.

        from zope.interface import Interface, implements
        class E2(Exception):
            pass

        ztapi.setDefaultViewName(E2, 'name',
                                 layer=self.presentation_type,
                                 type=self.presentation_type)
        view_text = 'You had a conflict error'

        from zope.app.exception.interfaces import ISystemErrorView
        class MyView:
            implements(ISystemErrorView)
            def __init__(self, context, request):
                pass

            def isSystemError(self):
                return True

            def __call__(self):
                return view_text

        ztapi.provideView(E2, self.presentation_type, Interface,
                          'name', MyView)
        try:
            raise E2
        except:
            self.publication.handleException(
                self.object, self.request, sys.exc_info(), retry_allowed=False)

        # Now, since the view was a system error view, we should have
        # a log entry for the E2 error (as well as the missing
        # error reporting utility).
        self.assertEqual(
            str(handler),
            'SiteError ERROR\n'
            '  Error while reporting an error to the Error Reporting utility\n'
            'SiteError ERROR\n'
            '  http://test.url'
            )

        handler.uninstall()

    def testNoViewOnClassicClassException(self):
        from zope.interface import Interface
        from types import ClassType
        class ClassicError:
            __metaclass__ = ClassType
        class IClassicError(Interface):
            pass
        classImplements(ClassicError, IClassicError)
        ztapi.setDefaultViewName(IClassicError, 'name', self.presentation_type)
        view_text = 'You made a classic error ;-)'
        ztapi.provideView(IClassicError, self.presentation_type, Interface,
                          'name', lambda obj,request: lambda: view_text)
        try:
            raise ClassicError
        except:
            pass
        self.publication.handleException(
            self.object, self.request, sys.exc_info(), retry_allowed=False)
        # check we don't get the view we registered
        self.failIf(''.join(self.request.response._result) == view_text)
        # check we do actually get something
        self.failIf(''.join(self.request.response._result) == '')

    def testExceptionSideEffects(self):
        from zope.publisher.interfaces import IExceptionSideEffects
        class SideEffects(object):
            implements(IExceptionSideEffects)
            def __init__(self, exception):
                self.exception = exception
            def __call__(self, obj, request, exc_info):
                self.obj = obj
                self.request = request
                self.exception_type = exc_info[0]
                self.exception_from_info = exc_info[1]
        class SideEffectsFactory:
            def __call__(self, exception):
                self.adapter = SideEffects(exception)
                return self.adapter
        factory = SideEffectsFactory()
        from ZODB.POSException import ConflictError
        from zope.interface import Interface
        class IConflictError(Interface):
            pass
        classImplements(ConflictError, IConflictError)
        ztapi.provideAdapter(IConflictError, IExceptionSideEffects, factory)
        exception = ConflictError()
        try:
            raise exception
        except:
            pass
        self.publication.handleException(
            self.object, self.request, sys.exc_info(), retry_allowed=False)
        adapter = factory.adapter
        self.assertEqual(exception, adapter.exception)
        self.assertEqual(exception, adapter.exception_from_info)
        self.assertEqual(ConflictError, adapter.exception_type)
        self.assertEqual(self.object, adapter.obj)
        self.assertEqual(self.request, adapter.request)

    def testExceptionResetsResponse(self):
        from zope.publisher.browser import TestRequest
        request = TestRequest()
        request.response.setHeader('Content-Type', 'application/pdf')
        request.response.setCookie('spam', 'eggs')
        from ZODB.POSException import ConflictError
        try:
            raise ConflictError
        except:
            pass
        self.publication.handleException(
            self.object, request, sys.exc_info(), retry_allowed=False)
        self.assertEqual(request.response.getHeader('Content-Type'),
                         'text/html;charset=utf-8')
        self.assertEqual(request.response._cookies, {})

    def testAbortOrCommitTransaction(self):
        txn = transaction.get()
        try:
            raise Exception
        except:
            pass
        self.publication.handleException(
            self.object, self.request, sys.exc_info(), retry_allowed=False)
        # assert that we get a new transaction
        self.assert_(txn is not transaction.get())

    def testAbortTransactionWithErrorReportingUtility(self):
        # provide our fake error reporting utility
        zope.component.provideUtility(ErrorReportingUtility())

        class FooError(Exception):
            pass

        last_txn_info = self.db.undoInfo()[0]
        try:
            raise FooError
        except FooError:
            pass
        self.publication.handleException(
            self.object, self.request, sys.exc_info(), retry_allowed=False)

        # assert that the last transaction is NOT our transaction
        new_txn_info = self.db.undoInfo()[0]
        self.assertEqual(last_txn_info, new_txn_info)

        # instead, we expect a message in our logging utility
        error_log = zope.component.getUtility(IErrorReportingUtility)
        self.assertEqual(len(error_log.exceptions), 1)
        error_info, request = error_log.exceptions[0]
        self.assertEqual(error_info[0], FooError)
        self.assert_(isinstance(error_info[1], FooError))
        self.assert_(request is self.request)


class ZopePublicationTests(BasePublicationTests):

    def testPlacefulAuth(self):
        setup.setUpTraversal()
        setup.setUpSiteManagerLookup()
        principalRegistry.defineDefaultPrincipal('anonymous', '')

        root = self.db.open().root()
        app = root[ZopePublication.root_name]
        app['f1'] = rootFolder()
        f1 = app['f1']
        f1['f2'] = Folder()
        sm1 = setup.createSiteManager(f1)
        setup.addUtility(sm1, '', IAuthenticationUtility, AuthUtility1())

        f2 = f1['f2']
        sm2 = setup.createSiteManager(f2)
        setup.addUtility(sm2, '', IAuthenticationUtility, AuthUtility2())
        transaction.commit()

        from zope.app.container.interfaces import ISimpleReadContainer
        from zope.app.container.traversal import ContainerTraverser

        ztapi.provideView(ISimpleReadContainer, IRequest, IPublishTraverse,
                          '', ContainerTraverser)

        from zope.app.folder.interfaces import IFolder
        from zope.security.checker import defineChecker, InterfaceChecker
        defineChecker(Folder, InterfaceChecker(IFolder))

        self.publication.beforeTraversal(self.request)
        self.assertEqual(list(queryInteraction().participations),
                         [self.request])
        self.assertEqual(self.request.principal.id, 'anonymous')
        root = self.publication.getApplication(self.request)
        self.publication.callTraversalHooks(self.request, root)
        self.assertEqual(self.request.principal.id, 'anonymous')
        ob = self.publication.traverseName(self.request, root, 'f1')
        self.publication.callTraversalHooks(self.request, ob)
        self.assertEqual(self.request.principal.id, 'test.anonymous')
        ob = self.publication.traverseName(self.request, ob, 'f2')
        self.publication.afterTraversal(self.request, ob)
        self.assertEqual(self.request.principal.id, 'test.bob')
        self.assertEqual(list(queryInteraction().participations),
                         [self.request])
        self.publication.endRequest(self.request, ob)
        self.assertEqual(queryInteraction(), None)

    def testTransactionCommitAfterCall(self):
        root = self.db.open().root()
        txn = transaction.get()
        # we just need a change in the database to make the
        # transaction notable in the undo log
        root['foo'] = object()
        last_txn_info = self.db.undoInfo()[0]
        self.publication.afterCall(self.request, self.object)
        self.assert_(txn is not transaction.get())
        new_txn_info = self.db.undoInfo()[0]
        self.failIfEqual(last_txn_info, new_txn_info)

    def testTransactionAnnotation(self):
        from zope.interface import directlyProvides
        from zope.location.traversing import LocationPhysicallyLocatable
        from zope.location.interfaces import ILocation
        from zope.traversing.interfaces import IPhysicallyLocatable
        from zope.traversing.interfaces import IContainmentRoot
        ztapi.provideAdapter(ILocation, IPhysicallyLocatable,
                             LocationPhysicallyLocatable)

        root = self.db.open().root()
        root['foo'] = foo = LocatableObject()
        root['bar'] = bar = LocatableObject()
        bar.__name__ = 'bar'
        foo.__name__ = 'foo'
        bar.__parent__ = foo
        foo.__parent__ = root
        directlyProvides(root, IContainmentRoot)

        from zope.publisher.interfaces import IRequest
        expected_path = "/foo/bar"
        expected_user = "/ " + self.user.id
        expected_request = IRequest.__module__ + '.' + IRequest.getName()

        self.publication.afterCall(self.request, bar)
        txn_info = self.db.undoInfo()[0]
        self.assertEqual(txn_info['location'], expected_path)
        self.assertEqual(txn_info['user_name'], expected_user)
        self.assertEqual(txn_info['request_type'], expected_request)

        # also, assert that we still get the right location when
        # passing an instance method as object.
        self.publication.afterCall(self.request, bar.foo)
        self.assertEqual(txn_info['location'], expected_path)

    def testSiteEvents(self):
        from zope.app.publication.interfaces import IBeforeTraverseEvent
        from zope.app.publication.interfaces import IEndRequestEvent

        set = []
        clear = []
        ztapi.subscribe([IBeforeTraverseEvent], None, set.append)
        ztapi.subscribe([IEndRequestEvent], None, clear.append)

        ob = object()

        # This should fire the BeforeTraverseEvent
        self.publication.callTraversalHooks(self.request, ob)

        self.assertEqual(len(set), 1)
        self.assertEqual(len(clear), 0)
        self.assertEqual(set[0].object, ob)

        ob2 = object()

        # This should fire the EndRequestEvent
        self.publication.endRequest(self.request, ob2)

        self.assertEqual(len(set), 1)
        self.assertEqual(len(clear), 1)
        self.assertEqual(clear[0].object, ob2)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ZopePublicationTests),
        unittest.makeSuite(ZopePublicationErrorHandling),
        ))

if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())
