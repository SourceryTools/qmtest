========
ZopeTree
========


What is ZopeTree?
-----------------

ZopeTree is a port of Philipp's Zope2 product ZopeTree. ZopeTree was
meant to be a light-weight and easy-to-use static tree implementation,
mainly designed for use in ZPTs. It was originally written because
Zope2's `ZTUtils.Tree` was found to be too complicated and inflexible.

The `ZTUtils` package has not been ported to Zope3. Parts of it, like
batching, have found their way into Zope3, though. Only support for
static tree generation is not in the core.


How to use it
-------------

Using the skin
~~~~~~~~~~~~~~

ZopeTree comes with a pre-defined skin, StaticTree. It looks just
like Zope3's default skin, Rotterdam, except that it displays a static
tree in the navigation box instead of the Javascript/XML based dynamic
tree.

Using predefined views on objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ZopeTree comes with several predefined views:

`cookie_tree`
  simple view using cookies for tree state storage.

`folder_cookie_tree`
  same as above, however only showing folders.

`site_cookie_tree`
  same as above, with the nearest site as root node.

`root_cookie_tree`
  same as above, with the root container as root node.

The example page template(s) in the browser package give an idea how
to use these views for HTML templating.

Customization
-------------

The best way to customize ZopeTree is to define your own view for
objects (usually '*'). If you want to use the cookie functionality,
simply extend the cookie browser view::

  from zope.app.tree.filters import OnlyInterfacesFilter
  from zope.app.tree.browser.cookie import CookieTreeView

  class BendableStaticTreeView(StaticTreeView):

      def bendablesTree(self):
          # tree with only IBendables, but also show the folder
          # they're in
          filter = OnlyInterfacesFilter(IBendable, IFolder)
          return self.cookieTree(filter)

You can also write your own filters. All you have to do is implement
the IObjectFindFilter interface (which is trivial)::

  from zope.interface import implements
  from zope.app.interfaces.find import IObjectFindFilter

  class BendableFilter:
      implements(IObjectFindFilter)

      def matches(self, obj)
          # only allow bendable objects
          return obj.isBendable()


License and Copyright
---------------------

This product is released under the terms of the `Zope Public License
(ZPL) v2.1`__. See the `ZopePublicLicense.txt` file at the root of your
Zope distribution.

Copyright (c) 2003 Philipp "philiKON" von Weitershausen
Copyright (c) 2004 Zope Corporation and Contributors

.. __: http://www.zope.org/Resources/ZPL/ZPL-2.1


Credits
-------

Thanks to ZopeMag (http://zopemag.com) for sponsoring development of
the original ZopeTree product.

Thanks to Runyaga LLC (http://runyaga.com) for sponsoring the Zope3
port.
