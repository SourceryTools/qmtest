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

$Id: testdt_in.py 25177 2004-06-02 13:17:31Z jim $
"""

import unittest
from zope.documenttemplate import String
from zope.documenttemplate.tests.dtmltestbase import DTMLTestBase, dict, ObjectStub

class TestDT_In(DTMLTestBase):


    def testMapping(self):
        data = (
            dict(name=u'jim', age=39),
            dict(name=u'kak', age=29),
            dict(name=u'will', age=8),
            dict(name=u'andrew', age=5),
            dict(name=u'chessie',age=2),
            )

        html=u"""
<dtml-in data mapping>
   <dtml-var name>, <dtml-var age>
</dtml-in>
"""
        expected = u"""
   jim, 39
   kak, 29
   will, 8
   andrew, 5
   chessie, 2
"""
        result = self.doc_class(html)(data=data)
        self.assertEqual(result, expected)


    def testObjectSequence(self):
        seq = (ObjectStub(name=1), ObjectStub(name=2), ObjectStub(name=3))
        html = u"""
<dtml-in seq>
   <dtml-var name>
</dtml-in>
"""
        expected = """
   1
   2
   3
"""
        result = self.doc_class(html)(seq=seq)
        self.assertEqual(result, expected)


    def testSequenceNamespace(self):
        ns = {'prop_ids': ('name', 'id'), 'name': 'good', 'id': 'times'}
        html = u""":<dtml-in prop_ids><dtml-var sequence-item>=<dtml-var
        expr="_[_['sequence-item']]">:</dtml-in>"""

        result = self.doc_class(html)(None, ns)
        expected = ":name=good:id=times:"

        self.assertEqual(result, expected)


    def testElse(self):
        seq = (ObjectStub(name=1), ObjectStub(name=2), ObjectStub(name=3))
        html = u"""
<dtml-in data mapping>
<dtml-var name>, <dtml-var age>
<dtml-else>
<dtml-in seq>
<dtml-var name>
</dtml-in>
</dtml-in>
"""
        expected = u"""
1
2
3
"""
        result = self.doc_class(html)(seq=seq, data={})
        self.assertEqual(result, expected)


    def testStringSyntax(self):
        data = (
            dict(name=u'jim', age=39),
            dict(name=u'kak', age=29),
            dict(name=u'will', age=8),
            dict(name=u'andrew', age=5),
            dict(name=u'chessie',age=2),
            )
        s = u"""
%(in data mapping)[
   %(name)s, %(age)s
%(in)]
"""
        expected = u"""
   jim, 39
   kak, 29
   will, 8
   andrew, 5
   chessie, 2
"""
        result = String(s)(data=data)
        self.assertEqual(result, expected)



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDT_In))
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())
