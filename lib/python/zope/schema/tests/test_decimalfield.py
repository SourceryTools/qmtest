##############################################################################
#
# Copyright (c) 2001, 2002, 2006 Zope Corporation and Contributors.
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
"""Decimal field tests

$Id: test_decimalfield.py 70794 2006-10-19 04:29:42Z baijum $
"""
import decimal
from unittest import main, makeSuite
from zope.schema import Decimal
from zope.schema.interfaces import RequiredMissing, InvalidValue
from zope.schema.interfaces import TooSmall, TooBig
from zope.schema.tests.test_field import FieldTestBase

class DecimalTest(FieldTestBase):
    """Test the Decimal Field."""

    _Field_Factory = Decimal

    def testValidate(self):
        field = self._Field_Factory(title=u'Decimal field', description=u'',
                                    readonly=False, required=False)
        field.validate(None)
        field.validate(decimal.Decimal("10.0"))
        field.validate(decimal.Decimal("0.93"))
        field.validate(decimal.Decimal("1000.0003"))

    def testValidateRequired(self):
        field = self._Field_Factory(title=u'Decimal field', description=u'',
                                    readonly=False, required=True)
        field.validate(decimal.Decimal("10.0"))
        field.validate(decimal.Decimal("0.93"))
        field.validate(decimal.Decimal("1000.0003"))

        self.assertRaises(RequiredMissing, field.validate, None)

    def testValidateMin(self):
        field = self._Field_Factory(title=u'Decimal field', description=u'',
                                    readonly=False, required=False,
                                    min=decimal.Decimal("10.5"))
        field.validate(None)
        field.validate(decimal.Decimal("10.6"))
        field.validate(decimal.Decimal("20.2"))

        self.assertRaises(TooSmall, field.validate, decimal.Decimal("-9.0"))
        self.assertRaises(TooSmall, field.validate, decimal.Decimal("10.4"))

    def testValidateMax(self):
        field = self._Field_Factory(title=u'Decimal field', description=u'',
                                    readonly=False, required=False,
                                    max=decimal.Decimal("10.5"))
        field.validate(None)
        field.validate(decimal.Decimal("5.3"))
        field.validate(decimal.Decimal("-9.1"))

        self.assertRaises(TooBig, field.validate, decimal.Decimal("10.51"))
        self.assertRaises(TooBig, field.validate, decimal.Decimal("20.7"))

    def testValidateMinAndMax(self):
        field = self._Field_Factory(title=u'Decimal field', description=u'',
                                    readonly=False, required=False,
                                    min=decimal.Decimal("-0.6"),
                                    max=decimal.Decimal("10.1"))
        field.validate(None)
        field.validate(decimal.Decimal("0.0"))
        field.validate(decimal.Decimal("-0.03"))
        field.validate(decimal.Decimal("10.0001"))

        self.assertRaises(TooSmall, field.validate, decimal.Decimal("-10.0"))
        self.assertRaises(TooSmall, field.validate, decimal.Decimal("-1.6"))
        self.assertRaises(TooBig, field.validate, decimal.Decimal("11.45"))
        self.assertRaises(TooBig, field.validate, decimal.Decimal("20.02"))


def test_suite():
    suite = makeSuite(DecimalTest)
    return suite

if __name__ == '__main__':
    main(defaultTest='test_suite')
