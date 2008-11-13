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
"""Life cycle events

$Id: __init__.py 67636 2006-04-27 11:31:54Z srichter $
"""
__docformat__ = 'restructuredtext'

import zope.component.interfaces
from zope.component import subscribers
from zope.interface import implements
from zope.event import notify
from zope.lifecycleevent.interfaces import IObjectCreatedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.lifecycleevent.interfaces import IObjectCopiedEvent
from zope.lifecycleevent.interfaces import IAttributes, ISequence

_marker = object()

##############################################################################
# BBB 2006/04/03 -- to be removed after 12 months

import zope.deferredimport
zope.deferredimport.deprecated(
    "It has moved to zope.component.interfaces.  This reference will be "
    "gone in Zope 3.5.",
    ObjectEvent = 'zope.component.interfaces:ObjectEvent',
    )
zope.deferredimport.deprecated(
    "It has moved to zope.component.event.  This reference will be gone "
    "in Zope 3.5",
    objectEventNotify = 'zope.component.event:objectEventNotify',
    )

#
##############################################################################

class ObjectCreatedEvent(zope.component.interfaces.ObjectEvent):
    """An object has been created"""

    # for repr backward compatibility. In the next release cycle, we'll
    # provide a testing framework that addresses repr migration.
    __module__ = 'zope.app.event.objectevent'

    implements(IObjectCreatedEvent)


class Attributes(object) :
    """
    Describes modified attributes of an interface.

        >>> from zope.dublincore.interfaces import IZopeDublinCore
        >>> desc = Attributes(IZopeDublinCore, "title", "description")
        >>> desc.interface == IZopeDublinCore
        True
        >>> 'title' in desc.attributes
        True

    """

    implements(IAttributes)

    def __init__(self, interface, *attributes) :
        self.interface = interface
        self.attributes = attributes


class Sequence(object) :
    """
    Describes modified keys of an interface.

        >>> from zope.app.container.interfaces import IContainer
        >>> desc = Sequence(IContainer, 'foo', 'bar')
        >>> desc.interface == IContainer
        True
        >>> desc.keys
        ('foo', 'bar')

    """

    implements(ISequence)

    def __init__(self, interface, *keys) :
        self.interface = interface
        self.keys = keys

class ObjectModifiedEvent(zope.component.interfaces.ObjectEvent):
    """An object has been modified"""

    # for repr backward compatibility. In the next release cycle, we'll
    # provide a testing framework that addresses repr migration.
    __module__ = 'zope.app.event.objectevent'

    implements(IObjectModifiedEvent)

    def __init__(self, object, *descriptions) :
        """
        Init with a list of modification descriptions.

        >>> from zope.interface import implements, Interface, Attribute
        >>> class ISample(Interface) :
        ...     field = Attribute("A test field")
        >>> class Sample(object) :
        ...     implements(ISample)

        >>> obj = Sample()
        >>> obj.field = 42
        >>> notify(ObjectModifiedEvent(obj, Attributes(ISample, "field")))

        """
        super(ObjectModifiedEvent, self).__init__(object)
        self.descriptions = descriptions


def modified(object, *descriptions):
    notify(ObjectModifiedEvent(object, *descriptions))


class ObjectCopiedEvent(ObjectCreatedEvent):
    """An object has been copied"""

    # for repr backward compatibility. In the next release cycle, we'll
    # provide a testing framework that addresses repr migration.
    __module__ = 'zope.app.event.objectevent'

    implements(IObjectCopiedEvent)

    def __init__(self, object, original):
        super(ObjectCopiedEvent, self).__init__(object)
        self.original = original
