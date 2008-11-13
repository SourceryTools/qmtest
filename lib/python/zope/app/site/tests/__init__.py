import zope.deferredimport

zope.deferredimport.deprecated(
    "Import of PlacefulSetup from zope.app.site.testing is deprecated "
    "and will be disabled in Zope 3.5.  Import from "
    "zope.app.component.testing instead.",
    PlacefulSetup = "zope.app.component.testing:PlacefulSetup",
    )
