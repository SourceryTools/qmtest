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
"""Checkbox Widget tests

$Id: test_checkboxwidget.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest
import transaction
from persistent import Persistent

import zope.security.checker
from zope.interface import Interface, implements
from zope.schema import Bool
from zope.traversing.api import traverse

from zope.app.form.browser import CheckBoxWidget
from zope.app.form.browser.ftests.support import *
from zope.app.testing.functional import BrowserTestCase

class IBoolTest(Interface):

    b1 = Bool(
        required=True)

    b2 = Bool(
        required=False)

class BoolTest(Persistent):

    implements(IBoolTest)

    def __init__(self):
        self.b1 = True
        self.b2 = False

class Test(BrowserTestCase):


    def setUp(self):
        BrowserTestCase.setUp(self)
        registerEditForm(IBoolTest)
        defineSecurity(BoolTest, IBoolTest)

    def test_display_editform(self):
        self.getRootFolder()['test'] = BoolTest()
        transaction.commit()

        # display edit view
        response = self.publish('/test/edit.html')
        self.assertEqual(response.getStatus(), 200)

        # b1 and b2 should be displayed in checkbox input fields
        self.assert_(patternExists(
            '<input .* checked="checked".* name="field.b1".* ' \
            'type="checkbox".* />',
            response.getBody()))
        self.assert_(patternExists(
            '<input .* name="field.b2".* type="checkbox".* />',
            response.getBody()))
        # confirm that b2 is *not* checked
        self.assert_(not patternExists(
            '<input .* checked="checked".* name="field.b2".* ' \
            'type="checkbox".* />',
            response.getBody()))


    def test_submit_editform(self):
        self.getRootFolder()['test'] = BoolTest()
        transaction.commit()

        # submit edit view
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.b1' : '',
            'field.b2' : 'on' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(updatedMsgExists(response.getBody()))

        # check new values in object
        object = traverse(self.getRootFolder(), 'test')
        self.assertEqual(object.b1, False)
        self.assertEqual(object.b2, True)


    def test_unexpected_value(self):
        object = BoolTest()
        object.b1 = True
        object.b2 = True
        self.getRootFolder()['test'] = object
        transaction.commit()

        # submit invalud type for text line
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.b1' : 'true',
            'field.b2' : 'foo' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(updatedMsgExists(response.getBody()))

        # values other than 'on' should be treated as False
        object = traverse(self.getRootFolder(), 'test')
        self.assertEqual(object.b1, False)
        self.assertEqual(object.b2, False)


    def test_missing_value(self):
        # Note: checkbox widget doesn't support a missing value. This
        # test confirms that one cannot set a Bool field to None.

        self.getRootFolder()['test'] = BoolTest()
        transaction.commit()

        # confirm default value of b1 is True
        object = traverse(self.getRootFolder(), 'test')
        self.assertEqual(object.b1, True)

        # submit missing for b1
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.b1' : CheckBoxWidget._missing })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(updatedMsgExists(response.getBody()))

        # confirm b1 is not missing
        object = traverse(self.getRootFolder(), 'test')
        self.assert_(object.b1 != Bool.missing_value)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Test))
    return suite

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')


