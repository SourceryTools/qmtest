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

$Id: factory.py 78905 2007-08-17 12:12:44Z zagy $
"""
import zope.component
import zope.interface
import zope.location.location

import zope.annotation.interfaces


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
        annotations = zope.annotation.interfaces.IAnnotations(context)
        try:
            result = annotations[key]
        except KeyError:
            result = factory()
            annotations[key] = result
        # Location has to be set up late to allow location proxies
        # to be applied, if needed. This does not trigger an event and is idempotent
        # if location or containment is set up already.
        located_result = zope.location.location.located(result, context, key)
        return located_result

    # Convention to make adapter introspectable, used by apidoc
    getAnnotation.factory = factory
    return getAnnotation
