=====================================
Zope 3's Local Component Architecture
=====================================

The local component architecture provides several packages that can be used
independent of the entire component architecture framework. Thus, I decided to
document these frameworks in different files.

  o Registration Framework (`registration.txt`)

    Provides an API for creating custom registries. The entries of the
    registries are managed via registration components. A specific
    implementation for component-based registrations is also
    provided. Finally, there are some generic container classes that allow the
    developer to manage the components and their registrations.

  o Local Adapter Registry (`adapterregistry.txt`)

    Provides a persistent adapter registry that uses the registration
    framework. Local registries can be assembled to a registry tree where
    nodes further down in the tree overrride registrations of higher-up nodes.

  o Sites and Local Site Managers (`site.txt`)

    Provides a local and persistent site manager implementation, so that one
    can register local utilities and adapters. It uses local adapter
    registries for its adapter and utility registry. The module also provides
    some facilities to organize the local software and ensures the correct
    behavior inside the ZODB.


Local Component Architecture API
--------------------------------

While the component architecture API provided by ``zope.component`` is
sufficient most of the time, there are a couple of functions that are useful
in the context of multiple sites and base component registries.

--- BBB: Deprecated on 9/26/2006 --

  >>> import zope.deprecation
  >>> zope.deprecation.__show__.off()

A very common use case is to get the nearest site manager in a given
context. Sometimes, however, one wants the next higher-up site manager. First,
let's create a folder tree and create some sites from it:

  >>> from zope.app.testing import setup
  >>> root = setup.buildSampleFolderTree()
  >>> root_sm = setup.createSiteManager(root)
  >>> folder1_sm = setup.createSiteManager(root['folder1'])

If we ask `folder1` for its nearest site manager, we get

  >>> from zope.app import zapi
  >>> zapi.getSiteManager(root['folder1']) is folder1_sm
  True

but its next site manager is

  >>> from zope.app import component
  >>> component.getNextSiteManager(root['folder1']) is root_sm
  True

The next site manager of the local root is the global site manager:

  >>> gsm = zapi.getGlobalSiteManager()
  >>> component.getNextSiteManager(root) is gsm
  True

If a non-location is passed into the function, a component lookup error is
raised, since there is no site manager beyond the global site manager:

  >>> component.getNextSiteManager(object())
  Traceback (most recent call last):
  ...
  ComponentLookupError: No more site managers have been found.

If you use the `queryNextSiteManager()` function, you can specify a `default`
return value:

  >>> component.queryNextSiteManager(object(), 'default')
  'default'

  >>> zope.deprecation.__show__.on()

--- BBB: End of block --

It is common for a utility to delegate its answer to a utility providing the
same interface in one of the component registry's bases. Let's start by
creating a utility and inserting it in our folder hiearchy:

  >>> import zope.interface
  >>> class IMyUtility(zope.interface.Interface):
  ...     pass

  >>> class MyUtility(object):
  ...     zope.interface.implements(IMyUtility)
  ...     def __init__(self, id):
  ...         self.id = id
  ...     def __repr__(self):
  ...         return "%s('%s')" %(self.__class__.__name__, self.id)

  >>> gutil = MyUtility('global')
  >>> gsm.registerUtility(gutil, IMyUtility, 'myutil')

  >>> util1 = setup.addUtility(folder1_sm, 'myutil', IMyUtility,
  ...                          MyUtility('one'))

  >>> folder1_1_sm = setup.createSiteManager(root['folder1']['folder1_1'])
  >>> util1_1 = setup.addUtility(folder1_1_sm, 'myutil', IMyUtility,
  ...                            MyUtility('one-one'))

Now, if we ask `util1_1` for its next available utility and we get

  >>> component.getNextUtility(util1_1, IMyUtility, 'myutil')
  MyUtility('one')

Next we ask `util1` for its next utility and we should get the global version:

  >>> component.getNextUtility(util1, IMyUtility, 'myutil')
  MyUtility('global')

However, if we ask the global utility for the next one, an error is raised

  >>> component.getNextUtility(gutil, IMyUtility,
  ...                          'myutil') #doctest: +NORMALIZE_WHITESPACE
  Traceback (most recent call last):
  ...
  ComponentLookupError:
  No more utilities for <InterfaceClass __builtin__.IMyUtility>,
  'myutil' have been found.

or you can simply use the `queryNextUtility` and specify a default:

  >>> component.queryNextUtility(gutil, IMyUtility, 'myutil', 'default')
  'default'

Let's now ensure that the function also works with multiple registries. First
we create another base registry:

  >>> from zope.component import registry
  >>> myregistry = registry.Components()

  >>> custom_util = MyUtility('my_custom_util')
  >>> myregistry.registerUtility(custom_util, IMyUtility, 'my_custom_util')

Now we add it as a base to the local site manager:

  >>> folder1_sm.__bases__ = (myregistry,) + folder1_sm.__bases__

Both, the ``myregistry`` and global utilities should be available:

  >>> component.queryNextUtility(folder1_sm, IMyUtility, 'my_custom_util')
  MyUtility('my_custom_util')
  >>> component.queryNextUtility(folder1_sm, IMyUtility, 'myutil')
  MyUtility('global')
