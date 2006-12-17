"""
Interfaces for the unique id utility.

$Id: interfaces.py 30786 2005-06-13 20:55:05Z jim $
"""
from zope.interface import Interface, Attribute, implements


class IIntIdsQuery(Interface):

    def getObject(uid):
        """Return an object by its unique id"""

    def getId(ob):
        """Get a unique id of an object.
        """

    def queryObject(uid, default=None):
        """Return an object by its unique id

        Return the default if the uid isn't registered
        """

    def queryId(ob, default=None):
        """Get a unique id of an object.

        Return the default if the object isn't registered
        """

    def __iter__():
        """Return an iteration on the ids"""
        

class IIntIdsSet(Interface):

    def register(ob):
        """Register an object and returns a unique id generated for it.

        The object *must* be adaptable to IKeyReference.

        If the object is already registered, its id is returned anyway.
        """

    def unregister(ob):
        """Remove the object from the indexes.

        KeyError is raised if ob is not registered previously.
        """

class IIntIdsManage(Interface):
    """Some methods used by the view."""

    def __len__():
        """Return the number of objects indexed."""

    def items():
        """Return a list of (id, object) pairs."""


class IIntIds(IIntIdsSet, IIntIdsQuery, IIntIdsManage):
    """A utility that assigns unique ids to objects.

    Allows to query object by id and id by object.
    """


class IIntIdRemovedEvent(Interface):
    """A unique id will be removed

    The event is published before the unique id is removed
    from the utility so that the indexing objects can unindex the object.
    """

    object = Attribute("The object being removed")

    original_event = Attribute("The IObjectRemoveEvent related to this event")


class IntIdRemovedEvent:
    """The event which is published before the unique id is removed
    from the utility so that the catalogs can unindex the object.
    """

    implements(IIntIdRemovedEvent)

    def __init__(self, object, event):
        self.object = object
        self.original_event = event


class IIntIdAddedEvent(Interface):
    """A unique id has been added

    The event gets sent when an object is registered in a
    unique id utility.
    """

    object = Attribute("The object being added")

    original_event = Attribute("The ObjectAddedEvent related to this event")


class IntIdAddedEvent:
    """The event which gets sent when an object is registered in a
    unique id utility.
    """

    implements(IIntIdAddedEvent)

    def __init__(self, object, event):
        self.object = object
        self.original_event = event
