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
"""DateTime Widget Functional Tests

$Id: test_datetimewidget.py 68937 2006-07-01 17:18:56Z hdima $
"""
import unittest
import re
import transaction
from persistent import Persistent
from datetime import datetime

import zope.security.checker
from zope.datetime import parseDatetimetz, tzinfo
from zope.interface import Interface, implements
from zope.schema import Datetime, Choice
from zope.traversing.api import traverse

from zope.app.form.browser.ftests.support import *
from zope.app.testing.functional import BrowserTestCase


class IDatetimeTest(Interface):

    d2 = Datetime(
        required=False)

    d3 = Choice(
        required=False,
        values=(
            datetime(2003, 9, 15, tzinfo=tzinfo(0)),
            datetime(2003, 10, 15, tzinfo=tzinfo(0))),
        missing_value=datetime(2000, 1, 1, tzinfo=tzinfo(0)))

    d1 = Datetime(
        required=True,
        min=datetime(2003, 1, 1, tzinfo=tzinfo(0)),
        max=datetime(2020, 12, 31, tzinfo=tzinfo(0)))

class DatetimeTest(Persistent):

    implements(IDatetimeTest)

    def __init__(self):
        self.d1 = datetime(2003, 4, 6, tzinfo=tzinfo(0))
        self.d2 = datetime(2003, 8, 6, tzinfo=tzinfo(0))
        self.d3 = None

class Test(BrowserTestCase):

    def setUp(self):
        BrowserTestCase.setUp(self)
        registerEditForm(IDatetimeTest)
        defineSecurity(DatetimeTest, IDatetimeTest)

    def getDateForField(self, field, source):
        """Returns a datetime object for the specified field in source.

        Returns None if the field value cannot be converted to date.
        """

        # look in input element first
        pattern = '<input .* name="field.%s".* value="(.*)".*>' % field
        m = re.search(pattern, source)
        if m is None:
            # look in a select element
            pattern = '<select .* name="field.%s".*>.*' \
                '<option value="(.*)" selected>*.</select>' % field
            m = re.search(pattern, source, re.DOTALL)
            if m is None:
                return None
        return parseDatetimetz(m.group(1))

    def test_display_editform(self):
        self.getRootFolder()['test'] = DatetimeTest()
        transaction.commit()
        object = traverse(self.getRootFolder(), 'test')

        # display edit view
        response = self.publish('/test/edit.html',
            env={"HTTP_ACCEPT_LANGUAGE": "ru"})
        self.assertEqual(response.getStatus(), 200)

        # confirm date values in form with actual values
        self.assertEqual(self.getDateForField('d1', response.getBody()),
            object.d1)
        self.assertEqual(self.getDateForField('d2', response.getBody()),
            object.d2)
        self.assert_(self.getDateForField('d3', response.getBody()) is None)


    def test_submit_editform(self):
        self.getRootFolder()['test'] = DatetimeTest()
        transaction.commit()

        # submit edit view
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.d1' : u'2003-02-01 00:00:00+00:00',
            'field.d2' : u'2003-02-02 00:00:00+00:00',
            'field.d3' : u'2003-10-15 00:00:00+00:00' },
            env={"HTTP_ACCEPT_LANGUAGE": "en"})
        self.assertEqual(response.getStatus(), 200)
        self.assert_(updatedMsgExists(response.getBody()))

        # check new values in object
        object = traverse(self.getRootFolder(), 'test')

        self.assertEqual(object.d1, datetime(2003, 2, 1, tzinfo=tzinfo(0)))
        self.assertEqual(object.d2, datetime(2003, 2, 2, tzinfo=tzinfo(0)))
        self.assertEqual(object.d3, datetime(2003, 10, 15, tzinfo=tzinfo(0)))


    def test_missing_value(self):
        self.getRootFolder()['test'] = DatetimeTest()
        transaction.commit()

        # submit missing values for d2 and d3
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.d2' : '',
            'field.d3-empty-marker' : '' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(updatedMsgExists(response.getBody()))

        # check new values in object
        object = traverse(self.getRootFolder(), 'test')
        self.assert_(object.d2 is None) # default missing_value for dates
        # 2000-1-1 is missing_value for d3
        self.assertEqual(object.d3, datetime(2000, 1, 1, tzinfo=tzinfo(0)))


    def test_required_validation(self):
        self.getRootFolder()['test'] = DatetimeTest()
        transaction.commit()

        # submit missing values for required field d1
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.d1' : '',
            'field.d2' : '',
            'field.d3' : '' })
        self.assertEqual(response.getStatus(), 200)

        # confirm error msgs
        self.assert_(missingInputErrorExists('d1', response.getBody()))
        self.assert_(not missingInputErrorExists('d2', response.getBody()))
        self.assert_(not missingInputErrorExists('d3', response.getBody()))


    def test_invalid_value(self):
        self.getRootFolder()['test'] = DatetimeTest()
        transaction.commit()

        # submit a value for d3 that isn't allowed
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.d3' : u'2003-02-01 12:00:00+00:00'})
        self.assertEqual(response.getStatus(), 200)
        self.assert_(invalidValueErrorExists('d3', response.getBody()))


    def test_min_max_validation(self):
        self.getRootFolder()['test'] = DatetimeTest()
        transaction.commit()

        # submit value for d1 that is too low
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.d1' : u'2002-12-31 12:00:00+00:00'},
            env={"HTTP_ACCEPT_LANGUAGE": "en"})
        self.assertEqual(response.getStatus(), 200)
        self.assert_(validationErrorExists('d1', 'Value is too small',
            response.getBody()))

        # submit value for i1 that is too high
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.d1' : u'2021-12-01 12:00:00+00:00'},
            env={"HTTP_ACCEPT_LANGUAGE": "en"})
        self.assertEqual(response.getStatus(), 200)
        self.assert_(validationErrorExists('d1', 'Value is too big',
            response.getBody()))


    def test_omitted_value(self):
        self.getRootFolder()['test'] = DatetimeTest()
        transaction.commit()

        # remember default values
        object = traverse(self.getRootFolder(), 'test')
        d1 = object.d1
        d2 = object.d2
        self.assert_(d2 is not None)
        d3 = object.d3

        # submit change with only d2 present -- note that required
        # field d1 is omitted, which should not cause a validation error
        response = self.publish('/test/edit.html', form={
            'UPDATE_SUBMIT' : '',
            'field.d2' : '' })
        self.assertEqual(response.getStatus(), 200)
        self.assert_(updatedMsgExists(response.getBody()))

        # check new value in object
        object = traverse(self.getRootFolder(), 'test')
        self.assertEqual(object.d1, d1)
        self.assert_(object.d2 is None)
        self.assertEqual(object.d3, d3)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Test))
    return suite

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
