# This module has moved to zope.lifecycleevent
# and will go away in Zope 3.5
import zope.deprecation
zope.deprecation.moved(
    'zope.lifecycleevent',
    "Zope 3.5",
    )

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
