import zope.deferredimport

zope.deferredimport.deprecatedModule(
    "zope.app.site.tests.placefulsetup",
    "zope.app.component.testing",
    "zope.app.site.tests.placefulsetup is deprecated and will go away "
    "in Zope 3.5. Use zope.app.component.testing instead"
    )

zope.deferredimport.deprecated(
    "Import of PlacefulSetup from zope.app.site.testing is deprecated "
    "and will be disabled in Zope 3.5.  Import from "
    "zope.app.component.testing instead.",
    PlacefulSetup = "zope.app.component.testing:PlacefulSetup",
    )
