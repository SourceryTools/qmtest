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
"""TextWidget Tests

$Id: test_textwidget.py 68730 2006-06-18 05:35:59Z ctheune $
"""
import unittest
import transaction
from persistent import Persistent

import zope.security.checker
from zope.interface import Interface, implements
from zope.schema import TextLine, Choice
from zope.traversing.api import traverse

from zope.app.form.browser.ftests.support import *
from zope.app.testing.functional import BrowserTestCase

class ITextLineTest(Interface):

    s2 = TextLine(
        required=False,
        missing_value=u'')

    s3 = Choice(
        required=False,
        values=(u'Bob', u'is', u'Your', u'Uncle'))

    s1 = TextLine(
        required=True,
        min_length=2,
        max_length=10)


class TextLineTest(Persistent):

    implements(ITextLineTest)

    def __init__(self):
        self.s1 = ''
        self.s2 = u'foo'
        self.s3 = None


class Test(BrowserTestCase):


    def setUp(self):
        BrowserTestCase.setUp(self)
        registerEditForm(ITextLineTest)
        defineSecurity(TextLineTest, ITextLineTest)

    def test_display_editform(self):
        self.getRootFolder()['test'] = TextLineTest()
        transaction.commit()

        # display edit view
        response = self.publish('/test/edit.html')
        self.assertEqual(response.getStatus(), 200)

        # s1 and s2 should be displayed in text fields
        self.assert_(patternExists(
            '<input .* name="field.s1".* value="".*>', response.getBody()))
        self.assert_(patternExists(
            '<input .* name="field.s2".* value="foo".*>', response.getBody()))

        # s3 should be in a dropdown
        self.assert_(patternExists(
            '<select .*name="field.s3".*>', response.getBody()))
        self.assert_(patternExists(
            '<option selected="selected" value="">.*</option>', response.getBody()))


    def test_submit_editform(self):
        self.getRootFolder()['test'] = TextLineTest()
        transaction.commit()

        # submit edit view
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.s1' : u'foo',
            'field.s2' : u'bar',
            'field.s3' : u'Uncle' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(updatedMsgExists(response.getBody()))

        # check new values in object
        object = traverse(self.getRootFolder(), 'test')
        self.assertEqual(object.s1, u'foo')
        self.assertEqual(object.s2, u'bar')
        self.assertEqual(object.s3, u'Uncle')


    def test_invalid_type(self):
        """Tests text widget's handling of invalid unicode input.
        
        The text widget will succeed in converting any form input into
        unicode.
        """
        self.getRootFolder()['test'] = TextLineTest()
        transaction.commit()

        # submit invalud type for text line
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.s1' : '' }) # not unicode (but automatically converted to it.
        self.assertEqual(response.getStatus(), 200)

        # We don't have a invalid field value
        #since we convert the value to unicode
        self.assert_(not validationErrorExists(
            's1', 'Object is of wrong type.', response.getBody()))


    def test_missing_value(self):
        self.getRootFolder()['test'] = TextLineTest()
        transaction.commit()

        # submit missing values for s2 and s3
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.s1' : u'foo',
            'field.s2' : u'',
            'field.s3' : u'' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(updatedMsgExists(response.getBody()))

        # check new values in object
        object = traverse(self.getRootFolder(), 'test')
        self.assertEqual(object.s1, u'foo')
        self.assertEqual(object.s2, u'')   # default missing_value
        self.assertEqual(object.s3, None)  # None is s3's missing_value


    def test_required_validation(self):
        self.getRootFolder()['test'] = TextLineTest()
        transaction.commit()

        # submit missing values for required field s1
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.s1' : u'',
            'field.s2' : u'',
            'field.s3' : u'' })
        self.assertEqual(response.getStatus(), 200)

        # confirm error msgs
        self.assert_(missingInputErrorExists('s1', response.getBody()))
        self.assert_(not missingInputErrorExists('s2', response.getBody()))
        self.assert_(not missingInputErrorExists('s3', response.getBody()))


    def test_invalid_value(self):
        self.getRootFolder()['test'] = TextLineTest()
        transaction.commit()

        # submit a value for s3 that isn't allowed
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.s3' : u'Bob is *Not* My Uncle' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(invalidValueErrorExists('s3', response.getBody()))


    def test_length_validation(self):
        self.getRootFolder()['test'] = TextLineTest()
        transaction.commit()

        # submit value for s1 that is too short
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.s1' : u'a' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(validationErrorExists(
            's1', 'Value is too short', response.getBody()))

        # submit value for s1 that is too long
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.s1' : u'12345678901' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(validationErrorExists(
            's1', 'Value is too long', response.getBody()))


    def test_omitted_value(self):
        self.getRootFolder()['test'] = TextLineTest()
        transaction.commit()

        # confirm default values
        object = traverse(self.getRootFolder(), 'test')
        self.assertEqual(object.s1, '')
        self.assertEqual(object.s2, u'foo')
        self.assert_(object.s3 is None)

        # submit change with only s2 present -- note that required
        # field s1 is omitted, which should not cause a validation error
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.s2' : u'bar' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(updatedMsgExists(response.getBody()))

        # check new value in object
        object = traverse(self.getRootFolder(), 'test')
        self.assertEqual(object.s1, '')
        self.assertEqual(object.s2, u'bar')
        self.assert_(object.s3 is None)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Test))
    return suite

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

