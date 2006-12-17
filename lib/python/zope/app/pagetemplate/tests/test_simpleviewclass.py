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
"""Simple View Class Tests

$Id: test_simpleviewclass.py 29143 2005-02-14 22:43:16Z srichter $
"""
import unittest

from zope.app.pagetemplate.simpleviewclass import SimpleViewClass
from zope.app.pagetemplate.tests.simpletestview import SimpleTestView
from zope.publisher.browser import TestRequest

class data(object): pass

class SimpleViewTestCase(unittest.TestCase):

    def test_simple(self):
        ob = data()
        request = TestRequest()
        view = SimpleTestView(ob, request)
        macro = view['test']
        out = view()
        self.assertEqual(out,
                         '<html>\n'
                         '  <body>\n'
                         '    <p>hello world</p>\n'
                         '  </body>\n</html>\n')

    def test_name(self):
        View = SimpleViewClass('testsimpleviewclass.pt', name='test.html')
        view = View(None, None)
        self.assertEqual(view.__name__, 'test.html')

    def test_getitem(self):
        View = SimpleViewClass('testsimpleviewclass.pt', name='test.html')
        view = View(None, None)
        self.assert_(view['test'] is not None)
        self.assertRaises(KeyError, view.__getitem__, 'foo')

    def test_WBases(self):
        class C(object): pass

        SimpleTestView = SimpleViewClass('testsimpleviewclass.pt', bases=(C, ))

        self.failUnless(issubclass(SimpleTestView, C))

        ob = data()
        request = TestRequest()
        view = SimpleTestView(ob, request)
        macro = view['test']
        out = view()
        self.assertEqual(out,
                         '<html>\n'
                         '  <body>\n'
                         '    <p>hello world</p>\n'
                         '  </body>\n</html>\n')

def test_suite():
    return unittest.makeSuite(SimpleViewTestCase)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
