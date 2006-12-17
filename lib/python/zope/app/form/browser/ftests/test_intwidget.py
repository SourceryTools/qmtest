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
"""Int Widget Functional Tests

$Id: test_intwidget.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest
import transaction
from persistent import Persistent

import zope.security.checker
from zope.interface import Interface, implements
from zope.schema import Int, Choice
from zope.traversing.api import traverse

from zope.app.testing.functional import BrowserTestCase
from zope.app.form.browser.ftests.support import *

class IIntTest(Interface):

    i2 = Int(
        required=False)

    i3 = Choice(
        required=False,
        values=(0, 1, 2, 3, 5, 7, 11),
        missing_value=0)

    i1 = Int(
        required=True,
        min=1,
        max=10)


class IIntTest2(Interface):
    """Used to test an unusual care where missing_value is -1 and
    not in allowed_values."""

    i1 = Choice(
        required=False,
        missing_value=-1,
        values=(10, 20, 30))


class IntTest(Persistent):

    implements(IIntTest)

    def __init__(self):
        self.i1 = None
        self.i2 = 1
        self.i3 = 2


class IntTest2(Persistent):

    implements(IIntTest2)

    def __init__(self):
        self.i1 = 10


class Test(BrowserTestCase):

    def setUp(self):
        BrowserTestCase.setUp(self)
        registerEditForm(IIntTest)
        registerEditForm(IIntTest2)
        defineSecurity(IntTest, IIntTest)
        defineSecurity(IntTest2, IIntTest2)

    def test_display_editform(self):
        self.getRootFolder()['test'] = IntTest()
        transaction.commit()

        # display edit view
        response = self.publish('/test/edit.html')
        self.assertEqual(response.getStatus(), 200)

        # i1 and i2 should be displayed in text fields
        self.assert_(patternExists(
            '<input .* name="field.i1".* value="".*>', response.getBody()))
        self.assert_(patternExists(
            '<input .* name="field.i2".* value="1".*>', response.getBody()))

        # i3 should be in a dropdown
        self.assert_(patternExists(
            '<select .*name="field.i3".*>', response.getBody()))
        self.assert_(patternExists(
            '<option selected="selected" value="2">2</option>',
            response.getBody()))


    def test_submit_editform(self):
        self.getRootFolder()['test'] = IntTest()
        transaction.commit()

        # submit edit view
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.i1' : '1',
            'field.i2' : '2',
            'field.i3' : '3' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(updatedMsgExists(response.getBody()))

        # check new values in object
        object = traverse(self.getRootFolder(), 'test')
        self.assertEqual(object.i1, 1)
        self.assertEqual(object.i2, 2)
        self.assertEqual(object.i3, 3)


    def test_missing_value(self):
        self.getRootFolder()['test'] = IntTest()
        transaction.commit()

        # submit missing values for i2 and i3
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.i1' : '1',
            'field.i2' : '',
            'field.i3-empty-marker' : '' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(updatedMsgExists(response.getBody()))

        # check new values in object
        object = traverse(self.getRootFolder(), 'test')
        self.assertEqual(object.i1, 1)
        self.assertEqual(object.i2, None) # None is default missing_value
        self.assertEqual(object.i3, 0)  # 0 is from i3.missing_value=0


    def test_alternative_missing_value(self):
        """Tests the addition of an empty value at the top of the dropdown
        that, when selected, updates the field with field.missing_value.
        """

        self.getRootFolder()['test'] = IntTest2() # note alt. class
        transaction.commit()

        # display edit form
        response = self.publish('/test/edit.html')
        self.assertEqual(response.getStatus(), 200)

        # confirm that i1 is has a blank item at top with value=""
        self.assert_(patternExists(
            '<select id="field.i1" name="field.i1" .*>', response.getBody()))
        self.assert_(patternExists(
            '<option value="">.*</option>', response.getBody()))
        self.assert_(patternExists(
            '<option selected="selected" value="10">10</option>',
            response.getBody()))

        # submit form as if top item is selected
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.i1-empty-marker' : '1'})

        self.assertEqual(response.getStatus(), 200)
        self.assert_(updatedMsgExists(response.getBody()))

        # confirm new value is -1 -- i1.missing_value
        object = traverse(self.getRootFolder(), 'test')
        self.assertEqual(object.i1, -1)


    def test_required_validation(self):
        self.getRootFolder()['test'] = IntTest()
        transaction.commit()

        # submit missing values for required field i1
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.i1' : '',
            'field.i2' : '',
            'field.i3' : '' })
        self.assertEqual(response.getStatus(), 200)

        # confirm error msgs
        self.assert_(missingInputErrorExists('i1', response.getBody()))
        self.assert_(not missingInputErrorExists('i2', response.getBody()))
        self.assert_(not missingInputErrorExists('i3', response.getBody()))


    def test_invalid_allowed_value(self):
        self.getRootFolder()['test'] = IntTest()
        transaction.commit()

        # submit a value for i3 that isn't allowed
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.i3' : '12' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(invalidValueErrorExists('i3', response.getBody()))


    def test_min_max_validation(self):
        self.getRootFolder()['test'] = IntTest()
        transaction.commit()

        # submit value for i1 that is too low
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.i1' : '-1' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(validationErrorExists('i1', 'Value is too small',
            response.getBody()))

        # submit value for i1 that is too high
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.i1' : '11' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(validationErrorExists('i1', 'Value is too big',
            response.getBody()))


    def test_omitted_value(self):
        self.getRootFolder()['test'] = IntTest()
        transaction.commit()

        # confirm default values
        object = traverse(self.getRootFolder(), 'test')
        self.assert_(object.i1 is None)
        self.assertEqual(object.i2, 1)
        self.assertEqual(object.i3, 2)

        # submit change with only i2 present -- note that required
        # field i1 is omitted, which should not cause a validation error
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.i2' : '' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(updatedMsgExists(response.getBody()))

        # check new value in object
        object = traverse(self.getRootFolder(), 'test')
        self.assert_(object.i1 is None)
        self.assert_(object.i2 is None)
        self.assertEqual(object.i3, 2)


    def test_conversion(self):
        self.getRootFolder()['test'] = IntTest()
        transaction.commit()

        # submit value for i1 that cannot be convert to an int
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.i1' : 'foo' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(validationErrorExists('i1', 'Invalid integer data',
                                           response.getBody()))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Test))
    return suite

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
