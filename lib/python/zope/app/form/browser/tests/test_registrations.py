##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Test widget registrations.

$Id: test_registrations.py 37565 2005-07-29 20:46:23Z srichter $
"""
import unittest

from zope.configuration import xmlconfig
from zope.interface import implements
from zope.publisher.browser import TestRequest
from zope.testing.doctestunit import DocTestSuite

from zope.app import zapi
from zope.app.testing import setup
# import all widgets (in this case, importing * is ok, since we
# absolutely know what we're importing)
from zope.app.form.browser import *

from zope.app.form.interfaces import IDisplayWidget, IInputWidget
import zope.app.form.browser

import zope.schema as fields
from zope.schema import interfaces
from zope.schema import vocabulary

class ISampleObject(interfaces.IField):
    pass

class SampleObject(object):
    implements(ISampleObject)

class ISampleVocabulary(interfaces.IVocabularyTokenized,
                        interfaces.IVocabulary):
    pass

class SampleVocabulary(vocabulary.SimpleVocabulary):
    implements(ISampleVocabulary)

request = TestRequest()
sample = SampleObject()
vocab = SampleVocabulary([])

def setUp(test):
    setup.placelessSetUp()
    context = xmlconfig.file("tests/registerWidgets.zcml",
                             zope.app.form.browser)

class Tests(object):
    """Documents and tests widgets registration for specific field types.
    
    Standard Widgets
    ------------------------------------------------------------------------
    The relationships between field types and standard widgets are listed
    below.
    
    IField, IDisplayWidget -> DisplayWidget
        
        >>> field = fields.Field()
        >>> widget = zapi.getMultiAdapter((field, request), IDisplayWidget)
        >>> isinstance(widget, DisplayWidget)
        True
        
    ITextLine, IInputWidget -> TextWidget 
        
        >>> field = fields.TextLine()
        >>> widget = zapi.getMultiAdapter((field, request), IInputWidget)
        >>> isinstance(widget, TextWidget)
        True
        
    IText, IInputWidget -> TextAreaWidget
    
        >>> field = fields.Text()
        >>> widget = zapi.getMultiAdapter((field, request), IInputWidget)
        >>> isinstance(widget, TextAreaWidget)
        True
        
    ISourceText, IInputWidget -> TextAreaWidget
    
        >>> field = fields.SourceText()
        >>> widget = zapi.getMultiAdapter((field, request), IInputWidget)
        >>> isinstance(widget, TextAreaWidget)
        True

    IBytesLine, IInputWidget -> BytesWidget
    
        >>> field = fields.BytesLine()
        >>> widget = zapi.getMultiAdapter((field, request), IInputWidget)
        >>> isinstance(widget, BytesWidget)
        True

    IBytes, IInputWidget -> FileWidget
    
        >>> field = fields.Bytes()
        >>> widget = zapi.getMultiAdapter((field, request), IInputWidget)
        >>> isinstance(widget, FileWidget)
        True
        		
    IASCIILine, IInputWidget -> ASCIIWidget
    
        >>> field = fields.ASCIILine()
        >>> widget = zapi.getMultiAdapter((field, request), IInputWidget)
        >>> isinstance(widget, ASCIIWidget)
        True
        
    IASCII, IInputWidget -> ASCIIAreaWidget
    
        >>> field = fields.ASCII()
        >>> widget = zapi.getMultiAdapter((field, request), IInputWidget)
        >>> isinstance(widget, ASCIIAreaWidget)
        True
        
    IInt, IInputWidget -> IntWidget
    
        >>> field = fields.Int()
        >>> widget = zapi.getMultiAdapter((field, request), IInputWidget)
        >>> isinstance(widget, IntWidget)
        True
        
    IFloat, IInputWidget -> FloatWidget
    
        >>> field = fields.Float()
        >>> widget = zapi.getMultiAdapter((field, request), IInputWidget)
        >>> isinstance(widget, FloatWidget)
        True
        
    IDatetime, IInputWidget -> DatetimeWidget
    
        >>> field = fields.Datetime()
        >>> widget = zapi.getMultiAdapter((field, request), IInputWidget)
        >>> isinstance(widget, DatetimeWidget)
        True
        
    IDate, IInputWidget -> DateWidget
    
        >>> field = fields.Date()
        >>> widget = zapi.getMultiAdapter((field, request), IInputWidget)
        >>> isinstance(widget, DateWidget)
        True
        
    IBool, IInputWidget -> CheckBoxWidget
    
        >>> field = fields.Bool()
        >>> widget = zapi.getMultiAdapter((field, request), IInputWidget)
        >>> isinstance(widget, CheckBoxWidget)
        True
        
    ITuple, IInputWidget -> TupleSequenceWidget
    
        >>> field = fields.Tuple(value_type=fields.Int())
        >>> widget = zapi.getMultiAdapter((field, request), IInputWidget)
        >>> isinstance(widget, TupleSequenceWidget)
        True

    IList, IInputWidget -> ListSequenceWidget
    
        >>> field = fields.List(value_type=fields.Int())
        >>> widget = zapi.getMultiAdapter((field, request), IInputWidget)
        >>> isinstance(widget, ListSequenceWidget)
        True

    IPassword, IInputWidget -> PasswordWidget
    
        >>> field = fields.Password()
        >>> widget = zapi.getMultiAdapter((field, request), IInputWidget)
        >>> isinstance(widget, PasswordWidget)
        True

    IChoice, IDisplayWidget -> ItemDisplayWidget
    
        >>> field = fields.Choice(vocabulary=vocab)
        >>> field = field.bind(sample)
        >>> widget = zapi.getMultiAdapter((field, request), IDisplayWidget)
        >>> isinstance(widget, ItemDisplayWidget)
        True
                
    IChoice, IInputWidget -> DropdownWidget
    
        >>> field = fields.Choice(vocabulary=vocab)
        >>> field = field.bind(sample)
        >>> widget = zapi.getMultiAdapter((field, request), IInputWidget)
        >>> isinstance(widget, DropdownWidget)
        True

    IList with IChoice value_type, IDisplayWidget -> ItemsMultiDisplayWidget
    
        >>> field = fields.List(value_type=fields.Choice(vocabulary=vocab))
        >>> field = field.bind(sample)
        >>> widget = zapi.getMultiAdapter((field, request), IDisplayWidget)
        >>> isinstance(widget, ItemsMultiDisplayWidget)
        True
                
    IList with IChoice value_type, IInputWidget -> MultiSelectWidget
    
        >>> field = fields.List(value_type=fields.Choice(vocabulary=vocab))
        >>> field = field.bind(sample)
        >>> widget = zapi.getMultiAdapter((field, request), IInputWidget)
        >>> isinstance(widget, OrderedMultiSelectWidget)
        True
    """

def test_suite():    
    return DocTestSuite(setUp=setUp, tearDown=setup.placelessTearDown)

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
