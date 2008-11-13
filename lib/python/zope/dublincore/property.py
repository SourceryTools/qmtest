##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
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
"""
$Id: property.py 70826 2006-10-20 03:41:16Z baijum $
"""
__docformat__ = 'restructuredtext'

import re,os

from zope import schema
from zope import interface

from zope.dublincore.interfaces import IZopeDublinCore
from zope.dublincore.zopedublincore import SequenceProperty

_marker = object()


class DCProperty(object):
    """Adapt to a dublin core property
    
    Handles DC list properties as scalar property.
    """

    def __init__(self, name):
        self.__name = name

    def __get__(self, inst, klass):
        if inst is None:
            return self
        name = self.__name
        inst = IZopeDublinCore(inst)
        value = getattr(inst, name, _marker)
        if value is _marker:
            field = IZopeDublinCore[name].bind(inst)
            value = getattr(field, 'default', _marker)
            if value is _marker:
                raise AttributeError(name)
        if isinstance(value, (list, tuple)):
            value = value[0]
        return value

    def __set__(self, inst, value):
        name = self.__name
        inst = IZopeDublinCore(inst)
        field = IZopeDublinCore[name].bind(inst)
        if isinstance(field, schema.List):
            if isinstance(value, tuple):
                value = list(value)
            else:
                value = [value]
        elif isinstance(field, schema.Tuple):
            if isinstance(value, list):
                value = tuple(value)
            else:
                value = (value,)
        field.validate(value)
        if field.readonly and inst.__dict__.has_key(name):
            raise ValueError(name, 'field is readonly')
        setattr(inst, name, value)

    def __getattr__(self, name):
        return getattr(IZopeDublinCore[self.__name], name)


class DCListProperty(DCProperty):
    """Adapt to a dublin core list property
    
    Returns the DC property unchanged.
    """

    def __init__(self, name):
        self.__name = name

    def __get__(self, inst, klass):
        if inst is None:
            return self
        name = self.__name
        inst = IZopeDublinCore(inst)
        value = getattr(inst, name, _marker)
        if value is _marker:
            field = IZopeDublinCore[name].bind(inst)
            value = getattr(field, 'default', _marker)
            if value is _marker:
                raise AttributeError(name)
        return value

    def __set__(self, inst, value):
        name = self.__name
        inst = IZopeDublinCore(inst)
        field = IZopeDublinCore[name].bind(inst)
        if isinstance(field, schema.Tuple):
            value = tuple(value)
        field.validate(value)
        if field.readonly and inst.__dict__.has_key(name):
            raise ValueError(name, 'field is readonly')
        setattr(inst, name, value)

