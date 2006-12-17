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
"""Float Widget Functional Tests

$Id: test_floatwidget.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest
import transaction
from persistent import Persistent

import zope.security.checker
from zope.interface import Interface, implements
from zope.traversing.api import traverse

from zope.schema import Float, Choice
from zope.app.form.browser.ftests.support import *
from zope.app.testing.functional import BrowserTestCase

class IFloatTest(Interface):

    f1 = Float(
        required=False,
        min=1.1,
        max=10.1)

    f2 = Float(
        required=False)

    f3 = Choice(
        required=True,
        values=(0.0, 1.1, 2.1, 3.1, 5.1, 7.1, 11.1),
        missing_value=0)


class FloatTest(Persistent):

    implements(IFloatTest)

    def __init__(self):
        self.f1 = None
        self.f2 = 1.1
        self.f3 = 2.1


class Test(BrowserTestCase):

    def setUp(self):
        BrowserTestCase.setUp(self)
        registerEditForm(IFloatTest)
        defineSecurity(FloatTest, IFloatTest)

    def test_display_editform(self):
        self.getRootFolder()['test'] = FloatTest()
        transaction.commit()

        # display edit view
        response = self.publish('/test/edit.html')
        self.assertEqual(response.getStatus(), 200)

        # f1 and f2 should be displayed in text fields
        self.assert_(patternExists(
            '<input .* name="field.f1".* value="".*>', response.getBody()))
        self.assert_(patternExists(
            '<input .* name="field.f2".* value="1.1".*>', response.getBody()))

        # f3 should be in a dropdown
        self.assert_(patternExists(
            '<select .*name="field.f3".*>', response.getBody()))
        self.assert_(patternExists(
            '<option selected="selected" value="2.1">2.1</option>',
            response.getBody()))


    def test_submit_editform(self):
        self.getRootFolder()['test'] = FloatTest()
        transaction.commit()

        # submit edit view
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.f1' : '1.123',
            'field.f2' : '2.23456789012345',
            'field.f3' : '11.1' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(updatedMsgExists(response.getBody()))

        # check new values in object
        object = traverse(self.getRootFolder(), 'test')
        self.assertEqual(object.f1, 1.123)
        self.assertEqual(object.f2, 2.23456789012345)
        self.assertEqual(object.f3, 11.1)


    def test_missing_value(self):
        self.getRootFolder()['test'] = FloatTest()
        transaction.commit()

        # submit missing values for f2 and f3
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.f1' : '',
            'field.f2' : '',
            'field.f3' : '1.1' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(updatedMsgExists(response.getBody()))

        # check new values in object
        object = traverse(self.getRootFolder(), 'test')
        self.assertEqual(object.f1, None)
        self.assertEqual(object.f2, None) # None is default missing_value
        self.assertEqual(object.f3, 1.1)  # 0 is from f3.missing_value=0


    def test_required_validation(self):
        self.getRootFolder()['test'] = FloatTest()
        transaction.commit()

        # submit missing values for required field f1
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.f1' : '',
            'field.f2' : '',
            'field.f3' : '' })
        self.assertEqual(response.getStatus(), 200)

        # confirm error msgs
        self.assert_(not missingInputErrorExists('f1', response.getBody()))
        self.assert_(not missingInputErrorExists('f2', response.getBody()))
        self.assert_(missingInputErrorExists('f3', response.getBody()))


    def test_invalid_allowed_value(self):
        self.getRootFolder()['test'] = FloatTest()
        transaction.commit()

        # submit a value for f3 that isn't allowed
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.f3' : '10000' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(invalidValueErrorExists('f3', response.getBody()))


    def test_min_max_validation(self):
        self.getRootFolder()['test'] = FloatTest()
        transaction.commit()

        # submit value for f1 that is too low
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.f1' : '-1' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(validationErrorExists('f1', 'Value is too small',
            response.getBody()))

        # submit value for f1 that is too high
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.f1' : '1000.2' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(validationErrorExists('f1', 'Value is too big',
            response.getBody()))


    def test_omitted_value(self):
        self.getRootFolder()['test'] = FloatTest()
        transaction.commit()

        # confirm default values
        object = traverse(self.getRootFolder(), 'test')
        self.assert_(object.f1 is None)
        self.assertEqual(object.f2, 1.1)
        self.assertEqual(object.f3, 2.1)

        # submit change with only f2 present -- note that required
        # field f1 is omitted, which should not cause a validation error
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.f2' : '' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(updatedMsgExists(response.getBody()))

        # check new value in object
        object = traverse(self.getRootFolder(), 'test')
        self.assert_(object.f1 is None)
        self.assert_(object.f2 is None)
        self.assertEqual(object.f3, 2.1)


    def test_conversion(self):
        self.getRootFolder()['test'] = FloatTest()
        transaction.commit()

        # submit value for f1 that cannot be convert to an float
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.f1' : 'foo' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(validationErrorExists(
            'f1',
            'Invalid floating point data', response.getBody()))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Test))
    return suite

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

