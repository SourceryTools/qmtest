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

$Id: testdt_sqltest.py 25177 2004-06-02 13:17:31Z jim $
"""

import unittest
from zope.app.sqlscript.dtml import SQLDTML, comparison_operators

class TestDT_SQLTest(unittest.TestCase):

    doc_class = SQLDTML


    def testSimpleUse(self):
        html = self.doc_class("<dtml-sqltest column type=nb>")
        result = "column = 'name'"

        self.assertEqual(html(column='name'), result)


    def testIntType(self):
        html = self.doc_class("<dtml-sqltest column type=int>")
        result = "column = 3"

        self.assertEqual(html(column=3), result)
        self.assertEqual(html(column='3'), result)
        self.assertEqual(html(column=3.1), result)


    def testFloatType(self):
        html = self.doc_class("<dtml-sqltest column type=float>")
        result = "column = 3.1"

        self.assertEqual(html(column=3), "column = 3.0")
        self.assertEqual(html(column='3'), "column = 3")
        self.assertEqual(html(column='3.1'), result)
        self.assertEqual(html(column=3.1), result)
        self.assertEqual(html(column=0.0), "column = 0.0")

    def testStringTypeAndEscaping(self):
        html = self.doc_class("<dtml-sqltest column type=nb>")

        self.assertEqual(html(column='name'), "column = 'name'")
        self.assertEqual(html(column='Let\'s do it'),
                         "column = 'Let''s do it'")
        # Acid test :)
        self.assertEqual(html(column="\'\'"), "column = ''''''")


    def testOperators(self):
        for item in comparison_operators.items():
            html = self.doc_class(
                "<dtml-sqltest column type=nb op=%s>" %item[0])
            result = "column %s 'name'" %item[1]

            self.assertEqual(html(column='name'), result)


    def testCustomColumnName(self):
        html = self.doc_class(
            "<dtml-sqltest col column=col type=nb optional>")
        result1 = "col = 'name'"
        result2 = ""

        self.assertEqual(html(col='name'), result1)
        self.assertEqual(html(col=''), result2)
        self.assertEqual(html(), result2)


    def testOptional(self):
        html = self.doc_class("<dtml-sqltest column type=nb optional>")
        result1 = "column = 'name'"
        result2 = ""

        self.assertEqual(html(column='name'), result1)
        self.assertEqual(html(column=''), result2)
        self.assertEqual(html(), result2)


    def testMultiple(self):
        html = self.doc_class(
            "<dtml-sqltest column type=nb optional multiple>")
        result1 = "column in ('name1', 'name2')"
        result2 = ""

        self.assertEqual(html(column=('name1', 'name2')), result1)
        self.assertEqual(html(column=()), result2)
        self.assertEqual(html(), result2)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDT_SQLTest))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())
