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

$Id: testdt_sqlgroup.py 25177 2004-06-02 13:17:31Z jim $
"""

import unittest
from zope.app.sqlscript.dtml import SQLDTML

class TestDT_SQLGroup(unittest.TestCase):

    doc_class = SQLDTML


    def testSimpleUse(self):
        html = self.doc_class("""
          <dtml-sqlgroup>
            <dtml-sqlvar column type=nb>
          </dtml-sqlgroup>""")
        result = "'name'"

        self.assertEqual(html(column='name').strip(), result)


    def testComplexUse(self):
        html = self.doc_class("""
          <dtml-sqlgroup required>
            <dtml-sqlgroup>
              <dtml-sqltest name column=nick_name type=nb multiple optional>
            <dtml-or>
              <dtml-sqltest name column=first_name type=nb multiple optional>
            </dtml-sqlgroup>
          <dtml-and>
            <dtml-sqltest home_town type=nb optional>
          <dtml-and>
            <dtml-if minimum_age>
               age >= <dtml-sqlvar minimum_age type=int>
            </dtml-if>
          <dtml-and>
            <dtml-if maximum_age>
               age <= <dtml-sqlvar maximum_age type=int>
            </dtml-if>
          </dtml-sqlgroup>
        """)

        result = """
((nick_name = 'stephan'
 or first_name = 'stephan'
)
 and home_town = 'berlin'
 and age >= 16
 and age <= 21
)"""
        self.assertEqual(html(name="stephan", home_town="berlin",
                              minimum_age=16, maximum_age="21").strip(),
                         result.strip())



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDT_SQLGroup))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())
