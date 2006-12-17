##############################################################################
#
# Copyright (c) 2004-2006 Zope Corporation and Contributors.
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
"""Doc tests for the pagetemplate's 'engine' module

$Id: test_engine.py 69506 2006-08-15 12:09:32Z ctheune $
"""
import unittest
from zope.testing.doctestunit import DocTestSuite

import zope.component
from zope.app.pagetemplate.engine import _Engine
from zope.proxy import isProxy
from zope.traversing.interfaces import IPathAdapter

class DummyNamespace(object):

    def __init__(self, context):
        self.context = context

class EngineTests(unittest.TestCase):

    def setUp(self):
        gsm = zope.component.getGlobalSiteManager()
        gsm.registerAdapter(DummyNamespace, required=(), provided=IPathAdapter, name='test')

    def tearDown(self):
        gsm = zope.component.getGlobalSiteManager()
        gsm.unregisterAdapter(DummyNamespace, required=(), provided=IPathAdapter, name='test')

    def test_issue574(self):
        engine = _Engine()
        namespace = engine.getFunctionNamespace('test')
        self.failUnless(isProxy(namespace))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(DocTestSuite('zope.app.pagetemplate.engine'))
    suite.addTest(unittest.makeSuite(EngineTests))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

