Life-cycle events
=================

In Zope 3, events are used by components to inform each other about
relevant new objects and object modifications.

To keep all subscribers up to date it is indispensable that the life
cycle of an object is accompanied by various events.

    >>> from zope.event import notify
    >>> from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent

    >>> class Sample(object) :
    ...    "Test class"

    >>> obj = Sample()
    >>> notify(ObjectCreatedEvent(obj))
    
    >>> obj.modified = True
    >>> notify(ObjectModifiedEvent(obj))
    
Zope 3's Dublin Core Metadata for instance, rely on the bare
ObjectCreatedEvent and ObjectModifiedEvent to record creation and
modification times. Other event consumers like catalogs and caches may
need more information to update themselves in an efficient manner. The
necessary information can be provided as optional modification
descriptions of the ObjectModifiedEvent.

Some examples:

    >>> from zope.interface import Interface, Attribute, implements
    >>> class IFile(Interface):
    ...     data = Attribute("Data")
    ... 

    >>> class File(object):
    ...     implements(IFile)
    ...

    >>> file = File()
    >>> file.data = "123"
    >>> notify(ObjectModifiedEvent(obj, IFile))
    
This says that we modified something via IFile.  Note that an interface is an 
acceptable description. In fact, we might allow pretty much anything as a 
description and it depends on your needs what kind of descriptions 
you use.

In the following we use an IAttributes description to describe in more detail
which parts of an object where modified :

    >>> file.data = "456"
 
    >>> from zope.dublincore.interfaces import IZopeDublinCore
    >>> from zope.interface import directlyProvides
    >>> from zope.annotation.interfaces import IAttributeAnnotatable
    >>> directlyProvides(file, IAttributeAnnotatable) 
    
    >>> IZopeDublinCore(file).title = u"New title"
    >>> IZopeDublinCore(file).title = u"New description"

    >>> from zope.lifecycleevent import Attributes
    >>> event = ObjectModifiedEvent(
    ...     obj,
    ...     Attributes(IFile, 'data'),
    ...     Attributes(IZopeDublinCore, 'title', 'description'),
    ...     )
    >>> notify(event)

This says we modified the file data and the DC title and description.
