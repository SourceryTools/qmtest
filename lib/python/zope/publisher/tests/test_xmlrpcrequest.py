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
"""XML-RPC Request Tests

$Id: test_xmlrpcrequest.py 38357 2005-09-07 20:14:34Z srichter $
"""
import unittest
from StringIO import StringIO

from zope.publisher.base import DefaultPublication
from zope.publisher.http import HTTPCharsets
from zope.publisher.xmlrpc import XMLRPCRequest

class Publication(DefaultPublication):

    require_docstrings = 0

    def getDefaultTraversal(self, request, ob):
        if hasattr(ob, 'browserDefault'):
            return ob.browserDefault(request)
        return ob, ()


class TestXMLRPCRequest(XMLRPCRequest, HTTPCharsets):
    """Make sure that our request also implements IHTTPCharsets, so that we do
    not need to register any adapters."""

    def __init__(self, *args, **kw):
        self.request = self
        XMLRPCRequest.__init__(self, *args, **kw)


xmlrpc_call = u'''<?xml version='1.0'?>
<methodCall>
  <methodName>action</methodName>
  <params>
    <param>
      <value><int>1</int></value>
    </param>
  </params>
</methodCall>
'''


class XMLRPCTests(unittest.TestCase):
    """The only thing different to HTTP is the input processing; so there
       is no need to redo all the HTTP tests again.
    """

    _testEnv =  {
        'PATH_INFO':          '/folder/item2/view/',
        'QUERY_STRING':       '',
        'SERVER_URL':         'http://foobar.com',
        'HTTP_HOST':          'foobar.com',
        'CONTENT_LENGTH':     '0',
        'REQUEST_METHOD':     'POST',
        'HTTP_AUTHORIZATION': 'Should be in accessible',
        'GATEWAY_INTERFACE':  'TestFooInterface/1.0',
        'HTTP_OFF_THE_WALL':  "Spam 'n eggs",
        'HTTP_ACCEPT_CHARSET': 'ISO-8859-1, UTF-8;q=0.66, UTF-16;q=0.33',
    }

    def setUp(self):
        super(XMLRPCTests, self).setUp()

        class AppRoot(object):
            pass

        class Folder(object):
            pass

        class Item(object):

            def __call__(self, a, b):
                return "%s, %s" % (`a`, `b`)

            def doit(self, a, b):
                return 'do something %s %s' % (a, b)

        class View(object):

            def action(self, a):
                return "Parameter[type: %s; value: %s" %(
                    type(a).__name__, `a`)

        class Item2(object):
            view = View()


        self.app = AppRoot()
        self.app.folder = Folder()
        self.app.folder.item = Item()
        self.app.folder.item2 = Item2()


    def _createRequest(self, extra_env={}, body=""):
        env = self._testEnv.copy()
        env.update(extra_env)
        if len(body):
            env['CONTENT_LENGTH'] = str(len(body))

        publication = Publication(self.app)
        instream = StringIO(body)
        request = TestXMLRPCRequest(instream, env)
        request.setPublication(publication)
        return request


    def testProcessInput(self):
        req = self._createRequest({}, xmlrpc_call)
        req.processInputs()
        self.failUnlessEqual(req._args, (1,))
        self.failUnlessEqual(tuple(req._path_suffix), ('action',))


    def testTraversal(self):
        req = self._createRequest({}, xmlrpc_call)
        req.processInputs()
        action = req.traverse(self.app)
        self.failUnlessEqual(action(*req._args),
                             "Parameter[type: int; value: 1")


def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(XMLRPCTests)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
