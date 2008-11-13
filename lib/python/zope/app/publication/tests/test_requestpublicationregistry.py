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
"""Tests for the HTTP Publication Request Factory.

$Id: test_requestpublicationregistry.py 70826 2006-10-20 03:41:16Z baijum $
"""
from unittest import TestCase, TestSuite, main, makeSuite

from StringIO import StringIO

from zope import component, interface
from zope.interface.verify import verifyClass
from zope.component.testing import PlacelessSetup

from zope.configuration.exceptions import ConfigurationError
from zope.app.publication import interfaces
from zope.app.publication.interfaces import IRequestPublicationRegistry
from zope.app.publication.requestpublicationregistry import \
     RequestPublicationRegistry
from zope.app.publication.requestpublicationfactories import \
     HTTPFactory, SOAPFactory, BrowserFactory, XMLRPCFactory


def DummyFactory():
    return object

class DummyRequestFactory(object):
    def __call__(self, input_stream, env):
        self.input_stream = input_stream
        self.env = env
        return self

    def setPublication(self, pub):
        self.pub = pub

class Test(PlacelessSetup, TestCase):

    def test_interface(self):
        verifyClass(IRequestPublicationRegistry, RequestPublicationRegistry)

    def test_registration(self):
        r = RequestPublicationRegistry()
        xmlrpc_f = DummyFactory()
        r.register('POST', 'text/xml', 'xmlrpc', 0, xmlrpc_f)
        soap_f = DummyFactory()
        r.register('POST', 'text/xml', 'soap', 1, soap_f)
        browser_f = DummyFactory()
        r.register('*', '*', 'browser_default', 0, browser_f)
        l = r.getFactoriesFor('POST', 'text/xml')
        self.assertEqual(
            l,
            [{'name' : 'soap', 'priority' : 1, 'factory' : object},
             {'name' : 'xmlrpc', 'priority' : 0, 'factory' : object}])
        self.assertEqual(r.getFactoriesFor('POST', 'text/html'), None)

    def test_configuration_same_priority(self):
        r = RequestPublicationRegistry()
        xmlrpc_f = DummyFactory()
        r.register('POST', 'text/xml', 'xmlrpc', 0, DummyFactory)
        r.register('POST', 'text/xml', 'soap', 1, DummyFactory())
        # try to register a factory with the same priority
        self.assertRaises(ConfigurationError, r.register,
                          'POST', 'text/xml', 'soap2', 1, DummyFactory())

    def test_configuration_reregistration(self):
        r = RequestPublicationRegistry()
        xmlrpc_f = DummyFactory()
        r.register('POST', 'text/xml', 'xmlrpc', 0, DummyFactory)
        r.register('POST', 'text/xml', 'soap', 1, DummyFactory())
        # re-register 'soap' but with priority 2
        r.register('POST', 'text/xml', 'soap', 2, DummyFactory())
        factory_data = r.getFactoriesFor('POST', 'text/xml')
        priorities = [item['priority'] for item in factory_data]
        self.assertEqual(priorities, [2, 0])

    def test_realfactories(self):
        r = RequestPublicationRegistry()
        r.register('POST', '*', 'post_fallback', 0, HTTPFactory())
        r.register('POST', 'text/xml', 'xmlrpc', 1, XMLRPCFactory())
        r.register('POST', 'text/xml', 'soap', 2, SOAPFactory())
        r.register('GET', '*', 'http', 0, HTTPFactory())
        r.register('PUT', '*', 'http', 0, HTTPFactory())
        r.register('HEAD', '*', 'http', 0, HTTPFactory())
        r.register('*', '*', 'http', 1, BrowserFactory())

        self.assertEqual(len(r.getFactoriesFor('POST', 'text/xml')) , 2)
        self.assertEqual(len(r.getFactoriesFor('POST', 'text/xml; charset=utf-8')) , 2)
        self.assertEqual(len(r.getFactoriesFor('POST', '*')) , 1)
        self.assertEqual(r.getFactoriesFor('GET', 'text/html') , None)
        self.assertEqual(len(r.getFactoriesFor('HEAD', '*')) , 1)

        env =  {
            'SERVER_URL':         'http://127.0.0.1',
            'HTTP_HOST':          '127.0.0.1',
            'CONTENT_LENGTH':     '0',
            'GATEWAY_INTERFACE':  'TestFooInterface/1.0',
            }

        soaprequestfactory = DummyRequestFactory()
        interface.directlyProvides(
            soaprequestfactory, interfaces.ISOAPRequestFactory)
        component.provideUtility(soaprequestfactory)

        self.assert_(
            isinstance(r.lookup('POST', 'text/xml', env), XMLRPCFactory))
        env['HTTP_SOAPACTION'] = 'foo'
        self.assert_(
            isinstance(r.lookup('POST', 'text/xml', env), SOAPFactory))
        self.assert_(
            isinstance(r.lookup('FOO', 'zope/sucks', env), BrowserFactory))


def test_suite():
    return TestSuite((
        makeSuite(Test),
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')
