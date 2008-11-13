##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Document Template Tests

$Id: testdt_with.py 26559 2004-07-15 21:22:32Z srichter $
"""
import unittest
from zope.documenttemplate.tests.dtmltestbase import DTMLTestBase

class TestDT_With(DTMLTestBase):

    def testBasic(self):
        class person(object):
            name=u'Jim'
            height_inches=73

        result = self.doc_class(u'''<dtml-with person>
        Hi, my name is <dtml-var name>
        My height is <dtml-var "height_inches*2.54"> centimeters.
        </dtml-with>''')(person=person)

        expected = u"""        Hi, my name is Jim
        My height is 185.42 centimeters.
        """

        self.assertEqual(result, expected)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDT_With))
    return suite



if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())
