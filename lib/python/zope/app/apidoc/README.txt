========================
Zope 3 API Documentation
========================

This Zope 3 package provides fully dynamic API documentation of Zope 3 and
registered add-on components. The package is very extensible and can be easily
extended by implementing new modules.

Besides being an application, the API doctool also provides several public
APIs to extract information from various objects used by Zope 3.

 * utilities -- Miscellaneous classes and functions that aid all documentation
   modules. They are broadly usable.

 * interface -- This module contains functions to inspect interfaces and
   schemas.

 * component -- This modules provides utility functions to lookup components
   given an interface.

 * presentation -- Presentation components are generally more complex than
   others, so a separate utilities module is provided to inspect views.

 * classregistry -- Here a simple dictionary-based registry for all known
   classes is provided. It allows us to search in classes.


Using the API Dcoumentation
---------------------------

The `APIDocumentation` class provides access to all available documentation
modules. Documentation modules are utilities providing `IDocumentationModule`:


  >>> from zope.app.testing import ztapi
  >>> from zope.app.apidoc.interfaces import IDocumentationModule
  >>> from zope.app.apidoc.ifacemodule.ifacemodule import InterfaceModule
  >>> from zope.app.apidoc.zcmlmodule import ZCMLModule

  >>> ztapi.provideUtility(IDocumentationModule, InterfaceModule(),
  ...                      'Interface')
  >>> ztapi.provideUtility(IDocumentationModule, ZCMLModule(), 'ZCML')

Now we can instantiate the class (which is usually done when traversing
'++apidoc++') and get a list of available modules:

  >>> from zope.app.apidoc.apidoc import APIDocumentation
  >>> doc = APIDocumentation(None, '++apidoc++')

  >>> modules =  doc.keys()
  >>> modules.sort()
  >>> modules
  [u'Interface', u'ZCML']

  >>> doc['ZCML'] #doctest:+ELLIPSIS
  <zope.app.apidoc.zcmlmodule.ZCMLModule object at ...>


Developing a Module
-------------------

1. Implement a class that realizes the `IDocumentationModule`
   interface.

2. Register this class as a utility using something like this::

     <utility
         provides="zope.app.apidoc.interfaces.IDocumentationModule"
         factory=".examplemodule.ExampleModule"
         name="Example" />

3. Take care of security by allowing at least `IDocumentationModule`::

     <class class=".ExampleModule">
       <allow interface="zope.app.apidoc.interfaces.IDocumentationModule" />
     </class>

4. Provide a browser view called ``menu.html``.

5. Provide another view, usually ``index.html``, that can show the
   details for the various menu items.

Note:  There are several modules that come with the product. Just look
in them for some guidance.


New Static APIDOC-Version
-------------------------

An alternative APIDOC-Version is available through ++apidoc++/static.html 
Find and Tree is implemented in Javascript. So it should be possible to do a
"wget" - Offline-Version of APIDOC



