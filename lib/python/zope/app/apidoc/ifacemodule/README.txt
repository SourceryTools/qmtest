==================================
The Interface Documentation Module
==================================

This documentation module allows you to inspect all aspects of an interface
and its role within the Zope 3 framework. The module can be instantiated like
all other documentation modules:

  >>> from zope.app.apidoc.ifacemodule.ifacemodule import InterfaceModule
  >>> module = InterfaceModule()

After registering an interface

  >>> from zope.interface import Interface
  >>> class IFoo(Interface):
  ...     pass

  >>> from zope.component.interface import provideInterface
  >>> provideInterface(None, IFoo)
  >>> provideInterface('IFoo', IFoo)

Now let's lookup an interface that is registered.
  
  >>> module.get('IFoo')
  <InterfaceClass __builtin__.IFoo>

  >>> module.get('__builtin__.IFoo')
  <InterfaceClass __builtin__.IFoo>
  

Now we find an interface that is not in the site manager, but exists.

  >>> module.get('zope.app.apidoc.interfaces.IDocumentationModule')
  <InterfaceClass zope.app.apidoc.interfaces.IDocumentationModule>
 
Finally, you can list all registered interfaces:

  >>> ifaces = module.items()
  >>> ifaces.sort()
  >>> pprint(ifaces)
  [(u'IFoo', <InterfaceClass __builtin__.IFoo>),
   (u'__builtin__.IFoo', <InterfaceClass __builtin__.IFoo>)]
