========================================
Code Module specific `apidoc` Directives 
========================================

The `apidoc:rootModule` Directive
---------------------------------

The `rootModule` directive allows you to register a third party Python package
with apidoc's code browser. 

Before we can register a new root module, we need to load the
metaconfiguration:

  >>> from zope.configuration import xmlconfig
  >>> import zope.app.apidoc.codemodule
  >>> context = xmlconfig.file('meta.zcml', zope.app.apidoc.codemodule)

Now we can run the directive. First, let's make sure that no root modules have
been registered yet:

  >>> from zope.component import getUtilitiesFor
  >>> from zope.app.apidoc.codemodule.interfaces import IAPIDocRootModule
  >>> list(getUtilitiesFor(IAPIDocRootModule))
  []

Now run the registration code:

  >>> context = xmlconfig.string('''
  ...     <configure
  ...         xmlns="http://namespaces.zope.org/apidoc">
  ...       <rootModule module="zope" />
  ...     </configure>''', context)

and the root module is available:

  >>> list(getUtilitiesFor(IAPIDocRootModule))
  [(u'zope', 'zope')]


The `apidoc:importModule` Directive
-----------------------------------

The `importModule` directive allows you to set the
``__import_unknown_modules__`` flag of the class registry. When this flag is
set to false, paths will only be looked up in ``sys.modules``. When set true,
and the ``sus.modules`` lookup fails, the import function of the class
registry tries to import the path. The hook was provided for security reasons,
since uncontrolled importing of modules in a running application is considered
a security hole.

By default the flag is set to false:

  >>> from zope.app.apidoc import classregistry
  >>> classregistry.__import_unknown_modules__
  False

We can now use the directive to set it to true:

  >>> context = xmlconfig.string('''
  ...     <configure
  ...         xmlns="http://namespaces.zope.org/apidoc">
  ...       <moduleImport allow="true" />
  ...     </configure>''', context)

  >>> classregistry.__import_unknown_modules__
  True

We can also set it back to false of course:

  >>> context = xmlconfig.string('''
  ...     <configure
  ...         xmlns="http://namespaces.zope.org/apidoc">
  ...       <moduleImport allow="false" />
  ...     </configure>''', context)

  >>> classregistry.__import_unknown_modules__
  False

