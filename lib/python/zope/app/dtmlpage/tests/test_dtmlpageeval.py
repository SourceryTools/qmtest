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
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""DTML Page Evaluation Tests

$Id: test_dtmlpageeval.py 26551 2004-07-15 07:06:37Z srichter $
"""
from unittest import TestCase, main, makeSuite
from zope.app.container.contained import contained
from zope.app.dtmlpage.browser import DTMLPageEval

class Test(TestCase):

    def test(self):

        class Template(object):
            def render(self, request, **kw):
                self.called = request, kw
                request.response.setHeader('content-type', self.content_type)
                return 42

            content_type = 'text/x-test'

        class Folder(object):
            name='zope'

        folder = Folder()

        class Request(object):

            def _getResponse(self):
                return self

            response = property(_getResponse)

            def setHeader(self, name, value):
                setattr(self, name, value)

        request = Request()
        template = contained(Template(), folder, 'foo')

        view = DTMLPageEval()
        # Do manually, since directive adds BrowserView as base class
        view.context = template
        view.request = request
        self.assertEqual(view.index(request), 42)
        self.assertEqual(template.called, (request, {}))
        self.assertEqual(getattr(request, 'content-type'), 'text/x-test')

def test_suite():
    return makeSuite(Test)

if __name__=='__main__':
    main(defaultTest='test_suite')
