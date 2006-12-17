##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Interfaces for code browser

$Id$
"""
__docformat__ = "reStructuredText"
import zope.interface
import zope.schema

from zope.app.container.interfaces import IReadContainer
from zope.app.i18n import ZopeMessageFactory as _


class IAPIDocRootModule(zope.interface.Interface):
    """Marker interface for utilities that represent class browser root
    modules.

    The utilities will be simple strings, representing the modules Python
    dotted name.
    """

class IModuleDocumentation(IReadContainer):
    """Representation of a Python module for documentation.

    The items of the container are sub-modules and classes.
    """
    def getDocString():
        """Return the doc string of the module."""

    def getFileName():
        """Return the file name of the module."""

    def getPath():
        """Return the Python path of the module."""


class IClassDocumentation(zope.interface.Interface):
    """Representation of a class or type for documentation."""

    def getDocString():
        """Return the doc string of the class."""

    def getPath():
        """Return the Python path of the class."""

    def getBases():
        """Return the base classes of the class."""

    def getKnownSubclasses():
        """Return the known subclasses classes of the class."""

    def getInterfaces():
        """Return the interfaces the class implements."""

    def getAttributes():
        """Return a list of 3-tuple attribute information.

        The first entry of the 3-tuple is the name of the attribute, the
        second is the attribute object itself. The third entry is the
        interface in which the attribute is defined.

        Note that only public attributes are returned, meaning only attributes
        that do not start with an '_'-character.
        """

    def getMethods():
        """Return a list of 3-tuple method information.

        The first entry of the 3-tuple is the name of the method, the
        second is the method object itself. The third entry is the
        interface in which the method is defined.

        Note that only public methods are returned, meaning only methods
        that do not start with an '_'-character.
        """

    def getMethodDescriptors():
        """Return a list of 3-tuple method descriptor information.

        The first entry of the 3-tuple is the name of the method, the
        second is the method descriptor object itself. The third entry is the
        interface in which the method is defined.

        Note that only public methods are returned, meaning only method
        descriptors that do not start with an '_'-character.
        """

    def getSecurityChecker():
        """Return the security checker for this class.

        Since 99% of the time we are dealing with name-based security
        checkers, we can look up the get/set permission required for a
        particular class attribute/method.
        """


class IFunctionDocumentation(zope.interface.Interface):
    """Representation of a function for documentation."""

    def getDocString():
        """Return the doc string of the function."""

    def getPath():
        """Return the Python path of the function."""

    def getSignature():
        """Return the signature of the function as a string."""

    def getAttributes():
        """Return a list of 2-tuple attribute information.

        The first entry of the 2-tuple is the name of the attribute, the
        second is the attribute object itself.
        """

class IDirective(zope.interface.Interface):
    """Representation of a directive in IZCMLFile."""

    name = zope.schema.Tuple(
        title=u'Name',
        description=u'Name of the directive in the form (Namespace. Name)',
        required = True)

    schema = zope.schema.Field(
        title=u'Schema',
        description=u'Schema describing the directive attributes',
        required = True)

    attrs = zope.schema.Field(
        title=u'Attributes',
        description=u'SAX parser representation of the directive\'s attributes',
        required = True)

    context = zope.schema.Field(
        title=u'Configuration Context',
        description=u'Configuration context while the directive was parsed.',
        required = True)

    prefixes = zope.schema.Dict(
        title=u'Prefixes',
        description=u'Mapping from namespace URIs to prefixes.',
        required = True)

    info = zope.schema.Field(
        title=u'Info',
        description=u'ParserInfo objects containing line and column info.',
        required = True)

    __parent__ = zope.schema.Field(
        title=u'Parent',
        description=u'Parent Directive',
        required = True)

    subs = zope.schema.List(
        title=u'Sub-Directives',
        description=u'List of sub-directives',
        required = True)


class IRootDirective(IDirective):
    """Marker interface"""


class IZCMLFile(zope.interface.Interface):
    """ZCML File Object

    This is the main object that will manage the configuration of one particular
    ZCML configuration file.
    """

    filename = zope.schema.BytesLine(
        title=_('Configuration Filename'),
        description=_('Path to the configuration file'),
        required=True)

    package = zope.schema.BytesLine(
        title=_('Configuration Package'),
        description=_(
        '''Specifies the package from which the configuration file will be
        executed. If you do not specify the package, then the configuration
        cannot be fully validated and improper ZCML files might be written.'''),
        required=False)

    rootElement = zope.schema.Field(
        title=_("XML Root Element"),
        description=_("XML element representing the configuration root."),
        required=True)
