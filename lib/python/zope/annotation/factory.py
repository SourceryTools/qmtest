##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
"""Annotation factory helper

$Id: factory.py 66606 2006-04-06 19:04:54Z philikon $
"""
import zope.component
import zope.interface
from zope.annotation.interfaces import IAnnotations
import zope.app.container.contained

def factory(factory, key=None):
    """Adapter factory to help create annotations easily.
    """
    # if no key is provided,
    # we'll determine the unique key based on the factory's dotted name
    if key is None:
        key = factory.__module__ + '.' + factory.__name__

    adapts = zope.component.adaptedBy(factory)
    if adapts is None:
        raise TypeError("Missing 'zope.component.adapts' on annotation")

    @zope.component.adapter(list(adapts)[0])
    @zope.interface.implementer(list(zope.component.implementedBy(factory))[0])
    def getAnnotation(context):
        annotations = IAnnotations(context)
        try:
            return annotations[key]
        except KeyError:
            result = factory()
            annotations[key] = result
            zope.app.container.contained.contained(
                result, context, key)
            return result

    # Convention to make adapter introspectable, used by apidoc
    getAnnotation.factory = factory 
    return getAnnotation
