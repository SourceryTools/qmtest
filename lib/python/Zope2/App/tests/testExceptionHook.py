##############################################################################
#
# Copyright (c) 2007 Zope Corporation and Contributors.
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

import sys
import unittest
import logging

from zope.publisher.interfaces import INotFound
from zope.security.interfaces import IUnauthorized
from zope.security.interfaces import IForbidden
from zope.interface.common.interfaces import IException

from zope.app.testing import ztapi
from zope.app.testing.placelesssetup import PlacelessSetup
from zope.publisher.browser import setDefaultSkin

class ExceptionHookTestCase(unittest.TestCase):

    def _makeOne(self):
        from Zope2.App.startup import ZPublisherExceptionHook
        return ZPublisherExceptionHook()

    def _makeRequest(self, stdin=None, environ=None,
                     response=None, clean=1, stdout=None):
        from ZPublisher.HTTPRequest import HTTPRequest
        from ZPublisher.HTTPResponse import HTTPResponse

        if stdin is None:
            from StringIO import StringIO
            stdin = StringIO()

        if stdout is None:
            from StringIO import StringIO
            stdout = StringIO()

        if environ is None:
            environ = {}

        if 'SERVER_NAME' not in environ:
            environ['SERVER_NAME'] = 'http://localhost'

        if 'SERVER_PORT' not in environ:
            environ['SERVER_PORT'] = '8080'

        if response is None:
            response = HTTPResponse(stdout=stdout)

        req = HTTPRequest(stdin, environ, response, clean)
        setDefaultSkin(req)
        return req

    def call(self, published, request, f, args=None, kw=None):
        hook = self._makeOne()
        try:
            if args is None:
                args = ()
            if kw is None:
                kw = {}
            f(*args, **kw)
        except:
            return hook(published, request,
                        sys.exc_info()[0],
                        sys.exc_info()[1],
                        sys.exc_info()[2],
                        )

    def call_no_exc(self, hook, published, request, f, args=None, kw=None):
        if hook is None:
            hook = self._makeOne()
        try:
            if args is None:
                args = ()
            if kw is None:
                kw = {}
            f(*args, **kw)
        except:
            try:
                hook(published, request,
                     sys.exc_info()[0],
                     sys.exc_info()[1],
                     sys.exc_info()[2],
                     )
            except:
                pass
            return hook

    def call_exc_value(self, published, request, f, args=None, kw=None):
        hook = self._makeOne()
        try:
            if args is None:
                args = ()
            if kw is None:
                kw = {}
            f(*args, **kw)
        except:
            try:
                return hook(published, request,
                            sys.exc_info()[0],
                            sys.exc_info()[1],
                            sys.exc_info()[2],
                            )
            except Exception, e:
                return e

class ExceptionHookTest(ExceptionHookTestCase):

    def testStringException1(self):
        def f():
            raise 'unauthorized', 'x'
        self.assertRaises('unauthorized', self.call, None, None, f)

    def testStringException2(self):
        def f():
            raise 'redirect', 'x'
        self.assertRaises('redirect', self.call, None, None, f)

    def testSystemExit(self):
        def f():
            raise SystemExit, 1
        self.assertRaises(SystemExit, self.call, None, None, f)

    def testUnauthorized(self):
        from AccessControl import Unauthorized
        def f():
            raise Unauthorized, 1
        self.assertRaises(Unauthorized, self.call, None, {}, f)

    def testConflictErrorRaisesRetry(self):
        from ZPublisher import Retry
        from ZODB.POSException import ConflictError
        from App.config import getConfiguration
        def f():
            raise ConflictError
        request = self._makeRequest()
        old_value = getattr(getConfiguration(), 'conflict_error_log_level', 0)
        self.assertEquals(old_value, 0) # default value
        try:
            getConfiguration().conflict_error_log_level = logging.CRITICAL
            level = getattr(getConfiguration(), 'conflict_error_log_level', 0)
            self.assertEquals(level, logging.CRITICAL)
            self.assertRaises(Retry, self.call, None, request, f)
        finally:
            getConfiguration().conflict_error_log_level = old_value

    def testConflictErrorCount(self):
        from ZPublisher import Retry
        from ZODB.POSException import ConflictError
        def f():
            raise ConflictError
        hook = self._makeOne()
        self.assertEquals(hook.conflict_errors, 0)
        self.call_no_exc(hook, None, None, f)
        self.assertEquals(hook.conflict_errors, 1)
        self.call_no_exc(hook, None, None, f)
        self.assertEquals(hook.conflict_errors, 2)

    def testRetryRaisesOriginalException(self):
        from ZPublisher import Retry
        class CustomException(Exception):
            pass
        def f():
            try:
                raise CustomException, 'Zope'
            except:
                raise Retry(sys.exc_info()[0],
                            sys.exc_info()[1],
                            sys.exc_info()[2])
        self.assertRaises(CustomException, self.call, None, {}, f)

    def testRetryRaisesConflictError(self):
        from ZPublisher import Retry
        from ZODB.POSException import ConflictError
        def f():
            try:
                raise ConflictError
            except:
                raise Retry(sys.exc_info()[0],
                            sys.exc_info()[1],
                            sys.exc_info()[2])
        self.assertRaises(ConflictError, self.call, None, {}, f)

    def testRetryUnresolvedConflictErrorCount(self):
        from ZPublisher import Retry
        from ZODB.POSException import ConflictError
        def f():
            try:
                raise ConflictError
            except:
                raise Retry(sys.exc_info()[0],
                            sys.exc_info()[1],
                            sys.exc_info()[2])
        hook = self._makeOne()
        self.assertEquals(hook.unresolved_conflict_errors, 0)
        self.call_no_exc(hook, None, None, f)
        self.assertEquals(hook.unresolved_conflict_errors, 1)
        self.call_no_exc(hook, None, None, f)
        self.assertEquals(hook.unresolved_conflict_errors, 2)

class Client:

    def __init__(self):
        self.standard_error_message = True
        self.messages = []

    def dummyMethod(self):
        return 'Aye'

class OldClient(Client):

    def raise_standardErrorMessage(self, c, r, t, v, tb):
        from zExceptions.ExceptionFormatter import format_exception
        self.messages.append(''.join(format_exception(t, v, tb, as_html=0)))

class StandardClient(Client):

    def raise_standardErrorMessage(self, c, r, t, v, tb, error_log_url):
        from zExceptions.ExceptionFormatter import format_exception
        fmt = format_exception(t, v, tb, as_html=0)
        self.messages.append(''.join([error_log_url] + fmt))

class BrokenClient(Client):

    def raise_standardErrorMessage(self, c, r, t, v, tb, error_log_url):
        raise AttributeError, 'ouch'

class ExceptionMessageRenderTest(ExceptionHookTestCase):

    def testRenderUnauthorizedOldClient(self):
        from AccessControl import Unauthorized
        def f():
            raise Unauthorized, 1
        request = self._makeRequest()
        client = OldClient()
        self.call(client, request, f)
        self.failUnless(client.messages, client.messages)
        tb = client.messages[0]
        self.failUnless("Unauthorized: You are not allowed" in tb, tb)

    def testRenderUnauthorizedStandardClient(self):
        from AccessControl import Unauthorized
        def f():
            raise Unauthorized, 1
        request = self._makeRequest()
        client = StandardClient()
        self.call(client, request, f)
        self.failUnless(client.messages, client.messages)
        tb = client.messages[0]
        self.failUnless("Unauthorized: You are not allowed" in tb, tb)

    def testRenderUnauthorizedStandardClientMethod(self):
        from AccessControl import Unauthorized
        def f():
            raise Unauthorized, 1
        request = self._makeRequest()
        client = StandardClient()
        self.call(client.dummyMethod, request, f)
        self.failUnless(client.messages, client.messages)
        tb = client.messages[0]
        self.failUnless("Unauthorized: You are not allowed" in tb, tb)

    def testRenderUnauthorizedBrokenClient(self):
        from AccessControl import Unauthorized
        def f():
            raise Unauthorized, 1
        request = self._makeRequest()
        client = BrokenClient()
        self.assertRaises(AttributeError, self.call, client, request, f)

    def testRenderRetryRaisesOriginalException(self):
        from ZPublisher import Retry
        class CustomException(Exception):
            pass
        def f():
            try:
                raise CustomException, 'Zope'
            except:
                raise Retry(sys.exc_info()[0],
                            sys.exc_info()[1],
                            sys.exc_info()[2])
        request = self._makeRequest()
        client = StandardClient()
        self.call(client, request, f)
        self.failUnless(client.messages, client.messages)
        tb = client.messages[0]
        self.failUnless("CustomException: Zope" in tb, tb)

    def testRenderRetryRaisesConflictError(self):
        from ZPublisher import Retry
        from ZODB.POSException import ConflictError
        def f():
            try:
                raise ConflictError
            except:
                raise Retry(sys.exc_info()[0],
                            sys.exc_info()[1],
                            sys.exc_info()[2])
        request = self._makeRequest()
        client = StandardClient()
        self.call(client, request, f)
        self.failUnless(client.messages, client.messages)
        tb = client.messages[0]
        self.failUnless("ConflictError: database conflict error" in tb, tb)

class CustomExceptionView:

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        return "Exception View: %s" % self.context.__class__.__name__

class ExceptionViewsTest(PlacelessSetup, ExceptionHookTestCase):

    def testCustomExceptionViewUnauthorized(self):
        from ZPublisher.HTTPResponse import HTTPResponse
        from AccessControl import Unauthorized
        ztapi.browserView(IUnauthorized, u'index.html', CustomExceptionView)
        def f():
            raise Unauthorized, 1
        request = self._makeRequest()
        client = StandardClient()
        v = self.call_exc_value(client, request, f)
        self.failUnless(isinstance(v, HTTPResponse), v)
        self.failUnless(v.status == 401, (v.status, 401))
        self.failUnless("Exception View: Unauthorized" in str(v))

    def testCustomExceptionViewForbidden(self):
        from ZPublisher.HTTPResponse import HTTPResponse
        from zExceptions import Forbidden
        ztapi.browserView(IForbidden, u'index.html', CustomExceptionView)
        def f():
            raise Forbidden, "argh"
        request = self._makeRequest()
        client = StandardClient()
        v = self.call_exc_value(client, request, f)
        self.failUnless(isinstance(v, HTTPResponse), v)
        self.failUnless(v.status == 403, (v.status, 403))
        self.failUnless("Exception View: Forbidden" in str(v))

    def testCustomExceptionViewNotFound(self):
        from ZPublisher.HTTPResponse import HTTPResponse
        from zExceptions import NotFound
        ztapi.browserView(INotFound, u'index.html', CustomExceptionView)
        def f():
            raise NotFound, "argh"
        request = self._makeRequest()
        client = StandardClient()
        v = self.call_exc_value(client, request, f)
        self.failUnless(isinstance(v, HTTPResponse), v)
        self.failUnless(v.status == 404, (v.status, 404))
        self.failUnless("Exception View: NotFound" in str(v), v)

    def testCustomExceptionViewBadRequest(self):
        from ZPublisher.HTTPResponse import HTTPResponse
        from zExceptions import BadRequest
        ztapi.browserView(IException, u'index.html', CustomExceptionView)
        def f():
            raise BadRequest, "argh"
        request = self._makeRequest()
        client = StandardClient()
        v = self.call_exc_value(client, request, f)
        self.failUnless(isinstance(v, HTTPResponse), v)
        self.failUnless(v.status == 400, (v.status, 400))
        self.failUnless("Exception View: BadRequest" in str(v), v)

    def testCustomExceptionViewInternalError(self):
        from ZPublisher.HTTPResponse import HTTPResponse
        from zExceptions import InternalError
        ztapi.browserView(IException, u'index.html', CustomExceptionView)
        def f():
            raise InternalError, "argh"
        request = self._makeRequest()
        client = StandardClient()
        v = self.call_exc_value(client, request, f)
        self.failUnless(isinstance(v, HTTPResponse), v)
        self.failUnless(v.status == 500, (v.status, 500))
        self.failUnless("Exception View: InternalError" in str(v), v)

    def testRedirectNoExceptionView(self):
        from ZPublisher.HTTPResponse import HTTPResponse
        from zExceptions import Redirect
        ztapi.browserView(IException, u'index.html', CustomExceptionView)
        def f():
            raise Redirect, "http://zope.org/"
        request = self._makeRequest()
        client = StandardClient()
        v = self.call_exc_value(client, request, f)
        self.failUnless(isinstance(v, Redirect), v)
        self.assertEquals(v.args[0], "http://zope.org/")


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ExceptionHookTest))
    suite.addTest(unittest.makeSuite(ExceptionMessageRenderTest))
    suite.addTest(unittest.makeSuite(ExceptionViewsTest))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
