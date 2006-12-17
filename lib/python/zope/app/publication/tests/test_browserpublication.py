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
"""Browser Publication Tests

$Id: test_browserpublication.py 38357 2005-09-07 20:14:34Z srichter $
"""
import unittest

from zope.app.testing import ztapi
from StringIO import StringIO

from zope.security.interfaces import ForbiddenAttribute
from zope.interface import Interface, implements

from zope.publisher.publish import publish
from zope.publisher.browser import TestRequest, BrowserView
from zope.publisher.interfaces.browser import IBrowserPublisher

from zope.proxy import getProxiedObject
from zope.security.proxy import Proxy, removeSecurityProxy
from zope.security.checker import defineChecker, NamesChecker

from zope.app.security.principalregistry import principalRegistry

from zope.app.publication.browser import BrowserPublication
from zope.app.publication.httpfactory import HTTPPublicationRequestFactory
from zope.app.publication.traversers import TestTraverser
from zope.app.publication.tests.test_zopepublication \
     import BasePublicationTests as BasePublicationTests_

from persistent import Persistent

def foo():
    "I am an otherwise empty docstring."
    return '<html><body>hello base fans</body></html>'

class DummyPublished(object):
    implements(IBrowserPublisher)

    def publishTraverse(self, request, name):
        if name == 'bruce':
            return foo
        raise KeyError(name)

    def browserDefault(self, request):
        return self, ['bruce']



class DummyView(DummyPublished, BrowserView):

    __Security_checker__ = NamesChecker(["browserDefault", "publishTraverse"])


class BasePublicationTests(BasePublicationTests_):

    def _createRequest(self, path, publication, **kw):
        request = TestRequest(PATH_INFO=path, **kw)
        request.setPublication(publication)
        return request

class SimpleObject(object):
    def __init__(self, v):
        self.v = v

class I1(Interface):
    pass

class mydict(dict):
    implements(I1)


class O1(Persistent):
    implements(I1)


class BrowserDefaultTests(BasePublicationTests):
    """
    test browser default

    many views lead to a default view
    <base href="/somepath/@@view/view_method">

    """
    klass = BrowserPublication

    def testBaseTagNoBase(self):
        self._testBaseTags('/somepath/@@view/', '')

    def testBaseTag1(self):
        self._testBaseTags('/somepath/@@view',
                           'http://127.0.0.1/somepath/@@view/bruce')

    def testBaseTag2(self):
        self._testBaseTags('/somepath/',
                           'http://127.0.0.1/somepath/@@view/bruce')

    def testBaseTag3(self):
        self._testBaseTags('/somepath',
                           'http://127.0.0.1/somepath/@@view/bruce')



    def _testBaseTags(self, url, expected):
        # Make sure I1 and O1 are visible in the module namespace
        # so that the classes can be pickled.
        import transaction

        pub = BrowserPublication(self.db)

        ztapi.browserView(I1, 'view', DummyView)
        ztapi.setDefaultViewName(I1, 'view')
        ztapi.browserViewProviding(None, TestTraverser, IBrowserPublisher)

        ob = O1()

        ## the following is for running the tests standalone
        principalRegistry.defineDefaultPrincipal(
            'tim', 'timbot', 'ai at its best')

        # now place our object inside the application

        connection = self.db.open()
        app = connection.root()['Application']
        app.somepath = ob
        transaction.commit()
        connection.close()

        defineChecker(app.__class__, NamesChecker(somepath='xxx'))

        req = self._createRequest(url, pub)
        response = req.response

        publish(req, handle_errors=0)

        self.assertEqual(response.getBase(), expected)


    def _createRequest(self, path, publication, **kw):
        request = TestRequest(PATH_INFO=path, **kw)
        request.setPublication(publication)
        return request



class BrowserPublicationTests(BasePublicationTests):

    klass = BrowserPublication

    def testAdaptedTraverseNameWrapping(self):

        class Adapter(object):
            implements(IBrowserPublisher)
            def __init__(self, context, request):
                self.context = context
                self.counter = 0

            def publishTraverse(self, request, name):
                self.counter += 1
                return self.context[name]

        ztapi.browserViewProviding(I1, Adapter, IBrowserPublisher)
        ob = mydict()
        ob['bruce'] = SimpleObject('bruce')
        ob['bruce2'] = SimpleObject('bruce2')
        pub = self.klass(self.db)
        ob2 = pub.traverseName(self._createRequest('/bruce', pub), ob, 'bruce')
        self.assertRaises(ForbiddenAttribute, getattr, ob2, 'v')
        self.assertEqual(removeSecurityProxy(ob2).v, 'bruce')

    def testAdaptedTraverseDefaultWrapping(self):
        # Test default content and make sure that it's wrapped.
        class Adapter(object):
            implements(IBrowserPublisher)
            def __init__(self, context, request):
                self.context = context

            def browserDefault(self, request):
                return (self.context['bruce'], 'dummy')

        ztapi.browserViewProviding(I1, Adapter, IBrowserPublisher)
        ob = mydict()
        ob['bruce'] = SimpleObject('bruce')
        ob['bruce2'] = SimpleObject('bruce2')
        pub = self.klass(self.db)
        ob2, x = pub.getDefaultTraversal(self._createRequest('/bruce',pub), ob)
        self.assertEqual(x, 'dummy')
        self.assertRaises(ForbiddenAttribute, getattr, ob2, 'v')
        self.assertEqual(removeSecurityProxy(ob2).v, 'bruce')

    def testTraverseName(self):
        pub = self.klass(self.db)
        class C(object):
            x = SimpleObject(1)
        ob = C()
        r = self._createRequest('/x',pub)
        ztapi.browserViewProviding(None, TestTraverser, IBrowserPublisher)
        ob2 = pub.traverseName(r, ob, 'x')
        self.assertRaises(ForbiddenAttribute, getattr, ob2, 'v')
        self.assertEqual(removeSecurityProxy(ob2).v, 1)

    def testTraverseNameView(self):
        pub = self.klass(self.db)
        class I(Interface): pass
        class C(object):
            implements(I)
        ob = C()
        class V(object):
            def __init__(self, context, request): pass
        r = self._createRequest('/@@spam',pub)
        ztapi.browserView(I, 'spam', V)
        ob2 = pub.traverseName(r, ob, '@@spam')
        self.assertEqual(ob2.__class__, V)

    def testTraverseNameSiteManager(self):
        pub = self.klass(self.db)
        class C(object):
            def getSiteManager(self):
                return SimpleObject(1)
        ob = C()
        r = self._createRequest('/++etc++site',pub)
        ob2 = pub.traverseName(r, ob, '++etc++site')
        self.assertRaises(ForbiddenAttribute, getattr, ob2, 'v')
        self.assertEqual(removeSecurityProxy(ob2).v, 1)

    def testTraverseNameApplicationControl(self):
        from zope.app.applicationcontrol.applicationcontrol \
             import applicationController, applicationControllerRoot
        pub = self.klass(self.db)
        r = self._createRequest('/++etc++process',pub)
        ac = pub.traverseName(r,
                              applicationControllerRoot,
                              '++etc++process')
        self.assertEqual(ac, applicationController)
        r = self._createRequest('/++etc++process',pub)
        app = r.publication.getApplication(r)
        self.assertEqual(app, applicationControllerRoot)

    def testHEADFuxup(self):
        pub = self.klass(None)

        class User(object):
            id = 'bob'

        # With a normal request, we should get a body:
        request = TestRequest(StringIO(''), {'PATH_INFO': '/'})
        request.setPrincipal(User())
        request.response.setResult(u"spam")
        pub.afterCall(request, None)
        self.assertEqual(request.response.consumeBody(), 'spam' )

        # But with a HEAD request, the body should be empty
        request = TestRequest(StringIO(''), {'PATH_INFO': '/'})
        request.setPrincipal(User())
        request.method = 'HEAD'
        request.response.setResult(u"spam")
        pub.afterCall(request, None)
        self.assertEqual(request.response.consumeBody(), '')

    def testUnicode_NO_HTTP_CHARSET(self):
        # Test so that a unicode body doesn't cause a UnicodeEncodeError
        request = TestRequest(StringIO(''), {})
        request.response.setResult(u"\u0442\u0435\u0441\u0442")
        headers = request.response.getHeaders()
        headers.sort()
        self.assertEqual(
            headers,
            [('Content-Length', '8'),
             ('Content-Type', 'text/plain;charset=utf-8'),
             ('X-Content-Type-Warning', 'guessed from content'),
             ('X-Powered-By', 'Zope (www.zope.org), Python (www.python.org)')])
        self.assertEqual(
            request.response.consumeBody(),
            '\xd1\x82\xd0\xb5\xd1\x81\xd1\x82')


class HTTPPublicationRequestFactoryTests(BasePublicationTests):

    def setUp(self):
        super(BasePublicationTests, self).setUp()
        from zope.app.publication.requestpublicationregistry import \
             factoryRegistry
        from zope.app.publication.requestpublicationfactories \
            import SOAPFactory, XMLRPCFactory, HTTPFactory, BrowserFactory

        factoryRegistry.register('*', '*', 'HTTP', 0, HTTPFactory())
        factoryRegistry.register('POST', 'text/xml', 'SOAP', 20, SOAPFactory())
        factoryRegistry.register('POST', 'text/xml', 'XMLRPC', 10,
                                 XMLRPCFactory())
        factoryRegistry.register('GET', '*', 'BROWSER', 10, BrowserFactory())
        factoryRegistry.register('POST', '*', 'BROWSER', 10, BrowserFactory())
        factoryRegistry.register('HEAD', '*', 'BROWSER', 10, BrowserFactory())

    def testGetBackSamePublication(self):
        factory = HTTPPublicationRequestFactory(db=None)
        args = (StringIO(''), {})
        self.assert_(id(factory(*args).publication) ==
                     id(factory(*args).publication))


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(BrowserPublicationTests, 'test'),
        unittest.makeSuite(BrowserDefaultTests, 'test'),
        unittest.makeSuite(HTTPPublicationRequestFactoryTests, 'test'),
        ))


if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())
