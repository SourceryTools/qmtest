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
"""Functional testing framework for Zope 3.

There should be a file 'ftesting.zcml' in the current directory.

$Id: functional.py 69642 2006-08-18 10:48:20Z philikon $
"""
import logging
import os.path
import re
import rfc822
import sys
import traceback
import unittest
import urllib
from StringIO import StringIO
from Cookie import SimpleCookie
from transaction import abort, commit
from ZODB.DB import DB
from ZODB.DemoStorage import DemoStorage

from zope import interface, component
from zope.publisher.browser import BrowserRequest, setDefaultSkin
from zope.publisher.http import HTTPRequest
from zope.publisher.publish import publish
from zope.publisher.xmlrpc import XMLRPCRequest
from zope.security.interfaces import Forbidden, Unauthorized
from zope.security.management import endInteraction
from zope.testing import doctest

import zope.app.testing.setup
from zope.app import zapi
from zope.app.debug import Debugger
from zope.app.publication.http import HTTPPublication
from zope.app.publication.browser import BrowserPublication
from zope.app.publication.xmlrpc import XMLRPCPublication
from zope.app.publication.soap import SOAPPublication
from zope.app.publication.interfaces import ISOAPRequestFactory
from zope.app.publication.zopepublication import ZopePublication
from zope.app.publication.http import HTTPPublication
from zope.app.publication.httpfactory import chooseClasses
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.publisher.interfaces.browser import IDefaultSkin
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.app.component.hooks import setSite, getSite


class ResponseWrapper(object):
    """A wrapper that adds several introspective methods to a response."""

    def __init__(self, response, path, omit=()):
        self._response = response
        self._path = path
        self.omit = omit
        self._body = None

    def getOutput(self):
        """Returns the full HTTP output (headers + body)"""
        body = self.getBody()
        omit = self.omit
        headers = [x
                   for x in self._response.getHeaders()
                   if x[0].lower() not in omit]
        headers.sort()
        headers = '\n'.join([("%s: %s" % (n, v)) for (n, v) in headers])
        statusline = '%s %s' % (self._response._request['SERVER_PROTOCOL'],
                                self._response.getStatusString())
        if body:
            return '%s\n%s\n\n%s' %(statusline, headers, body)
        else:
            return '%s\n%s\n' % (statusline, headers)

    def getBody(self):
        """Returns the response body"""
        if self._body is None:
            self._body = ''.join(self._response.consumeBody())

        return self._body

    def getPath(self):
        """Returns the path of the request"""
        return self._path

    def __getattr__(self, attr):
        return getattr(self._response, attr)

    __str__ = getOutput


class IManagerSetup(zope.interface.Interface):
    """Utility for enabling up a functional testing manager with needed grants

    TODO This is an interim solution.  It tries to break the dependence
    on a particular security policy, however, we need a much better
    way of managing functional-testing configurations.
    """

    def setUpManager():
        """Set up the manager, zope.mgr
        """

class FunctionalTestSetup(object):
    """Keeps shared state across several functional test cases."""

    __shared_state = { '_init': False }

    def __init__(self, config_file=None):
        """Initializes Zope 3 framework.

        Creates a volatile memory storage.  Parses Zope3 configuration files.
        """
        self.__dict__ = self.__shared_state

        if not self._init:

            # Make sure unit tests are cleaned up
            zope.app.testing.setup.placefulSetUp()
            zope.app.testing.setup.placefulTearDown()

            if not config_file:
                config_file = 'ftesting.zcml'
            self.log = StringIO()
            # Make it silent but keep the log available for debugging
            logging.root.addHandler(logging.StreamHandler(self.log))
            self.base_storage = DemoStorage("Memory Storage")
            self.db = DB(self.base_storage)
            self.app = Debugger(self.db, config_file)
            self.connection = None
            self._config_file = config_file
            self._init = True

            # Make a local grant for the test user
            setup = component.queryUtility(IManagerSetup)
            if setup is not None:
                setup.setUpManager()

            FunctionalTestSetup().connection = None

        elif config_file and config_file != self._config_file:
            # Running different tests with different configurations is not
            # supported at the moment
            raise NotImplementedError('Already configured'
                                      ' with a different config file')

    def setUp(self):
        """Prepares for a functional test case."""
        # Tear down the old demo storage (if any) and create a fresh one
        abort()
        self.db.close()
        storage = DemoStorage("Demo Storage", self.base_storage)
        self.db = self.app.db = DB(storage)
        self.connection = None

    def tearDown(self):
        """Cleans up after a functional test case."""
        abort()
        if self.connection:
            self.connection.close()
            self.connection = None
        self.db.close()
        setSite(None)

    def getRootFolder(self):
        """Returns the Zope root folder."""
        if not self.connection:
            self.connection = self.db.open()
        root = self.connection.root()
        return root[ZopePublication.root_name]

    def getApplication(self):
        """Returns the Zope application instance."""
        return self.app

class ZCMLLayer:
    """ZCML-defined test layer
    """

    __bases__ = ()

    def __init__(self, config_file, module, name):
        self.config_file = config_file
        self.__module__ = module
        self.__name__ = name

    def setUp(self):
        FunctionalTestSetup(self.config_file)

    def tearDown(self):
        raise NotImplementedError

def defineLayer(name, zcml='test.zcml'):
    """Helper function for defining layers.

    Usage: defineLayer('foo')
    """
    globals = sys._getframe(1).f_globals
    globals[name] = ZCMLLayer(
        os.path.join(os.path.split(globals['__file__'])[0], zcml),
        globals['__name__'],
        name,
        )

if os.path.exists(os.path.join('zopeskel', 'etc', 'ftesting.zcml')):
    Functional = os.path.join('zopeskel', 'etc', 'ftesting.zcml')
    FunctionalNoDevMode = os.path.join('zopeskel', 'etc', 'ftesting-base.zcml')
elif os.path.exists(os.path.join('etc', 'ftesting.zcml')):
    Functional = os.path.join('etc', 'ftesting.zcml')
    FunctionalNoDevMode = os.path.join('etc', 'ftesting-base.zcml')
else:
    # let's hope that the file is in our CWD. If not, we'll get an
    # error anyways, but we can't just throw an error if we don't find
    # that file. This module might be imported for other things as
    # well, not only starting up Zope from ftesting.zcml.    
    Functional = 'ftesting.zcml'
    FunctionalNoDevMode = 'ftesting-base.zcml'

Functional = os.path.abspath(Functional)
FunctionalNoDevMode = os.path.abspath(FunctionalNoDevMode)

Functional = ZCMLLayer(Functional, __name__, 'Functional')
FunctionalNoDevMode = ZCMLLayer(FunctionalNoDevMode, __name__,
                                'FunctionalNoDevMode')

class FunctionalTestCase(unittest.TestCase):
    """Functional test case."""

    layer = Functional

    def setUp(self):
        """Prepares for a functional test case."""
        super(FunctionalTestCase, self).setUp()
        FunctionalTestSetup().setUp()

    def tearDown(self):
        """Cleans up after a functional test case."""
        FunctionalTestSetup().tearDown()
        super(FunctionalTestCase, self).tearDown()

    def getRootFolder(self):
        """Returns the Zope root folder."""
        return FunctionalTestSetup().getRootFolder()

    def commit(self):
        commit()

    def abort(self):
        abort()


class CookieHandler(object):

    def __init__(self, *args, **kw):
        # Somewhere to store cookies between consecutive requests
        self.cookies = SimpleCookie()
        super(CookieHandler, self).__init__(*args, **kw)


    def httpCookie(self, path):
         """Return self.cookies as an HTTP_COOKIE environment value."""
         l = [m.OutputString().split(';')[0] for m in self.cookies.values()
              if path.startswith(m['path'])]
         return '; '.join(l)

    def loadCookies(self, envstring):
        self.cookies.load(envstring)

    def saveCookies(self, response):
        """Save cookies from the response."""
        # Urgh - need to play with the response's privates to extract
        # cookies that have been set
        # TODO: extend the IHTTPRequest interface to allow access to all 
        # cookies
        # TODO: handle cookie expirations
        for k,v in response._cookies.items():
            k = k.encode('utf8')
            self.cookies[k] = v['value'].encode('utf8')
            if v.has_key('path'):
                self.cookies[k]['path'] = v['path']


class BrowserTestCase(CookieHandler, FunctionalTestCase):
    """Functional test case for Browser requests."""

    def setSite(self, site):
        """Set the site which will be used to look up local components"""
        setSite(site)

    def getSite(self):
        """Returns the site which is used to look up local components"""
        return getSite()

    def makeRequest(self, path='', basic=None, form=None, env={}):
        """Creates a new request object.

        Arguments:
          path   -- the path to be traversed (e.g. "/folder1/index.html")
          basic  -- basic HTTP authentication credentials ("user:password")
          form   -- a dictionary emulating a form submission
                    (Note that field values should be Unicode strings)
          env    -- a dictionary of additional environment variables
                    (You can emulate HTTP request header
                       X-Header: foo
                     by adding 'HTTP_X_HEADER': 'foo' to env)
        """
        environment = {"HTTP_HOST": 'localhost',
                       "HTTP_REFERER": 'localhost',
                       "HTTP_COOKIE": self.httpCookie(path)}
        environment.update(env)
        app = FunctionalTestSetup().getApplication()
        request = app._request(path, '',
                               environment=environment,
                               basic=basic, form=form,
                               request=BrowserRequest)
        setDefaultSkin(request)
        return request

    def publish(self, path, basic=None, form=None, env={},
                handle_errors=False):
        """Renders an object at a given location.

        Arguments are the same as in makeRequest with the following exception:
          handle_errors  -- if False (default), exceptions will not be caught
                            if True, exceptions will return a formatted error
                            page.

        Returns the response object enhanced with the following methods:
          getOutput()    -- returns the full HTTP output as a string
          getBody()      -- returns the full response body as a string
          getPath()      -- returns the path used in the request
        """
        old_site = self.getSite()
        self.setSite(None)
        # A cookie header has been sent - ensure that future requests
        # in this test also send the cookie, as this is what browsers do.
        # We pull it apart and reassemble the header to block cookies
        # with invalid paths going through, which may or may not be correct
        if env.has_key('HTTP_COOKIE'):
            self.loadCookies(env['HTTP_COOKIE'])
            del env['HTTP_COOKIE'] # Added again in makeRequest

        request = self.makeRequest(path, basic=basic, form=form, env=env)
        response = ResponseWrapper(request.response, path)
        if env.has_key('HTTP_COOKIE'):
            self.loadCookies(env['HTTP_COOKIE'])
        publish(request, handle_errors=handle_errors)
        self.saveCookies(response)
        self.setSite(old_site)
        return response

    def checkForBrokenLinks(self, body, path, basic=None):
        """Looks for broken links in a page by trying to traverse relative
        URIs.
        """
        if not body: return

        old_site = self.getSite()
        self.setSite(None)

        from htmllib import HTMLParser
        from formatter import NullFormatter
        class SimpleHTMLParser(HTMLParser):
            def __init__(self, fmt, base):
                HTMLParser.__init__(self, fmt)
                self.base = base
            def do_base(self, attrs):
                self.base = dict(attrs).get('href', self.base)

        parser = SimpleHTMLParser(NullFormatter(), path)
        parser.feed(body)
        parser.close()
        base = parser.base
        while not base.endswith('/'):
            base = base[:-1]
        if base.startswith('http://localhost/'):
            base = base[len('http://localhost/') - 1:]

        errors = []
        for a in parser.anchorlist:
            if a.startswith('http://localhost/'):
                a = a[len('http://localhost/') - 1:]
            elif a.find(':') != -1:
                # Assume it is an external link
                continue
            elif not a.startswith('/'):
                a = base + a
            if a.find('#') != -1:
                a = a[:a.index('#')]
            # ??? what about queries (/path/to/foo?bar=baz&etc)?
            request = None
            try:
                try:
                    request = self.makeRequest(a, basic=basic)
                    publication = request.publication
                    request.processInputs()
                    publication.beforeTraversal(request)
                    object = publication.getApplication(request)
                    object = request.traverse(object)
                    publication.afterTraversal(request, object)
                except (KeyError, NameError, AttributeError, Unauthorized,
                        Forbidden):
                    e = traceback.format_exception_only(
                        *sys.exc_info()[:2])[-1]
                    errors.append((a, e.strip()))
            finally:
                publication.endRequest(request, object)
                self.setSite(old_site)

                # Make sure we don't have pending changes
                abort()

                # The request should always be closed to free resources
                # held by the request
                if request:
                    request.close()
        if errors:
            self.fail("%s contains broken links:\n" % path
                      + "\n".join(["  %s:\t%s" % (a, e) for a, e in errors]))


class HTTPTestCase(FunctionalTestCase):
    """Functional test case for HTTP requests."""

    def makeRequest(self, path='', basic=None, form=None, env={},
                    instream=None):
        """Creates a new request object.

        Arguments:
          path   -- the path to be traversed (e.g. "/folder1/index.html")
          basic  -- basic HTTP authentication credentials ("user:password")
          form   -- a dictionary emulating a form submission
                    (Note that field values should be Unicode strings)
          env    -- a dictionary of additional environment variables
                    (You can emulate HTTP request header
                       X-Header: foo
                     by adding 'HTTP_X_HEADER': 'foo' to env)
          instream  -- a stream from where the HTTP request will be read
        """
        if instream is None:
            instream = ''
        environment = {"HTTP_HOST": 'localhost',
                       "HTTP_REFERER": 'localhost'}
        environment.update(env)
        app = FunctionalTestSetup().getApplication()
        request = app._request(path, instream,
                               environment=environment,
                               basic=basic, form=form,
                               request=HTTPRequest, publication=HTTPPublication)
        return request

    def publish(self, path, basic=None, form=None, env={},
                handle_errors=False, request_body=''):
        """Renders an object at a given location.

        Arguments are the same as in makeRequest with the following exception:
          handle_errors  -- if False (default), exceptions will not be caught
                            if True, exceptions will return a formatted error
                            page.

        Returns the response object enhanced with the following methods:
          getOutput()    -- returns the full HTTP output as a string
          getBody()      -- returns the full response body as a string
          getPath()      -- returns the path used in the request
        """
        request = self.makeRequest(path, basic=basic, form=form, env=env,
                                   instream=request_body)
        response = ResponseWrapper(request.response, path)
        publish(request, handle_errors=handle_errors)
        return response


headerre = re.compile(r'(\S+): (.+)$')
def split_header(header):
    return headerre.match(header).group(1, 2)

basicre = re.compile('Basic (.+)?:(.+)?$')
def auth_header(header):
    match = basicre.match(header)
    if match:
        import base64
        u, p = match.group(1, 2)
        if u is None:
            u = ''
        if p is None:
            p = ''
        auth = base64.encodestring('%s:%s' % (u, p))
        return 'Basic %s' % auth[:-1]
    return header

def getRootFolder():
    return FunctionalTestSetup().getRootFolder()

def sync():
    getRootFolder()._p_jar.sync()

#
# Sample functional test case
#

class SampleFunctionalTest(BrowserTestCase):

    def testRootPage(self):
        response = self.publish('/')
        self.assertEquals(response.getStatus(), 200)

    def testRootPage_preferred_languages(self):
        response = self.publish('/', env={'HTTP_ACCEPT_LANGUAGE': 'en'})
        self.assertEquals(response.getStatus(), 200)

    def testNotExisting(self):
        response = self.publish('/nosuchthing', handle_errors=True)
        self.assertEquals(response.getStatus(), 404)

    def testLinks(self):
        response = self.publish('/')
        self.assertEquals(response.getStatus(), 200)
        self.checkForBrokenLinks(response.consumeBody(), response.getPath())


def sample_test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SampleFunctionalTest))
    return suite


class HTTPCaller(CookieHandler):
    """Execute an HTTP request string via the publisher"""

    def __call__(self, request_string, handle_errors=True, form=None):
        # Commit work done by previous python code.
        commit()

        # Discard leading white space to make call layout simpler
        request_string = request_string.lstrip()

        # split off and parse the command line
        l = request_string.find('\n')
        command_line = request_string[:l].rstrip()
        request_string = request_string[l+1:]
        method, path, protocol = command_line.split()
        path = urllib.unquote(path)

        instream = StringIO(request_string)
        environment = {"HTTP_COOKIE": self.httpCookie(path),
                       "HTTP_HOST": 'localhost',
                       "HTTP_REFERER": 'localhost',
                       "REQUEST_METHOD": method,
                       "SERVER_PROTOCOL": protocol,
                       }

        headers = [split_header(header)
                   for header in rfc822.Message(instream).headers]
        for name, value in headers:
            name = ('_'.join(name.upper().split('-')))
            if name not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                name = 'HTTP_' + name
            environment[name] = value.rstrip()

        auth_key = 'HTTP_AUTHORIZATION'
        if environment.has_key(auth_key):
            environment[auth_key] = auth_header(environment[auth_key])

        old_site = getSite()
        setSite(None)

        request_cls, publication_cls = self.chooseRequestClass(method, path,
                                                               environment)
        app = FunctionalTestSetup().getApplication()

        request = app._request(
            path, instream,
            environment=environment,
            request=request_cls, publication=publication_cls)
        if IBrowserRequest.providedBy(request):
            # only browser requests have skins
            setDefaultSkin(request)

        if form is not None:
            if request.form:
                raise ValueError("only one set of form values can be provided")
            request.form = form

        response = ResponseWrapper(
            request.response, path,
            omit=('x-content-type-warning', 'x-powered-by'),
            )

        publish(request, handle_errors=handle_errors)
        self.saveCookies(response)
        setSite(old_site)

        # sync Python connection:
        getRootFolder()._p_jar.sync()

        return response

    def chooseRequestClass(self, method, path, environment):
        """Choose and return a request class and a publication class"""
        # note that `path` is unused by the default implementation (BBB)
        return chooseClasses(method, environment)


def FunctionalDocFileSuite(*paths, **kw):
    globs = kw.setdefault('globs', {})
    globs['http'] = HTTPCaller()
    globs['getRootFolder'] = getRootFolder
    globs['sync'] = sync

    kw['package'] = doctest._normalize_module(kw.get('package'))

    kwsetUp = kw.get('setUp')
    def setUp(test):
        FunctionalTestSetup().setUp()

        if kwsetUp is not None:
            kwsetUp(test)
    kw['setUp'] = setUp

    kwtearDown = kw.get('tearDown')
    def tearDown(test):
        if kwtearDown is not None:
            kwtearDown(test)
        FunctionalTestSetup().tearDown()
    kw['tearDown'] = tearDown

    if 'optionflags' not in kw:
        old = doctest.set_unittest_reportflags(0)
        doctest.set_unittest_reportflags(old)
        kw['optionflags'] = (old
                             | doctest.ELLIPSIS
                             | doctest.REPORT_NDIFF
                             | doctest.NORMALIZE_WHITESPACE)

    suite = doctest.DocFileSuite(*paths, **kw)
    suite.layer = Functional
    return suite


if __name__ == '__main__':
    unittest.main()
