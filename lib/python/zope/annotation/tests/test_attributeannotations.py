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
"""Tests the 'AttributeAnnotations' adapter. Also test the annotation
factory.

$Id: test_attributeannotations.py 66599 2006-04-06 18:50:02Z philikon $
"""
import unittest, doctest
from zope.testing import cleanup
from zope.interface import implements
from zope import component
from zope.annotation.tests.annotations import AnnotationsTest
from zope.annotation.attribute import AttributeAnnotations
from zope.annotation.interfaces import IAttributeAnnotatable

class Dummy(object):
    implements(IAttributeAnnotatable)

class AttributeAnnotationsTest(AnnotationsTest, cleanup.CleanUp):

    def setUp(self):
        self.annotations = AttributeAnnotations(Dummy())
        super(AttributeAnnotationsTest, self).setUp()


def setUp(test=None):
    cleanup.setUp()
    component.provideAdapter(AttributeAnnotations)
    
def tearDown(test=None):
    cleanup.tearDown()
    
def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(AttributeAnnotationsTest),
        doctest.DocFileSuite('../README.txt', setUp=setUp, tearDown=tearDown)
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
