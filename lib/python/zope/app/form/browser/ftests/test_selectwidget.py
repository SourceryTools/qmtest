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
"""RadioWidget Tests

$Id: test_selectwidget.py 68730 2006-06-18 05:35:59Z ctheune $
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

class IRadioTest(Interface):

    s3 = Choice(
        required=False,
        values=(u'Bob', u'is', u'Your', u'Uncle'))

    s4 = Choice(
        required=True,
        values=(u'1', u'2', u'3'))

class RadioTest(Persistent):

    implements(IRadioTest)

    def __init__(self):
        self.s3 = None
        self.s4 = u'1'

class Test(BrowserTestCase):

    def setUp(self):
        BrowserTestCase.setUp(self)
        registerEditForm(IRadioTest)
        defineSecurity(RadioTest, IRadioTest)

    def test_display_editform(self):
        self.getRootFolder()['test'] = RadioTest()
        transaction.commit()

        test = self.getRootFolder()['test']
        test.s3 = u"Bob"

        # display edit view
        response = self.publish('/test/edit.html')
        self.assertEqual(response.getStatus(), 200)

        # S3
        self.assert_(patternExists(
            '<select .* name="field.s3".*>',
            response.getBody()))
        self.assert_(patternExists(
            '<option selected="selected" value="">',
            response.getBody()))
        self.assert_(patternExists(
            '<option value="Bob">',
            response.getBody()))
        self.assert_(patternExists(
            '<option value="is">',
            response.getBody()))
        self.assert_(patternExists(
            '<option value="Your">',
            response.getBody()))
        self.assert_(patternExists(
            '<option value="Uncle">',
            response.getBody()))

        # S4
        joined_body = "".join(response.getBody().split("\n"))
        self.failIf(patternExists(
            '<select.*name="field.s4".*>.*<option.*value="".*>',
            joined_body))
        self.assert_(patternExists(
            '<select .* name="field.s4".*>',
            response.getBody()))
        self.assert_(patternExists(
            '<option selected="selected" value="1">',
            response.getBody()))
        self.assert_(patternExists(
            '<option value="2">',
            response.getBody()))
        self.assert_(patternExists(
            '<option value="3">',
            response.getBody()))

        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT': '',
            'field.s3': u'Bob',
            'field.s4': u'2'})
        self.assert_(patternExists(
            '<option selected="selected" value="Bob">',
            response.getBody()))
        self.assert_(patternExists(
            '<option selected="selected" value="2">',
            response.getBody()))

        response = self.publish('/test/edit.html')
        self.assert_(patternExists(
            '<option selected="selected" value="Bob">',
            response.getBody()))
        self.assert_(patternExists(
            '<option selected="selected" value="2">',
            response.getBody()))

        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT': '',
            'field.s3': u''})
        self.assert_(patternExists(
            '<option selected="selected" value="">',
            response.getBody()))
        self.assert_(patternExists(
            '<option selected="selected" value="2">',
            response.getBody()))

        response = self.publish('/test/edit.html')
        self.assert_(patternExists(
            '<option selected="selected" value="">',
            response.getBody()))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Test))
    return suite

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

