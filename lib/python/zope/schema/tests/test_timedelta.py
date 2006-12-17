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
"""Timedelta Field tests

$Id: test_timedelta.py 29104 2005-02-10 19:08:38Z mgedmin $
"""
from unittest import main, makeSuite
from zope.schema import Timedelta
from zope.schema.interfaces import RequiredMissing, InvalidValue
from zope.schema.interfaces import TooSmall, TooBig
from zope.schema.tests.test_field import FieldTestBase
from datetime import timedelta

class TimedeltaTest(FieldTestBase):
    """Test the Timedelta Field."""

    _Field_Factory = Timedelta

    def testInterface(self):
        from zope.interface.verify import verifyObject
        from zope.schema.interfaces import ITimedelta
        verifyObject(ITimedelta, self._Field_Factory())

    def testValidate(self):
        field = self._Field_Factory(title=u'Timedelta field', description=u'',
                                    readonly=False, required=False)
        field.validate(None)
        field.validate(timedelta(minutes=15))

    def testValidateRequired(self):
        field = self._Field_Factory(title=u'Timedelta field', description=u'',
                                    readonly=False, required=True)
        field.validate(timedelta(minutes=15))

        self.assertRaises(RequiredMissing, field.validate, None)

    def testValidateMin(self):
        t1 = timedelta(hours=2)
        t2 = timedelta(hours=3)
        field = self._Field_Factory(title=u'Timedelta field', description=u'',
                                    readonly=False, required=False, min=t1)
        field.validate(None)
        field.validate(t1)
        field.validate(t2)

        self.assertRaises(TooSmall, field.validate, timedelta(hours=1))

    def testValidateMax(self):
        t1 = timedelta(minutes=1)
        t2 = timedelta(minutes=2)
        t3 = timedelta(minutes=3)
        field = self._Field_Factory(title=u'Timedelta field', description=u'',
                                    readonly=False, required=False, max=t2)
        field.validate(None)
        field.validate(t1)
        field.validate(t2)

        self.assertRaises(TooBig, field.validate, t3)

    def testValidateMinAndMax(self):
        t1 = timedelta(days=1)
        t2 = timedelta(days=2)
        t3 = timedelta(days=3)
        t4 = timedelta(days=4)
        t5 = timedelta(days=5)

        field = self._Field_Factory(title=u'Timedelta field', description=u'',
                                    readonly=False, required=False,
                                    min=t2, max=t4)
        field.validate(None)
        field.validate(t2)
        field.validate(t3)
        field.validate(t4)

        self.assertRaises(TooSmall, field.validate, t1)
        self.assertRaises(TooBig, field.validate, t5)


def test_suite():
    suite = makeSuite(TimedeltaTest)
    return suite

if __name__ == '__main__':
    main(defaultTest='test_suite')
