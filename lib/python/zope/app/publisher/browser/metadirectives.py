#############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Browser configuration code

This module defines the schemas for browser directives.

$Id: metadirectives.py 69358 2006-08-05 17:54:32Z flox $
"""
from zope.interface import Interface
from zope.configuration.fields import GlobalObject, GlobalInterface
from zope.configuration.fields import Tokens, Path, PythonIdentifier, MessageID
from zope.schema import TextLine, Text, Id, Int, Bool
from zope.security.zcml import Permission

from zope.app.component.metadirectives import IBasicViewInformation
from zope.app.component.back35 import LayerField
from zope.app.publisher.browser.fields import MenuField

#
# browser views
#

class IPagesDirective(IBasicViewInformation):
    """
    Define multiple pages without repeating all of the parameters.

    The pages directive allows multiple page views to be defined
    without repeating the 'for', 'permission', 'class', 'layer',
    'allowed_attributes', and 'allowed_interface' attributes.
    """

    for_ = GlobalObject(
        title=u"The interface or class this view is for.",
        required=False
        )

    permission = Permission(
        title=u"Permission",
        description=u"The permission needed to use the view.",
        required=True
        )

class IViewDirective(IPagesDirective):
    """
    The view directive defines a view that has subpages.

    The pages provided by the defined view are accessed by first
    traversing to the view name and then traversing to the page name.
    """

    for_ = GlobalInterface(
        title=u"The interface this view is for.",
        required=False
        )

    name = TextLine(
        title=u"The name of the view.",
        description=u"The name shows up in URLs/paths. For example 'foo'.",
        required=False,
        default=u'',
        )

    menu = MenuField(
        title=u"The browser menu to include the page (view) in.",
        description=u"""
          Many views are included in menus. It's convenient to name
          the menu in the page directive, rather than having to give a
          separate menuItem directive.  'zmi_views' is the menu most often
          used in the Zope management interface.
          </description>
          """,
        required=False
        )

    title = MessageID(
        title=u"The browser menu label for the page (view)",
        description=u"""
          This attribute must be supplied if a menu attribute is
          supplied.
          """,
        required=False
        )

    provides = GlobalInterface(
        title=u"The interface this view provides.",
        description=u"""
        A view can provide an interface.  This would be used for
        views that support other views.""",
        required=False,
        default=Interface,
        )

class IViewPageSubdirective(Interface):
    """
    Subdirective to IViewDirective.
    """

    name = TextLine(
        title=u"The name of the page (view)",
        description=u"""
        The name shows up in URLs/paths. For example 'foo' or
        'foo.html'. This attribute is required unless you use the
        subdirective 'page' to create sub views. If you do not have
        sub pages, it is common to use an extension for the view name
        such as '.html'. If you do have sub pages and you want to
        provide a view name, you shouldn't use extensions.""",
        required=True
        )

    attribute = PythonIdentifier(
        title=u"The name of the view attribute implementing the page.",
        description=u"""
        This refers to the attribute (method) on the view that is
        implementing a specific sub page.""",
        required=False
        )

    template = Path(
        title=u"The name of a template that implements the page.",
        description=u"""
        Refers to a file containing a page template (should end in
        extension '.pt' or '.html').""",
        required=False
        )

class IViewDefaultPageSubdirective(Interface):
    """
    Subdirective to IViewDirective.
    """

    name = TextLine(
        title=u"The name of the page that is the default.",
        description=u"""
        The named page will be used as the default if no name is
        specified explicitly in the path. If no defaultPage directive
        is supplied, the default page will be the first page
        listed.""",
        required=True
        )

class IDefaultViewDirective(Interface):
    """
    The name of the view that should be the default.

    This name refers to view that should be the
    view used by default (if no view name is supplied
    explicitly).
    """

    name = TextLine(
        title=u"The name of the view that should be the default.",
        description=u"""
        This name refers to view that should be the view used by
        default (if no view name is supplied explicitly).""",
        required=True
        )

    for_ = GlobalInterface(
        title=u"The interface this view is the default for.",
        description=u"""Specifies the interface for which the view is
        registered. All objects implementing this interface can make use of
        this view. If this attribute is not specified, the view is available
        for all objects.""",
        required=False
        )

    layer = LayerField(
        title=u"The layer the default view is declared for",
        description=u"The default layer for which the default view is "
                    u"applicable. By default it is applied to all layers.",
        required=False
        )

#
# browser pages
#

class IPagesPageSubdirective(IViewPageSubdirective):
    """
    Subdirective to IPagesDirective
    """

    menu = MenuField(
        title=u"The browser menu to include the page (view) in.",
        description=u"""
        Many views are included in menus. It's convenient to name the
        menu in the page directive, rather than having to give a
        separate menuItem directive.""",
        required=False
        )

    title = MessageID(
        title=u"The browser menu label for the page (view)",
        description=u"""
        This attribute must be supplied if a menu attribute is
        supplied.""",
        required=False
        )

class IPageDirective(IPagesDirective, IPagesPageSubdirective):
    """
    The page directive is used to create views that provide a single
    url or page.

    The page directive creates a new view class from a given template
    and/or class and registers it.
    """


#
# browser resources
#

class IBasicResourceInformation(Interface):
    """
    This is the basic information for all browser resources.
    """

    layer = LayerField(
        title=u"The layer the resource should be found in",
        description=u"""
        For information on layers, see the documentation for the skin
        directive. Defaults to "default".""",
        required=False
        )

    permission = Permission(
        title=u"The permission needed to access the resource.",
        description=u"""
        If a permission isn't specified, the resource will always be
        accessible.""",
        required=False
        )

class IResourceDirective(IBasicResourceInformation):
    """
    Defines a browser resource
    """

    name = TextLine(
        title=u"The name of the resource",
        description=u"""
        This is the name used in resource urls. Resource urls are of
        the form site/@@/resourcename, where site is the url of
        "site", a folder with a site manager.

        We make resource urls site-relative (as opposed to
        content-relative) so as not to defeat caches.""",
        required=True
        )

    factory = GlobalObject(
        title=u"Resource Factory",
        description=u"The factory used to create the resource. The factory "
                    u"should only expect to get the request passed when "
                    u"called.",
        required=False
        )

    file = Path(
        title=u"File",
        description=u"The file containing the resource data.",
        required=False
        )

    image = Path(
        title=u"Image",
        description=u"""
        If the image attribute is used, then an image resource, rather
        than a file resource will be created.""",
        required=False
        )

    template = Path(
        title=u"Template",
        description=u"""
        If the template attribute is used, then a page template resource,
        rather than a file resource will be created.""",
        required=False
        )

class II18nResourceDirective(IBasicResourceInformation):
    """
    Defines an i18n'd resource.
    """

    name = TextLine(
        title=u"The name of the resource",
        description=u"""
        This is the name used in resource urls. Resource urls are of
        the form site/@@/resourcename, where site is the url of
        "site", a folder with a site manager.

        We make resource urls site-relative (as opposed to
        content-relative) so as not to defeat caches.""",
        required=True
        )

    defaultLanguage = TextLine(
        title=u"Default language",
        description=u"Defines the default language",
        required=False
        )

class II18nResourceTranslationSubdirective(IBasicResourceInformation):
    """
    Subdirective to II18nResourceDirective.
    """

    language = TextLine(
        title=u"Language",
        description=u"Language of this translation of the resource",
        required=True
        )

    file = Path(
        title=u"File",
        description=u"The file containing the resource data.",
        required=False
        )

    image = Path(
        title=u"Image",
        description=u"""
        If the image attribute is used, then an image resource, rather
        than a file resource will be created.""",
        required=False
        )

class IResourceDirectoryDirective(IBasicResourceInformation):
    """
    Defines a directory containing browser resource
    """

    name = TextLine(
        title=u"The name of the resource",
        description=u"""
        This is the name used in resource urls. Resource urls are of
        the form site/@@/resourcename, where site is the url of
        "site", a folder with a site manager.

        We make resource urls site-relative (as opposed to
        content-relative) so as not to defeat caches.""",
        required=True
        )

    directory = Path(
        title=u"Directory",
        description=u"The directory containing the resource data.",
        required=True
        )

#
# browser menus
#

class IMenuDirective(Interface):
    """Define a browser menu"""

    id = TextLine(
        title=u"The name of the menu.",
        description=u"This is, effectively, an id.",
        required=False
        )

    title = MessageID(
        title=u"Title",
        description=u"A descriptive title for documentation purposes",
        required=False
        )
    
    description = MessageID(
        title=u"Description",
        description=u"A description title of the menu.",
        required=False
        )

    class_ = GlobalObject(
        title=u"Menu Class",
        description=u"The menu class used to generate the menu.",
        required=False
        )

    interface = GlobalInterface(
        title=u"The menu's interface.",
        required=False
        )
    

class IMenuItemsDirective(Interface):
    """
    Define a group of browser menu items

    This directive is useful when many menu items are defined for the
    same interface and menu.
    """

    menu = MenuField(
        title=u"Menu name",
        description=u"The (name of the) menu the items are defined for",
        required=True,
        )

    for_ = GlobalInterface(
        title=u"Interface",
        description=u"The interface the menu items are defined for",
        required=True
        )

    layer = LayerField(
        title=u"Layer",
        description=u"The Layer for which the item is declared.",
        required=False
        )

class IMenuItem(Interface):
    """Common menu item configuration
    """

    title = MessageID(
        title=u"Title",
        description=u"The text to be displayed for the menu item",
        required=True
        )

    description = MessageID(
        title=u"A longer explanation of the menu item",
        description=u"""
        A UI may display this with the item or display it when the
        user requests more assistance.""",
        required=False
        )

    icon = TextLine(
        title=u"Icon Path",
        description=u"Path to the icon resource representing this menu item.",
        required=False
        )

    permission = Permission(
        title=u"The permission needed access the item",
        description=u"""
        This can usually be inferred by the system, however, doing so
        may be expensive. When displaying a menu, the system tries to
        traverse to the URLs given in each action to determine whether
        the url is accessible to the current user. This can be
        avoided if the permission is given explicitly.""",
        required=False
        )

    filter = TextLine(
        title=u"A condition for displaying the menu item",
        description=u"""
        The condition is given as a TALES expression. The expression
        has access to the variables:

        context -- The object the menu is being displayed for

        request -- The browser request

        nothing -- None

        The menu item will not be displayed if there is a filter and
        the filter evaluates to a false value.""",
        required=False
        )

    order = Int(
        title=u"Order",
        description=u"A relative position of the menu item in the menu.",
        required=False,
        default=0
        )

class IMenuItemSubdirective(IMenuItem):
    """Define a menu item within a group of menu items"""

    action = TextLine(
        title=u"The relative url to use if the item is selected",
        description=u"""
        The url is relative to the object the menu is being displayed
        for.""",
        required=True
        )

class IMenuItemDirective(IMenuItemsDirective, IMenuItemSubdirective):
    """Define one menu item"""

class ISubMenuItemSubdirective(IMenuItem):
    """Define a menu item that represents a a sub menu.

    For a sub-menu menu item, the action is optional, this the item itself
    might not represent a destination, but just an entry point to the sub menu. 
    """

    action = TextLine(
        title=u"The relative url to use if the item is selected",
        description=u"""
        The url is relative to the object the menu is being displayed
        for.""",
        required=False
        )

    submenu = TextLine(
        title=u"Sub-Menu Id",
        description=u"The menu that will be used to provide the sub-entries.",
        required=True,
        )
    
class ISubMenuItemDirective(IMenuItemsDirective, ISubMenuItemSubdirective):
    """Define one menu item"""

class IAddMenuItemDirective(IMenuItem):
    """Define an add-menu item"""

    for_ = GlobalInterface(
        title=u"Interface",
        description=u"The interface the menu items are defined for",
        required=False
        )

    class_ = GlobalObject(
        title=u"Class",
        description=u"""
        A class to be used as a factory for creating new objects""",
        required=False
        )

    factory = Id(
        title=u"Factory",
        description=u"A factory id for creating new objects",
        required = False,
        )

    view = TextLine(
        title=u"Custom view name",
        description=u"The name of a custom add view",
        required = False,
        )

    menu = MenuField(
        title=u"Menu name",
        description=u"The (name of the) menu the items are defined for",
        required=False,
        )

    layer = LayerField(
        title=u"The layer the custom view is declared for",
        description=u"The default layer for which the custom view is "
                    u"applicable. By default it is applied to all layers.",
        required=False
        )

#
# misc. directives
#

# BBB 2006/02/18, to be removed after 12 months
class ILayerDirective(Interface):
    """ *BBB: DEPRECATED*

    Creating layers via ZCML has been deprecated.  The
    'browser:layer' directive will be removed in Zope 3.5.  Layers
    are now interfaces extending
    'zope.publisher.interfaces.browser.IBrowserRequest'.
    They do not need further registration.

    **Previous documentation**

    Defines a browser layer

    You must either specify a `name` or an `interface`. If you specify the
    name, then a layer interface will be created for you based on the name and
    the `base` interface.

    If you specify the `name` and the `interface`, then the layer will be
    registered twice for the name. This way we can be backward compatible. 
    The layer is still available via its dotted name.

    If you do not specify a `base`, then `IBrowserRequest` is used by default.

    You cannot specify both, the `interface` and the `base` attribute.
    """

    name = TextLine(
        title=u"Name",
        description=u"The name of the layer.",
        required=False
        )

    interface = GlobalInterface(
        title=u"The layer's interface.",
        required=False
        )

    base = GlobalObject(
        title=u"Name",
        description=u"The name of the skin",
        required=False
        )

    bbb_aware = Bool(
        title=u"BBB-aware",
        description=u"Backward-compatability aware?",
        required=False
        )

# BBB 2006/02/18, to be removed after 12 months
class ISkinDirective(Interface):
    """ *BBB: DEPRECATED*

    Creating skins via ZCML has been deprecated.  The 'browser:skin'
    directive will be removed in Zope 3.5.  Skins are now interfaces
    extending 'zope.publisher.interfaces.browser.IBrowserRequest'.
    They are registered using the 'interface' directive.

    **Previous documentation**

    Defines a browser skin

    If you do not specify an `interface`, then one will be automatically
    created for you based on the name using the layers as base interfaces.

    In case you specify an `interface` and a `name`, the skin will be
    available via its dotted name of the interface and the name you specified.

    You cannot specify both, the `interface` and the `layers` attribute.    
    """

    name = TextLine(
        title=u"Name",
        description=u"The name of the skin",
        required=False
        )

    interface = GlobalInterface(
        title=u"The skin's interface.",
        required=False
        )

    layers = Tokens(
        title=u"A list of layers",
        description=u"""
        This should be in order of lookup. Usually one of the layers
        has the same name as the skin, and the last layer should be
        'default', unless you want to completely override all views.
        """,
        required=False,
        value_type=LayerField()
        )

class IDefaultSkinDirective(Interface):
    """Sets the default browser skin
    """

    name = TextLine(
        title=u"Default skin name",
        description=u"Default skin name",
        required=True
        )


class IIconDirective(Interface):
    """
    Define an icon for an interface
    """

    name = TextLine(
        title=u"The name of the icon.",
        description=u"The name shows up in URLs/paths. For example 'foo'.",
        required=True
        )

    for_ = GlobalInterface(
        title=u"The interface this icon is for.",
        description=u"""
        The icon will be for all objects that implement this
        interface.""",
        required=True
        )

    file = Path(
        title=u"File",
        description=u"The file containing the icon.",
        required=False
        )

    resource = TextLine(
        title=u"Resource",
        description=u"A resource containing the icon.",
        required=False
        )

    title = MessageID(
        title=u"Title",
        description=u"Descriptive title",
        required=False
        )

    layer = LayerField(
        title=u"The layer the icon should be found in",
        description=u"""
        For information on layers, see the documentation for the skin
        directive. Defaults to "default".""",
        required=False
        )
