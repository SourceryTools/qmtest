# This module has moved to zope.lifecycleevent.interfaces
# and will go away in Zope 3.5
import zope.deprecation
zope.deprecation.moved(
    'zope.lifecycleevent.interfaces',
    "Zope 3.5",
    )

import zope.deferredimport
zope.deferredimport.deprecated(
    "IObjectEvent has moved to zope.component.interfaces",
    IObjectEvent = 'zope.component.interfaces:IObjectEvent',
    )
