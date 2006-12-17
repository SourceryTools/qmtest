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
"""Test the choice collections widgets (function).

$Id: test_choicecollections.py 29143 2005-02-14 22:43:16Z srichter $
"""
import unittest
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher.browser import TestRequest
from zope.schema.interfaces import IList, IChoice, IIterableVocabulary
from zope.schema import Choice, List

from zope.app import zapi
from zope.app.testing import ztapi
from zope.app.testing.placelesssetup import PlacelessSetup
from zope.app.form.interfaces import IInputWidget, IDisplayWidget
from zope.app.form.browser import CollectionDisplayWidget
from zope.app.form.browser import CollectionInputWidget
from zope.app.form.browser import ChoiceCollectionDisplayWidget
from zope.app.form.browser import ChoiceCollectionInputWidget
from zope.app.form.browser import ItemsMultiDisplayWidget, SelectWidget

class ListOfChoicesWidgetTest(PlacelessSetup, unittest.TestCase):

    def test_ListOfChoicesDisplayWidget(self):
        ztapi.provideMultiView((IList, IChoice), IBrowserRequest,
                         IDisplayWidget, '', ChoiceCollectionDisplayWidget)
        ztapi.provideMultiView((IList, IIterableVocabulary), IBrowserRequest,
                         IDisplayWidget, '', ItemsMultiDisplayWidget)
        field = List(value_type=Choice(values=[1, 2, 3]))
        bound = field.bind(object())
        widget = CollectionDisplayWidget(bound, TestRequest())
        self.assert_(isinstance(widget, ItemsMultiDisplayWidget))
        self.assertEqual(widget.context, bound)
        self.assertEqual(widget.vocabulary, bound.value_type.vocabulary)


    def test_ChoiceSequenceEditWidget(self):
        ztapi.provideMultiView((IList, IChoice), IBrowserRequest,
                               IInputWidget, '', ChoiceCollectionInputWidget)
        ztapi.provideMultiView((IList, IIterableVocabulary), IBrowserRequest,
                               IInputWidget, '', SelectWidget)
        field = List(value_type=Choice(values=[1, 2, 3]))
        bound = field.bind(object())
        widget = CollectionInputWidget(bound, TestRequest())
        self.assert_(isinstance(widget, SelectWidget))
        self.assertEqual(widget.context, bound)
        self.assertEqual(widget.vocabulary, bound.value_type.vocabulary)
        


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ListOfChoicesWidgetTest),
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
