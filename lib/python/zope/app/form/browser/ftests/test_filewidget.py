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
"""File Widget Tests

$Id: test_filewidget.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest
import transaction
from StringIO import StringIO
from persistent import Persistent

import zope.security.checker
from zope.interface import Interface, implements
from zope.schema.interfaces import IField
from zope.schema import Field
from zope.traversing.api import traverse

from zope.app.form.browser.textwidgets import FileWidget
from zope.app.form.browser.ftests.support import *
from zope.app.testing.functional import BrowserTestCase
from zope.app.form.interfaces import IInputWidget

class IFileField(IField):
    """Field for representing a file that can be edited by FileWidget."""


class FileField(Field):

    implements(IFileField)

class IFileTest(Interface):

    f1 = FileField(required=True)
    f2 = FileField(required=False)

class FileTest(Persistent):

    implements(IFileTest)

    def __init__(self):
        self.f1 = None
        self.f2 = 'foo'


class SampleTextFile(StringIO):

    def __init__(self, buf, filename=''):
        StringIO.__init__(self, buf)
        self.filename = filename


class Test(BrowserTestCase):

    sampleText = "The quick brown fox\njumped over the lazy dog."
    sampleTextFile = SampleTextFile(sampleText)

    emptyFileName = 'empty.txt'
    emptyFile = SampleTextFile('', emptyFileName)

    def setUp(self):
        BrowserTestCase.setUp(self)
        defineWidgetView(IFileField, FileWidget, IInputWidget)
        registerEditForm(IFileTest)
        defineSecurity(FileTest, IFileTest)

    def test_display_editform(self):
        self.getRootFolder()['test'] = FileTest()
        transaction.commit()

        # display edit view
        response = self.publish('/test/edit.html')
        self.assertEqual(response.getStatus(), 200)

        # field should be displayed in a file input element
        self.assert_(patternExists(
            '<input .* name="field.f1".* type="file".*>', response.getBody()))
        self.assert_(patternExists(
            '<input .* name="field.f2".* type="file".*>', response.getBody()))


    def test_submit_text(self):
        self.getRootFolder()['test'] = FileTest()
        transaction.commit()
        object = traverse(self.getRootFolder(), 'test')
        self.assert_(object.f1 is None)
        self.assertEqual(object.f2, 'foo')

        # submit a sample text file
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.f1' : self.sampleTextFile,
            'field.f2' : self.sampleTextFile,
            'field.f1.used' : '',
            'field.f2.used' : '' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(updatedMsgExists(response.getBody()))

        # check new values in object
        object = traverse(self.getRootFolder(), 'test')
        self.assertEqual(object.f1, self.sampleText)
        self.assertEqual(object.f2, self.sampleText)


    def test_invalid_value(self):
        self.getRootFolder()['test'] = FileTest()
        transaction.commit()

        # submit an invalid file value
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.f1' : 'not a file - same as missing input',
            'field.f1.used' : '',
            'field.f2.used' : '' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(validationErrorExists('f1',
            'Form input is not a file object', response.getBody()))


    def test_required_validation(self):
        self.getRootFolder()['test'] = FileTest()
        transaction.commit()

        # submit missing value for required field f1
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.f1.used' : '',
            'field.f2.used' : ''})
        self.assertEqual(response.getStatus(), 200)

        # confirm error msgs
        self.assert_(missingInputErrorExists('f1', response.getBody()))
        self.assert_(not missingInputErrorExists('f2', response.getBody()))


    def test_empty_file(self):
        self.getRootFolder()['test'] = FileTest()
        transaction.commit()

        # submit an empty text file
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.f2' : self.emptyFile,
            # 'field.f1.used' : '', # we don't let f1 know that it was rendered
            # or else it will complain (see test_required_validation) and the
            # change will not succeed.
            'field.f2.used' : ''})
        self.assertEqual(response.getStatus(), 200)
        self.assert_(updatedMsgExists(response.getBody()))

        # new value for f1 should be field.missing_value (i.e, None)
        object = traverse(self.getRootFolder(), 'test')
        self.assert_(object.f1 is None)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Test))
    return suite

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')


