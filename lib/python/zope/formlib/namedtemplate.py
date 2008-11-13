##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
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

$Id: namedtemplate.py 67630 2006-04-27 00:54:03Z jim $
"""

from zope import component, interface
import zope.traversing.interfaces

class INamedTemplate(interface.Interface):
    """A template that is looked up by name
    """

class NamedTemplateImplementation:

    def __init__(self, descriptor, view_type=None):
        try:
            descriptor.__get__
        except AttributeError:
            raise TypeError(
                "NamedTemplateImplementation must be passed a descriptor."
                )
        self.descriptor = descriptor
        interface.implementer(INamedTemplate)(self)

        if view_type is not None:
            component.adapter(view_type)(self)

    def __call__(self, instance):
        return self.descriptor.__get__(instance, instance.__class__)


class implementation:

    def __init__(self, view_type=None):
        self.view_type = view_type

    def __call__(self, descriptor):
        return NamedTemplateImplementation(descriptor, self.view_type)


class NamedTemplate(object):

    def __init__(self, name):
        self.__name__ = name

    def __get__(self, instance, type=None):
        if instance is None:
            return self
        return component.getAdapter(instance, INamedTemplate, self.__name__)

    def __call__(self, instance, *args, **kw):
        self.__get__(instance)(*args, **kw)


# TODO need test
class NamedTemplatePathAdapter(object):

    interface.implements(zope.traversing.interfaces.IPathAdapter)

    def __init__(self, context):
        self.context = context

    def __getitem__(self, name):
        return component.getAdapter(self.context, INamedTemplate, name)
