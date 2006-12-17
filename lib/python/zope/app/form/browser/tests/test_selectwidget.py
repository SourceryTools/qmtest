##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Select Widget Tests

$Id: test_selectwidget.py 37976 2005-08-17 00:38:32Z poster $
"""
import unittest

from zope.schema import Choice, List
from zope.app.form.browser import SelectWidget
from zope.publisher.browser import TestRequest

choice = Choice(
    title=u"Number",
    description=u"The Number",
    values=[1, 2, 3])

sequence = List(
    title=u"Numbers",
    description=u"The Numbers",
    value_type=choice)


class SelectWidgetTest(unittest.TestCase):
    
    def _makeWidget(self, form):
        request = TestRequest(form=form)
        return SelectWidget(sequence, choice.vocabulary, request) 


select_html = '''<div>
<div class="value">
<select id="field.terms" name="field.terms" size="5" >
<option value="&lt; foo">&lt; foo</option>
<option value="bar/&gt;">bar/&gt;</option>
<option value="&amp;blah&amp;">&amp;blah&amp;</option>
</select>
</div>
<input name="field.terms-empty-marker" type="hidden" value="1" />
</div>'''

class SelectWidgetHTMLEncodingTest(unittest.TestCase):
    
    def testOptionEncoding(self):
        choice = Choice(
            title=u"Number",
            description=u"The Number",
            values=['< foo', 'bar/>', '&blah&'])

        sequence = List(
            __name__="terms",
            title=u"Numbers",
            description=u"The Numbers",
            value_type=choice)
        
        request = TestRequest()
        sequence = sequence.bind(object())
        widget = SelectWidget(sequence, choice.vocabulary, request) 
        self.assertEqual(widget(), select_html)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(SelectWidgetTest),
        unittest.makeSuite(SelectWidgetHTMLEncodingTest)
        ))

if __name__ == '__main__':
    unittest.main(defaultTest="test_suite")
