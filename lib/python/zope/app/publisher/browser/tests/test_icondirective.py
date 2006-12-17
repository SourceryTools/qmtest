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
"""Test Icon-Directive

$Id: test_icondirective.py 69142 2006-07-16 14:14:34Z jim $
"""
import os
from StringIO import StringIO
from unittest import TestCase, main, makeSuite

from zope.configuration.exceptions import ConfigurationError
from zope.configuration.xmlconfig import xmlconfig, XMLConfig
from zope.interface import implements
from zope.publisher.browser import TestRequest
from zope.security.checker import ProxyFactory, CheckerPublic
from zope.security.interfaces import Forbidden
from zope.security.proxy import removeSecurityProxy
from zope.traversing.interfaces import IContainmentRoot

import zope.app.publisher.browser
from zope.app import zapi
from zope.app.component.tests.views import IC
from zope.app.component.interfaces import ISite
from zope.app.publisher.browser.tests import support
from zope.app.testing.placelesssetup import PlacelessSetup


template = """<configure
   xmlns='http://namespaces.zope.org/zope'
   xmlns:browser='http://namespaces.zope.org/browser'
   i18n_domain='zope'
   >
   %s
   </configure>"""


request = TestRequest()

class Ob(object):
    implements(IC)

ob = Ob()
request._vh_root = support.site

def defineCheckers():
    # define the appropriate checker for a FileResource for these tests
    from zope.app.security.protectclass import protectName
    from zope.app.publisher.browser.fileresource import FileResource
    protectName(FileResource, '__call__', 'zope.Public')


class Test(support.SiteHandler, PlacelessSetup, TestCase):

    def setUp(self):
        super(Test, self).setUp()
        XMLConfig('meta.zcml', zope.app.publisher.browser)()
        defineCheckers()
        
    def test(self):
        self.assertEqual(
            zapi.queryMultiAdapter((ob, request), name='zmi_icon'),
            None)

        import zope.app.publisher.browser.tests as p
        path = os.path.dirname(p.__file__)
        path = os.path.join(path, 'testfiles', 'test.gif')

        # Configure the icon and make sure we can render the resulting view:
        xmlconfig(StringIO(template % (
            '''
            <browser:icon name="zmi_icon"
                      for="zope.app.component.tests.views.IC"
                      file="%s" />
            ''' % path
            )))

        view = zapi.getMultiAdapter((ob, request), name='zmi_icon')
        rname = 'zope-app-component-tests-views-IC-zmi_icon.gif'
        self.assertEqual(
            view(),
            '<img src="http://127.0.0.1/@@/%s" alt="IC" '
            'width="16" height="16" border="0" />'
            % rname)

        # Make sure that the title attribute works
        xmlconfig(StringIO(template % (
            '''
            <browser:icon name="zmi_icon_w_title"
                      for="zope.app.component.tests.views.IC"
                      file="%s" title="click this!" />
            ''' % path
            )))

        view = zapi.getMultiAdapter((ob, request), name='zmi_icon_w_title')
        rname = 'zope-app-component-tests-views-IC-zmi_icon_w_title.gif'
        self.assertEqual(
            view(),
            '<img src="http://127.0.0.1/@@/%s" alt="click this!" '
            'width="16" height="16" border="0" />'
            % rname)


        # Make sure that the image was installed as a resource:
        resource = ProxyFactory(zapi.getAdapter(request, name=rname))
        self.assertRaises(Forbidden, getattr, resource, '_testData')
        resource = removeSecurityProxy(resource)
        self.assertEqual(resource._testData(), open(path, 'rb').read())

    def testResource(self):
        self.assertEqual(
            zapi.queryMultiAdapter((ob, request), name='zmi_icon'), None)

        import zope.app.publisher.browser.tests as p
        path = os.path.dirname(p.__file__)
        path = os.path.join(path, 'testfiles', 'test.gif')

        xmlconfig(StringIO(template % (
            '''
            <browser:resource name="zmi_icon_res"
                      image="%s" />
            <browser:icon name="zmi_icon"
                      for="zope.app.component.tests.views.IC"
                      resource="zmi_icon_res" />
            ''' % path
            )))

        view = zapi.getMultiAdapter((ob, request), name='zmi_icon')
        rname = "zmi_icon_res"
        self.assertEqual(
            view(),
            '<img src="http://127.0.0.1/@@/%s" alt="IC" width="16" '
            'height="16" border="0" />'
            % rname)

        resource = ProxyFactory(zapi.getAdapter(request, name=rname))

        self.assertRaises(Forbidden, getattr, resource, '_testData')
        resource = removeSecurityProxy(resource)
        self.assertEqual(resource._testData(), open(path, 'rb').read())

    def testResourceErrors(self):
        self.assertEqual(
            zapi.queryMultiAdapter((ob, request), name='zmi_icon'), None)

        import zope.app.publisher.browser.tests as p
        path = os.path.dirname(p.__file__)
        path = os.path.join(path, 'testfiles', 'test.gif')

        config = StringIO(template % (
            '''
            <browser:resource name="zmi_icon_res"
                      image="%s" />
            <browser:icon name="zmi_icon"
                      for="zope.app.component.tests.views.IC"
                      file="%s"
                      resource="zmi_icon_res" />
            ''' % (path, path)
            ))
        self.assertRaises(ConfigurationError, xmlconfig, config)

        config = StringIO(template % (
            """
            <browser:icon name="zmi_icon"
                      for="zope.app.component.tests.views.IC"
                      />
            """
            ))
        self.assertRaises(ConfigurationError, xmlconfig, config)


def test_suite():
    return makeSuite(Test)

if __name__=='__main__':
    main(defaultTest='test_suite')
