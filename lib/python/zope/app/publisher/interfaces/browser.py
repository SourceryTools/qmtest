##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Browser-Specific Publisher interfaces

$Id: browser.py 67630 2006-04-27 00:54:03Z jim $
"""
from zope.app.i18n import ZopeMessageFactory as _
from zope.interface import Interface, directlyProvides
from zope.interface.interfaces import IInterface
from zope.schema import TextLine, Text, Choice, URI, Int, InterfaceField

##############################################################################
# BBB 2006/04/03 - to be removed after 12 months

import zope.deferredimport
zope.deferredimport.deprecated(
    "IBrowserView has been moved to zope.publisher.interfaces.browser. "
    "This reference will be removed in Zope 3.5.",
    IBrowserView = 'zope.publisher.interfaces.browser:IBrowserView',
    )

#
##############################################################################

class IMenuItemType(IInterface):
    """Menu item type

    Menu item types are interfaces that define classes of
    menu items.
    """

class AddMenu(Interface):
    """Special menu for providing a list of addable objects."""

directlyProvides(AddMenu, IMenuItemType)


class IBrowserMenu(Interface):
    """Menu

    Menus are objects that can return a list of menu items they contain. How
    they generate this list is up to them. Commonly, however, they will look
    up adapters that provide the ``IBrowserMenuItem`` interface.
    """

    id = TextLine(
        title=_("Menu Id"),
        description=_("The id uniquely identifies this menu."),
        required=True
        )

    title = TextLine(
        title=_("Menu title"),
        description=_("The title provides the basic label for the menu."),
        required=False
        )

    description = Text(
        title=_("Menu description"),
        description=_("A description of the menu. This might be shown "
                      "on menu pages or in pop-up help for menus."),
        required=False
        )

    def getMenuItems(object, request):
        """Return a TAL-friendly list of menu items.

        The object (acts like the context) and request can be used to select
        the items that are available.
        """


class IBrowserMenuItem(Interface):
    """Menu type

    An interface that defines a menu.
    """

    title = TextLine(
        title=_("Menu item title"),
        description=_("The title provides the basic label for the menu item."),
        required=True
        )

    description = Text(
        title=_("Menu item description"),
        description=_("A description of the menu item. This might be shown "
                      "on menu pages or in pop-up help for menu items."),
        required=False
        )

    action = TextLine(
        title=_("The URL to display if the item is selected"),
        description=_("When a user selects a browser menu item, the URL"
                      "given in the action is displayed. The action is "
                      "usually given as a relative URL, relative to the "
                      "object the menu item is for."),
       required=True
       )

    order = Int(
        title=_("Menu item ordering hint"),
        description=_("This attribute provides a hint for menu item ordering."
                      "Menu items will generally be sorted by the `for_`"
                      "attribute and then by the order.")
        )

    filter_string = TextLine(
        title=_("A condition for displaying the menu item"),
        description=_("The condition is given as a TALES expression. The "
                      "expression has access to the variables:\n"
                      "\n"
                      "context -- The object the menu is being displayed "
                      "for\n"
                      "\n"
                      "request -- The browser request\n"
                      "\n"
                      "nothing -- None\n"
                      "\n"
                      "The menu item will not be displayed if there is a \n"
                      "filter and the filter evaluates to a false value."),
        required=False)

    icon = URI(
        title=_("Icon URI"),
        description=_("URI of the icon representing this menu item"))
       
    def available():
        """Test whether the menu item should be displayed
        
        A menu item might not be available for an object, for example
        due to security limitations or constraints.
        """

class IBrowserSubMenuItem(IBrowserMenuItem):
    """A menu item that points to a sub-menu."""

    submenuId = TextLine(
        title=_("Sub-Menu Id"),
        description=_("The menu id of the menu that describes the "
                      "sub-menu below this item."),
        required=True)
        
    action = TextLine(
        title=_("The URL to display if the item is selected"),
        description=_("When a user selects a browser menu item, the URL "
                      "given in the action is displayed. The action is "
                      "usually given as a relative URL, relative to the "
                      "object the menu item is for."),
       required=False
       )


class IMenuAccessView(Interface):
    """View that provides access to menus"""

    def __getitem__(menu_id):
        """Get menu information

        Return a sequence of dictionaries with labels and
        actions, where actions are relative URLs.
        """
