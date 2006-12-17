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
"""Tests to check talesapi zcml configuration

$Id: test_directives.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest
from cStringIO import StringIO

from zope.configuration.xmlconfig import xmlconfig, XMLConfig
from zope.interface import Interface, implements
from zope.traversing.interfaces import ITraversable

import zope.app.pagetemplate
from zope.app.testing import ztapi
from zope.app.testing.placelesssetup import PlacelessSetup
from zope.app.pagetemplate.engine import Engine

template = """<configure 
   xmlns='http://namespaces.zope.org/zope'
   xmlns:tales='http://namespaces.zope.org/tales'>
   %s
   </configure>"""


class Handler(object):
    pass

class Test(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(Test, self).setUp()
        XMLConfig('meta.zcml', zope.app.pagetemplate)()

    def testExpressionType(self):
        xmlconfig(StringIO(template % (
            """
            <tales:expressiontype
              name="test"
              handler="zope.app.pagetemplate.tests.test_directives.Handler"
              />
            """
            )))
        self.assert_("test" in Engine.getTypes())
        self.assert_(Handler is Engine.getTypes()['test'])

def test_suite():
    loader=unittest.TestLoader()
    return loader.loadTestsFromTestCase(Test)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
