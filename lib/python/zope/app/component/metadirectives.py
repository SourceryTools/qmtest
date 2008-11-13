##############################################################################
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
"""Component architecture related 'zope' ZCML namespace directive interfaces

$Id: metadirectives.py 73604 2007-03-25 12:17:44Z dobe $
"""
__docformat__ = 'restructuredtext'

import zope.configuration.fields
import zope.security.zcml
import zope.interface
import zope.schema
from zope.component.zcml import IBasicComponentInformation

from zope.app.component.back35 import LayerField
from zope.app.component.i18n import ZopeMessageFactory as _

class IDefaultViewName(zope.interface.Interface):
    """A string that contains the default view name

    A default view name is used to select a view when a user hasn't
    specified one.
    """

class IBasicViewInformation(zope.interface.Interface):
    """This is the basic information for all views."""

    for_ = zope.configuration.fields.Tokens(
        title=_("Specifications of the objects to be viewed"),
        description=_("""This should be a list of interfaces or classes
        """),
        required=True,
        value_type=zope.configuration.fields.GlobalObject(
          missing_value=object(),
          ),
        )

    permission = zope.security.zcml.Permission(
        title=_("Permission"),
        description=_("The permission needed to use the view."),
        required=False,
        )

    class_ = zope.configuration.fields.GlobalObject(
        title=_("Class"),
        description=_("A class that provides attributes used by the view."),
        required=False,
        )

    layer = LayerField(
        title=_("The layer the view is in."),
        description=_("""
        A skin is composed of layers. It is common to put skin
        specific views in a layer named after the skin. If the 'layer'
        attribute is not supplied, it defaults to 'default'."""),
        required=False,
        )

    allowed_interface = zope.configuration.fields.Tokens(
        title=_("Interface that is also allowed if user has permission."),
        description=_("""
        By default, 'permission' only applies to viewing the view and
        any possible sub views. By specifying this attribute, you can
        make the permission also apply to everything described in the
        supplied interface.

        Multiple interfaces can be provided, separated by
        whitespace."""),
        required=False,
        value_type=zope.configuration.fields.GlobalInterface(),
        )

    allowed_attributes = zope.configuration.fields.Tokens(
        title=_("View attributes that are also allowed if the user"
                " has permission."),
        description=_("""
        By default, 'permission' only applies to viewing the view and
        any possible sub views. By specifying 'allowed_attributes',
        you can make the permission also apply to the extra attributes
        on the view object."""),
        required=False,
        value_type=zope.configuration.fields.PythonIdentifier(),
        )

class IBasicResourceInformation(zope.interface.Interface):
    """
    Basic information for resources
    """

    name = zope.schema.TextLine(
        title=_("The name of the resource."),
        description=_("The name shows up in URLs/paths. For example 'foo'."),
        required=True,
        default=u'',
        )

    provides = zope.configuration.fields.GlobalInterface(
        title=_("The interface this component provides."),
        description=_("""
        A view can provide an interface.  This would be used for
        views that support other views."""),
        required=False,
        default=zope.interface.Interface,
        )

    type = zope.configuration.fields.GlobalInterface(
        title=_("Request type"),
        required=True
        )


# BBB 2006/02/24, to be removed after 12 months
class IFactoryDirective(zope.interface.Interface):
    """
    *BBB: DEPRECATED*

    The ``factory`` directive has been deprecated and will be
    removed in Zope 3.5.  Use the ``utility`` directive instead::

      <utility
          provides="zope.component.interfaces.IFactory"
          component="some.factory.class"
          name="factoryName"
          />

    (Define a factory.)
    """

    component = zope.configuration.fields.GlobalObject(
        title=_("Component to be used"),
        required=True,
        )

    id = zope.schema.Id(
        title=_("ID"),
        required=False,
        )

    title = zope.configuration.fields.MessageID(
        title=_("Title"),
        description=_("Text suitable for use in the 'add content' menu of"
                      " a management interface"),
        required=False,
        )

    description = zope.configuration.fields.MessageID(
        title=_("Description"),
        description=_("Longer narrative description of what this factory"
                      " does"),
        required=False,
        )


class IViewDirective(IBasicViewInformation, IBasicResourceInformation):
    """Register a view for a component"""

    factory = zope.configuration.fields.Tokens(
        title=_("Factory"),
        required=False,
        value_type=zope.configuration.fields.GlobalObject(),
        )

############################################################################
# BBB: Deprecated; use browser:defaultView instead. Will go away in 3.3.
class IDefaultViewDirective(IBasicResourceInformation):
    """
    *BBB: DEPRECATED*

    Use ``browser:defaultView`` instead.

    The name of the view that should be the default.

    This name refers to view that should be the
    view used by default (if no view name is supplied
    explicitly).
    """

    for_ = zope.configuration.fields.GlobalInterface(
        title=_("The interface this view is the default for."),
        description=_("""
        Specifies the interface for which the default view is declared. All
        objects implementing this interface make use of this default
        setting. If this attribute is not specified, the default is available
        for all objects."""),
        required=False,
        )
############################################################################


class IResourceDirective(IBasicComponentInformation,
                         IBasicResourceInformation):
    """Register a resource"""

    layer = LayerField(
        title=_("The layer the resource is in."),
        required=False,
        )

    allowed_interface = zope.configuration.fields.Tokens(
        title=_("Interface that is also allowed if user has permission."),
        required=False,
        value_type=zope.configuration.fields.GlobalInterface(),
        )

    allowed_attributes = zope.configuration.fields.Tokens(
        title=_("View attributes that are also allowed if user"
                " has permission."),
        required=False,
        value_type=zope.configuration.fields.PythonIdentifier(),
        )


class IClassDirective(zope.interface.Interface):
    """Make statements about a class"""

    class_ = zope.configuration.fields.GlobalObject(
        title=_("Class"),
        required=True
        )

# BBB 2006/09/17, to be removed after 12 months
class IBBBClassDirective(IClassDirective):
    """ *BBB: DEPRECATED*

    It is discouraged to use ``content`` or ``localUtility`` directives.
    They are currently deprecated:
    only use ``class`` directive for class statements.
    """

class IImplementsSubdirective(zope.interface.Interface):
    """Declare that the class given by the content directive's class
    attribute implements a given interface
    """

    interface = zope.configuration.fields.Tokens(
        title=_("One or more interfaces"),
        required=True,
        value_type=zope.configuration.fields.GlobalInterface()
        )

class IRequireSubdirective(zope.interface.Interface):
    """Indicate that the a specified list of names or the names in a
    given Interface require a given permission for access.
    """

    permission = zope.security.zcml.Permission(
        title=_("Permission"),
        description=_("""
        Specifies the permission by id that will be required to
        access or mutate the attributes and methods specified."""),
        required=False,
        )

    attributes = zope.configuration.fields.Tokens(
        title=_("Attributes and methods"),
        description=_("This is a list of attributes and methods"
                      " that can be accessed."),
        required=False,
        value_type=zope.configuration.fields.PythonIdentifier(),
        )

    set_attributes = zope.configuration.fields.Tokens(
        title=_("Attributes that can be set"),
        description=_("This is a list of attributes that can be"
                      " modified/mutated."),
        required=False,
        value_type=zope.configuration.fields.PythonIdentifier(),
        )

    interface = zope.configuration.fields.Tokens(
        title=_("Interfaces"),
        description=_("The listed interfaces' methods and attributes"
                      " can be accessed."),
        required=False,
        value_type=zope.configuration.fields.GlobalInterface(),
        )

    set_schema = zope.configuration.fields.Tokens(
        title=_("The attributes specified by the schema can be set"),
        description=_("The listed schemas' properties can be"
                      " modified/mutated."),
        required=False,
        value_type=zope.configuration.fields.GlobalInterface(),
        )

    like_class = zope.configuration.fields.GlobalObject(
        title=_("Configure like this class"),
        description=_("""
        This argument says that this content class should be configured in the
        same way the specified class' security is. If this argument is
        specified, no other argument can be used."""),
        required=False,
        )

class IAllowSubdirective(zope.interface.Interface):
    """
    Declare a part of the class to be publicly viewable (that is,
    requires the zope.Public permission). Only one of the following
    two attributes may be used.
    """

    attributes = zope.configuration.fields.Tokens(
        title=_("Attributes"),
        required=False,
        value_type=zope.configuration.fields.PythonIdentifier(),
        )

    interface = zope.configuration.fields.Tokens(
        title=_("Interface"),
        required=False,
        value_type=zope.configuration.fields.GlobalInterface(),
        )

class IFactorySubdirective(zope.interface.Interface):
    """Specify the factory used to create this content object"""

    id = zope.schema.Id(
        title=_("ID"),
        description=_("""
        the identifier for this factory in the ZMI factory
        identification scheme.  If not given, defaults to the literal
        string given as the content directive's 'class' attribute."""),
        required=False,
        )

    title = zope.configuration.fields.MessageID(
        title=_("Title"),
        description=_("Text suitable for use in the 'add content' menu"
                      " of a management interface"),
        required=False,
        )

    description = zope.configuration.fields.MessageID(
        title=_("Description"),
        description=_("Longer narrative description of what this"
                      " factory does"),
        required=False,
        )
