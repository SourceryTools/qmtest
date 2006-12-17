# This file is necessary to make this directory a package.

import zope.deferredimport
zope.deferredimport.deprecated(
    "Its contents has moved into zope.component.testing.  This reference "
    "will be gone in Zope 3.5",
    placelesssetup = 'zope.component.testing',
    )
