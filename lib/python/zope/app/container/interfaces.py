##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Container-related interfaces

$Id: interfaces.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

from zope.deprecation import deprecated

from zope.interface import Interface, Attribute, Invalid
from zope.component.interfaces import IView, IObjectEvent
from zope.interface.common.mapping import IItemMapping
from zope.interface.common.mapping import IReadMapping, IEnumerableMapping
from zope.location.interfaces import ILocation
from zope.lifecycleevent.interfaces import IObjectModifiedEvent

deprecated('IContentContainer',
           'This interface has been deprecated. '
           'Check the "containerViews" zcml directive. '
           'The reference will be gone in 3.3')

class DuplicateIDError(KeyError):
    pass

class ContainerError(Exception):
    """An error of a container with one of its components."""

class InvalidContainerType(Invalid, TypeError):
    """The type of a container is not valid."""

class InvalidItemType(Invalid, TypeError):
    """The type of an item is not valid."""

class InvalidType(Invalid, TypeError):
    """The type of an object is not valid."""



class IContained(ILocation):
    """Objects contained in containers."""


class IItemContainer(IItemMapping):
    """Minimal readable container."""


class ISimpleReadContainer(IItemContainer, IReadMapping):
    """Readable content containers."""


class IReadContainer(ISimpleReadContainer, IEnumerableMapping):
    """Readable containers that can be enumerated."""


class IWriteContainer(Interface):
    """An interface for the write aspects of a container."""

    def __setitem__(name, object):
        """Add the given `object` to the container under the given name.

        Raises a ``TypeError`` if the key is not a unicode or ascii string.
        Raises a ``ValueError`` if key is empty.

        The container might choose to add a different object than the
        one passed to this method.

        If the object doesn't implement `IContained`, then one of two
        things must be done:

        1. If the object implements `ILocation`, then the `IContained`
           interface must be declared for the object.

        2. Otherwise, a `ContainedProxy` is created for the object and
           stored.

        The object's `__parent__` and `__name__` attributes are set to the
        container and the given name.

        If the old parent was ``None``, then an `IObjectAddedEvent` is
        generated, otherwise, an `IObjectMovedEvent` is generated.  An
        `IContainerModifiedEvent` is generated for the container.

        If the object replaces another object, then the old object is
        deleted before the new object is added, unless the container
        vetos the replacement by raising an exception.

        If the object's `__parent__` and `__name__` were already set to
        the container and the name, then no events are generated and
        no hooks.  This allows advanced clients to take over event
        generation.

        """

    def __delitem__(name):
        """Delete the named object from the container.

        Raises a ``KeyError`` if the object is not found.

        If the deleted object's `__parent__` and `__name__` match the
        container and given name, then an `IObjectRemovedEvent` is
        generated and the attributes are set to ``None``. If the object
        can be adapted to `IObjectMovedEvent`, then the adapter's
        `moveNotify` method is called with the event.

        Unless the object's `__parent__` and `__name__` attributes were
        initially ``None``, generate an `IContainerModifiedEvent` for the
        container.

        If the object's `__parent__` and `__name__` were already set to
        ``None``, then no events are generated.  This allows advanced
        clients to take over event generation.

        """


class IItemWriteContainer(IWriteContainer, IItemContainer):
    """A write container that also supports minimal reads."""


class IContentContainer(IWriteContainer):
    """Containers (like folders) that contain ordinary content."""


class IContainer(IReadContainer, IWriteContainer):
    """Readable and writable content container."""


class IOrderedContainer(IContainer):
    """Containers whose contents are maintained in order."""

    def updateOrder(order):
        """Revise the order of keys, replacing the current ordering.

        order is a list or a tuple containing the set of existing keys in
        the new order. `order` must contain ``len(keys())`` items and cannot
        contain duplicate keys.

        Raises ``TypeError`` if order is not a tuple or a list.

        Raises ``ValueError`` if order contains an invalid set of keys.
        """


class IContainerNamesContainer(IContainer):
    """Containers that always choose names for their items."""


##############################################################################
# Moving Objects

class IObjectMovedEvent(IObjectEvent):
    """An object has been moved."""

    oldParent = Attribute("The old location parent for the object.")
    oldName = Attribute("The old location name for the object.")
    newParent = Attribute("The new location parent for the object.")
    newName = Attribute("The new location name for the object.")


##############################################################################
# Adding objects

class UnaddableError(ContainerError):
    """An object cannot be added to a container."""

    def __init__(self, container, obj, message=""):
        self.container = container
        self.obj = obj
        self.message = message and ": %s" % message

    def __str__(self):
        return ("%(obj)s cannot be added "
                "to %(container)s%(message)s" % self.__dict__)


class IObjectAddedEvent(IObjectMovedEvent):
    """An object has been added to a container."""


class IAdding(IView):

    def add(content):
        """Add content object to container.

        Add using the name in `contentName`.  Returns the added object
        in the context of its container.

        If `contentName` is already used in container, raises
        ``DuplicateIDError``.
        """

    contentName = Attribute(
         """The content name, as usually set by the Adder traverser.

         If the content name hasn't been defined yet, returns ``None``.

         Some creation views might use this to optionally display the
         name on forms.
         """
         )

    def nextURL():
        """Return the URL that the creation view should redirect to.

        This is called by the creation view after calling add.

        It is the adder's responsibility, not the creation view's to
        decide what page to display after content is added.
        """

    def nameAllowed():
        """Return whether names can be input by the user."""

    def addingInfo():
        """Return add menu data as a sequence of mappings.

        Each mapping contains 'action', 'title', and possibly other keys.

        The result is sorted by title.
        """

    def isSingleMenuItem():
        """Return whether there is single menu item or not."""

    def hasCustomAddView():
        "This should be called only if there is `singleMenuItem` else return 0"


class INameChooser(Interface):

    def checkName(name, object):
        """Check whether an object name is valid.

        Raises a user error if the name is not valid.
        """

    def chooseName(name, object):
        """Choose a unique valid name for the object

        The given name and object may be taken into account when
        choosing the name.
        """


##############################################################################
# Removing objects


class IObjectRemovedEvent(IObjectMovedEvent):
    """An object has been removed from a container."""


##############################################################################
# Modifying containers


class IContainerModifiedEvent(IObjectModifiedEvent):
    """The container has been modified.

    This event is specific to "containerness" modifications, which means
    addition, removal or reordering of sub-objects.
    """


##############################################################################
# Finding objects

class IFind(Interface):
    """
    Find support for containers.
    """

    def find(id_filters=None, object_filters=None):
        """Find object that matches all filters in all sub-objects.

        This container itself is not included.
        """


class IObjectFindFilter(Interface):

    def matches(object):
        """Return True if the object matches the filter criteria."""


class IIdFindFilter(Interface):

    def matches(id):
        """Return True if the id matches the filter criteria."""
