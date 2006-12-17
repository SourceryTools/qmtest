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
"""Interface Inspection Utilities

$Id: browser.py 29199 2005-02-17 22:38:55Z srichter $
"""
__docformat__ = 'restructuredtext'

import inspect

from zope.interface import Interface, providedBy
from zope.interface.interfaces import IInterface, ISpecification
from zope.interface.interfaces import IElement, IAttribute, IMethod
from zope.schema.interfaces import IField

from zope.app.apidoc.utilities import getPythonPath, renderText, getDocFormat


def getElements(iface, type=IElement):
    """Return a dictionary containing the elements in an interface.

    The type specifies whether we are looking for attributes or methods."""
    items = {}
    for name in iface:
        attr = iface[name]
        if type.providedBy(attr):
            items[name] = attr
    return items


def getFieldsInOrder(iface,
                     _itemsorter=lambda x, y: cmp(x[1].order, y[1].order)):
    """Return a list of (name, field) tuples in native interface order."""
    items = getElements(iface, IField).items()
    items.sort(_itemsorter)
    return items


def getAttributes(iface):
    """Returns a list of attributes specified in the interface."""
    return [(name, attr)
            for name, attr in getElements(iface, IAttribute).items()
            if not (IField.providedBy(attr) or IMethod.providedBy(attr))]


def getMethods(iface):
    """Returns a list of methods specified in the interface."""
    return getElements(iface, IMethod).items()


def getFields(iface):
    """Returns a list of fields specified in the interface."""
    return getFieldsInOrder(iface)


def getInterfaceTypes(iface):
    """Return a list of interface types that are specified for this
    interface.

    Note that you should only expect one type at a time.
    """
    types = list(providedBy(iface).flattened())
    # Remove interfaces provided by every interface instance
    types.remove(ISpecification)
    types.remove(IElement)
    types.remove(Interface)
    # Remove interface provided by every interface type
    types.remove(IInterface)
    return types


def getFieldInterface(field):
    """Return the interface representing the field."""
    name = field.__class__.__name__
    field_iface = None
    ifaces = tuple(providedBy(field).flattened())
    for iface in ifaces:
        # All field interfaces implement `IField`. In case the name match
        # below does not work, use the first `IField`-based interface found
        if field_iface is None and iface.extends(IField):
            field_iface = iface

        # Usually fields have interfaces with the same name (with an 'I')
        if iface.getName() == 'I' + name:
            return iface

    # If not even a `IField`-based interface was found, return the first
    # interface of the implemented interfaces list.
    return field_iface or ifaces[0]


def _getDocFormat(attr):
    module = inspect.getmodule(attr.interface)
    return getDocFormat(module)


def getAttributeInfoDictionary(attr, format=None):
    """Return a page-template-friendly information dictionary."""
    format = format or _getDocFormat(attr)
    return {'name': attr.getName(),
            'doc': renderText(attr.getDoc() or u'', format=format)}


def getMethodInfoDictionary(method, format=None):
    """Return a page-template-friendly information dictionary."""
    format = format or _getDocFormat(method)
    return {'name': method.getName(),
            'signature': method.getSignatureString(),
            'doc': renderText(method.getDoc() or u'', format=format)}


def getFieldInfoDictionary(field, format=None):
    """Return a page-template-friendly information dictionary."""
    format = format or _getDocFormat(field)

    info = {'name': field.getName(),
            'required': field.required,
            'required_string': field.required and u'required' or u'optional',
            'default': repr(field.default),
            'title': field.title}

    # Determine the interface of the field
    iface = getFieldInterface(field)
    info['iface'] = {'name': iface.getName(), 'id': getPythonPath(iface)}

    # Determine the field class
    class_ = field.__class__
    info['class'] = {'name': class_.__name__,
                     'path': getPythonPath(class_).replace('.', '/')}

    # Render the field description
    info['description'] = renderText(field.description or u'', format=format)

    return info
