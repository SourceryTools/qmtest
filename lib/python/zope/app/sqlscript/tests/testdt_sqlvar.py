##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""DT_SQLVar Tests

$Id: testdt_sqlvar.py 25177 2004-06-02 13:17:31Z jim $
"""

import unittest
from zope.app.sqlscript.dtml import SQLDTML

class TestDT_SQLVar(unittest.TestCase):

    doc_class = SQLDTML


    def testSimpleUse(self):
        html = self.doc_class("<dtml-sqlvar column type=nb>")
        result = "'name'"

        self.assertEqual(html(column='name'), result)


    def testIntType(self):
        html = self.doc_class("<dtml-sqlvar column type=int>")
        result = "3"

        self.assertEqual(html(column=3), result)
        self.assertEqual(html(column='3'), result)
        self.assertEqual(html(column=3.1), result)


    def testFloatType(self):
        html = self.doc_class("<dtml-sqlvar column type=float>")
        result = "3.1"

        self.assertEqual(html(column=3), "3.0")
        self.assertEqual(html(column='3'), "3")
        self.assertEqual(html(column='3.1'), result)
        self.assertEqual(html(column=3.1), result)


    def testStringTypeAndEscaping(self):
        html = self.doc_class("<dtml-sqlvar column type=nb>")

        self.assertEqual(html(column='name'), "'name'")
        self.assertEqual(html(column='Let\'s do it'), "'Let''s do it'")
        # Acid test :)
        self.assertEqual(html(column="\'\'"), "''''''")


    def testOptional(self):
        html = self.doc_class("""<dtml-sqlvar column type=nb optional>""")
        result = "null"

        self.assertEqual(html(column=None), result)
        self.assertEqual(html(column=''), result)
        self.assertEqual(html(), result)



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDT_SQLVar))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())
