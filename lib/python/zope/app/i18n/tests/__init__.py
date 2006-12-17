# This file is necessary to make this directory a package.

# BBB 2006/04/19 -- to be removed after 12 months
import zope.deferredimport
zope.deferredimport.deprecated(
    "Its contents has moved into zope.i18n.testing.  This reference "
    "will be gone in Zope 3.5",
    placelesssetup = 'zope.i18n.testing',
    )
