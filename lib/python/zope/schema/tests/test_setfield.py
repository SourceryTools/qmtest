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
"""Set field tests.

$Id: test_setfield.py 69144 2006-07-16 15:10:16Z jim $
"""
from unittest import TestSuite, main, makeSuite
import sets

from zope.interface import implements, providedBy
from zope.schema import Field, Set, Int, FrozenSet
from zope.schema.interfaces import IField
from zope.schema.interfaces import (
    ICollection, IUnorderedCollection, ISet, IFrozenSet, IAbstractSet)
from zope.schema.interfaces import NotAContainer, RequiredMissing
from zope.schema.interfaces import WrongContainedType, WrongType, NotUnique
from zope.schema.interfaces import TooShort, TooLong
from zope.schema.tests.test_field import CollectionFieldTestBase

class SetTest(CollectionFieldTestBase):
    """Test the Tuple Field."""

    _Field_Factory = Set

    def testValidate(self):
        field = Set(title=u'Set field', description=u'',
                    readonly=False, required=False)
        field.validate(None)
        field.validate(sets.Set())
        field.validate(sets.Set((1, 2)))
        field.validate(sets.Set((3,)))
        field.validate(set())
        field.validate(set((1, 2)))
        field.validate(set((3,)))

        self.assertRaises(WrongType, field.validate, [1, 2, 3])
        self.assertRaises(WrongType, field.validate, 'abc')
        self.assertRaises(WrongType, field.validate, 1)
        self.assertRaises(WrongType, field.validate, {})
        self.assertRaises(WrongType, field.validate, (1, 2, 3))
        self.assertRaises(WrongType, field.validate, frozenset((1, 2, 3)))

    def testValidateRequired(self):
        field = Set(title=u'Set field', description=u'',
                    readonly=False, required=True)
        field.validate(sets.Set())
        field.validate(sets.Set((1, 2)))
        field.validate(sets.Set((3,)))
        field.validate(set())
        field.validate(set((1, 2)))
        field.validate(set((3,)))

        self.assertRaises(RequiredMissing, field.validate, None)

    def testValidateRequiredAltMissingValue(self):
        missing = object()
        field = Set(required=True, missing_value=missing)
        field.validate(sets.Set())
        field.validate(set())

        self.assertRaises(RequiredMissing, field.validate, missing)

    def testValidateDefault(self):
        field = Set(required=True)
        field.default = None

    def testValidateDefaultAltMissingValue(self):
        missing = object()
        field = Set(required=True, missing_value=missing)
        field.default = missing

    def testValidateMinValues(self):
        field = Set(title=u'Set field', description=u'',
                    readonly=False, required=False, min_length=2)
        field.validate(None)
        field.validate(sets.Set((1, 2)))
        field.validate(sets.Set((1, 2, 3)))
        field.validate(set((1, 2)))
        field.validate(set((1, 2, 3)))

        self.assertRaises(TooShort, field.validate, sets.Set(()))
        self.assertRaises(TooShort, field.validate, sets.Set((3,)))
        self.assertRaises(TooShort, field.validate, set(()))
        self.assertRaises(TooShort, field.validate, set((3,)))

    def testValidateMaxValues(self):
        field = Set(title=u'Set field', description=u'',
                    readonly=False, required=False, max_length=2)
        field.validate(None)
        field.validate(sets.Set())
        field.validate(sets.Set((1, 2)))
        field.validate(set())
        field.validate(set((1, 2)))

        self.assertRaises(TooLong, field.validate, sets.Set((1, 2, 3, 4)))
        self.assertRaises(TooLong, field.validate, sets.Set((1, 2, 3)))
        self.assertRaises(TooLong, field.validate, set((1, 2, 3, 4)))
        self.assertRaises(TooLong, field.validate, set((1, 2, 3)))

    def testValidateMinValuesAndMaxValues(self):
        field = Set(title=u'Set field', description=u'',
                    readonly=False, required=False,
                    min_length=1, max_length=2)
        field.validate(None)
        field.validate(sets.Set((3,)))
        field.validate(sets.Set((1, 2)))
        field.validate(set((3,)))
        field.validate(set((1, 2)))

        self.assertRaises(TooShort, field.validate, sets.Set())
        self.assertRaises(TooLong, field.validate, sets.Set((1, 2, 3)))
        self.assertRaises(TooShort, field.validate, set())
        self.assertRaises(TooLong, field.validate, set((1, 2, 3)))

    def testValidateValueTypes(self):
        field = Set(title=u'Set field', description=u'',
                    readonly=False, required=False,
                    value_type=Int())
        field.validate(None)
        field.validate(sets.Set((5,)))
        field.validate(sets.Set((2, 3)))
        field.validate(set((5,)))
        field.validate(set((2, 3)))

        self.assertRaises(WrongContainedType, field.validate, sets.Set(('',)))
        self.assertRaises(WrongContainedType, 
                          field.validate, sets.Set((3.14159,)))
        self.assertRaises(WrongContainedType, field.validate, set(('',)))
        self.assertRaises(WrongContainedType, 
                          field.validate, set((3.14159,)))

    def testCorrectValueType(self):
        # TODO: We should not allow for a None value type. 
        Set(value_type=None)

        # do not allow arbitrary value types
        self.assertRaises(ValueError, Set, value_type=object())
        self.assertRaises(ValueError, Set, value_type=Field)

        # however, allow anything that implements IField
        Set(value_type=Field())
        class FakeField(object):
            implements(IField)
        Set(value_type=FakeField())
    
    def testNoUniqueArgument(self):
        self.assertRaises(TypeError, Set, unique=False)
        self.assertRaises(TypeError, Set, unique=True)
        self.failUnless(Set().unique)
    
    def testImplements(self):
        field = Set()
        self.failUnless(ISet.providedBy(field))
        self.failUnless(IUnorderedCollection.providedBy(field))
        self.failUnless(IAbstractSet.providedBy(field))
        self.failUnless(ICollection.providedBy(field))

class FrozenSetTest(CollectionFieldTestBase):
    """Test the Tuple Field."""

    _Field_Factory = FrozenSet

    def testValidate(self):
        field = FrozenSet(title=u'Set field', description=u'',
                    readonly=False, required=False)
        field.validate(None)
        field.validate(frozenset())
        field.validate(frozenset((1, 2)))
        field.validate(frozenset((3,)))

        self.assertRaises(WrongType, field.validate, [1, 2, 3])
        self.assertRaises(WrongType, field.validate, 'abc')
        self.assertRaises(WrongType, field.validate, 1)
        self.assertRaises(WrongType, field.validate, {})
        self.assertRaises(WrongType, field.validate, (1, 2, 3))
        self.assertRaises(WrongType, field.validate, set((1, 2, 3)))
        self.assertRaises(WrongType, field.validate, sets.Set((1, 2, 3)))

    def testValidateRequired(self):
        field = FrozenSet(title=u'Set field', description=u'',
                    readonly=False, required=True)
        field.validate(frozenset())
        field.validate(frozenset((1, 2)))
        field.validate(frozenset((3,)))

        self.assertRaises(RequiredMissing, field.validate, None)

    def testValidateRequiredAltMissingValue(self):
        missing = object()
        field = FrozenSet(required=True, missing_value=missing)
        field.validate(frozenset())

        self.assertRaises(RequiredMissing, field.validate, missing)

    def testValidateDefault(self):
        field = FrozenSet(required=True)
        field.default = None

    def testValidateDefaultAltMissingValue(self):
        missing = object()
        field = FrozenSet(required=True, missing_value=missing)
        field.default = missing

    def testValidateMinValues(self):
        field = FrozenSet(title=u'FrozenSet field', description=u'',
                    readonly=False, required=False, min_length=2)
        field.validate(None)
        field.validate(frozenset((1, 2)))
        field.validate(frozenset((1, 2, 3)))

        self.assertRaises(TooShort, field.validate, frozenset(()))
        self.assertRaises(TooShort, field.validate, frozenset((3,)))

    def testValidateMaxValues(self):
        field = FrozenSet(title=u'FrozenSet field', description=u'',
                          readonly=False, required=False, max_length=2)
        field.validate(None)
        field.validate(frozenset())
        field.validate(frozenset((1, 2)))

        self.assertRaises(TooLong, field.validate, frozenset((1, 2, 3, 4)))
        self.assertRaises(TooLong, field.validate, frozenset((1, 2, 3)))

    def testValidateMinValuesAndMaxValues(self):
        field = FrozenSet(title=u'FrozenSet field', description=u'',
                          readonly=False, required=False,
                          min_length=1, max_length=2)
        field.validate(None)
        field.validate(frozenset((3,)))
        field.validate(frozenset((1, 2)))

        self.assertRaises(TooShort, field.validate, frozenset())
        self.assertRaises(TooLong, field.validate, frozenset((1, 2, 3)))

    def testValidateValueTypes(self):
        field = FrozenSet(title=u'FrozenSet field', description=u'',
                          readonly=False, required=False,
                          value_type=Int())
        field.validate(None)
        field.validate(frozenset((5,)))
        field.validate(frozenset((2, 3)))

        self.assertRaises(WrongContainedType, field.validate, frozenset(('',)))
        self.assertRaises(WrongContainedType, 
                          field.validate, frozenset((3.14159,)))

    def testCorrectValueType(self):
        # TODO: We should not allow for a None value type. 
        FrozenSet(value_type=None)

        # do not allow arbitrary value types
        self.assertRaises(ValueError, FrozenSet, value_type=object())
        self.assertRaises(ValueError, FrozenSet, value_type=Field)

        # however, allow anything that implements IField
        FrozenSet(value_type=Field())
        class FakeField(object):
            implements(IField)
        FrozenSet(value_type=FakeField())
    
    def testNoUniqueArgument(self):
        self.assertRaises(TypeError, FrozenSet, unique=False)
        self.assertRaises(TypeError, FrozenSet, unique=True)
        self.failUnless(FrozenSet().unique)
    
    def testImplements(self):
        field = FrozenSet()
        self.failUnless(IFrozenSet.providedBy(field))
        self.failUnless(IAbstractSet.providedBy(field))
        self.failUnless(IUnorderedCollection.providedBy(field))
        self.failUnless(ICollection.providedBy(field))

def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(SetTest))
    suite.addTest(makeSuite(FrozenSetTest))
    return suite

if __name__ == '__main__':
    main(defaultTest='test_suite')
