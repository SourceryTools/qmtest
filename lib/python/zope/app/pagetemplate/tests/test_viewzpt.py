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
"""View ZPT Tests

$Id: test_viewzpt.py 29143 2005-02-14 22:43:16Z srichter $
"""
import unittest

from zope.app import zapi
from zope.app.testing import ztapi
from zope.interface import Interface, implements

from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.app.component.testing import PlacefulSetup


class I1(Interface):
    pass

class C1(object):
    implements(I1)

class InstanceWithContext(object):
    def __init__(self, context):
        self.context = context

class InstanceWithoutContext(object):
    pass


class TestViewZPT(PlacefulSetup, unittest.TestCase):

    def setUp(self):
        super(TestViewZPT, self).setUp()
        self.t = ViewPageTemplateFile('test.pt')
        self.context = C1()

    def testNamespaceContextAvailable(self):
        context = self.context
        request = None

        namespace = self.t.pt_getContext(InstanceWithContext(context), request)
        self.failUnless(namespace['context'] is context)
        self.failUnless('views' in namespace)

    def testNamespaceHereNotAvailable(self):
        request = None
        self.assertRaises(AttributeError, self.t.pt_getContext,
                          InstanceWithoutContext(), request)

    def testViewMapper(self):
        the_view = "This is the view"
        the_view_name = "some view name"
        def ViewMaker(*args, **kw):
            return the_view

        from zope.component.interfaces import IPresentationRequest

        ztapi.provideView(I1, IPresentationRequest, Interface,
                          the_view_name, ViewMaker)

        class MyRequest(object):
            implements(IPresentationRequest)

        request = MyRequest()

        namespace = self.t.pt_getContext(InstanceWithContext(self.context),
                                         request)
        views = namespace['views']
        self.failUnless(the_view is views[the_view_name])

    def test_debug_flags(self):
        from zope.publisher.browser import TestRequest
        self.request = TestRequest()
        self.request.debug.sourceAnnotations = False
        self.assert_('test.pt' not in self.t(self))
        self.request.debug.sourceAnnotations = True
        self.assert_('test.pt' in self.t(self))

        t = ViewPageTemplateFile('testsimpleviewclass.pt')
        self.request.debug.showTAL = False
        self.assert_('metal:' not in t(self))
        self.request.debug.showTAL = True
        self.assert_('metal:' in t(self))

    def test_render_sets_content_type_unless_set(self):
        from zope.publisher.browser import TestRequest
        t = ViewPageTemplateFile('test.pt')

        self.request = TestRequest()
        response = self.request.response
        self.assert_(not response.getHeader('Content-Type'))
        t(self)
        self.assertEquals(response.getHeader('Content-Type'), 'text/html')

        self.request = TestRequest()
        response = self.request.response
        response.setHeader('Content-Type', 'application/x-test-junk')
        t(self)
        self.assertEquals(response.getHeader('Content-Type'),
                          'application/x-test-junk')
        

class TestViewZPTContentType(unittest.TestCase):

    def testInitWithoutType(self):
        t = ViewPageTemplateFile('test.pt')
        t._cook_check()
        self.assertEquals(t.content_type, "text/html")

        t = ViewPageTemplateFile('testxml.pt')
        t._cook_check()
        self.assertEquals(t.content_type, "text/xml")

    def testInitWithType(self):
        t = ViewPageTemplateFile('test.pt', content_type="text/plain")
        t._cook_check()
        self.assertEquals(t.content_type, "text/plain")

        t = ViewPageTemplateFile('testxml.pt', content_type="text/plain")
        t._cook_check()
        self.assertEquals(t.content_type, "text/xml")


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestViewZPT))
    suite.addTest(unittest.makeSuite(TestViewZPTContentType))
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())
