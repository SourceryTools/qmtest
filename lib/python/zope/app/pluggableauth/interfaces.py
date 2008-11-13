##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Pluggable Authentication Utility.

$Id: interfaces.py 81110 2007-10-25 16:38:47Z srichter $
"""
__docformat__ = 'restructuredtext'

from zope.i18nmessageid import ZopeMessageFactory as _
from zope.app.container.interfaces import IContainer, IContained
from zope.app.container.constraints import ItemTypePrecondition
from zope.app.container.constraints import ContainerTypesConstraint
from zope.app.security.interfaces import IAuthentication, IPrincipal
from zope.interface import Interface
from zope.schema import Text, TextLine, Password, Field

class IUserSchemafied(IPrincipal):
    """A User object with schema-defined attributes."""

    login = TextLine(
        title=_("Login"),
        description=_("The Login/Username of the user. "
                      "This value can change."),
        required=True)

    password = Password(
        title=_(u"Password"),
        description=_("The password for the user."),
        required=True)

    def validate(test_password):
        """Confirm whether 'password' is the password of the user."""


class IPrincipalSource(Interface):
    """A read-only source of `IPrincipals`."""

    def getPrincipal(id):
        """Get principal meta-data.

        Returns an object of type `IPrincipal` for the given principal
        id. A ``PrincipalLookupError`` is raised if the principal cannot be
        found.

        Note that the id has three parts, separated by tabs.  The
        first two part are an authentication utility id and a
        principal source id.  The pricipal source will typically need
        to remove the two leading parts from the id when doing it's
        own internal lookup.

        Note that the authentication utility nearest to the requested
        resource is called. It is up to authentication utility
        implementations to collaborate with utilities higher in the
        object hierarchy.
        """

    def getPrincipals(name):
        """Get principals with matching names.

        Get a iterable object with the principals with names that are
        similar to (e.g. contain) the given name.
        """


class IPluggableAuthentication(IAuthentication, IContainer):
    """An `Authentication` utility that can contain multiple pricipal sources.
    """

    def __setitem__(id, principal_source):
        """Add to object"""
    __setitem__.precondition = ItemTypePrecondition(IPrincipalSource)

    def removePrincipalSource(id):
        """Remove a `PrincipalSource`.

        If id is not present, raise ``KeyError``.
        """

IPluggableAuthenticationService = IPluggableAuthentication

class ILoginPasswordPrincipalSource(IPrincipalSource):
    """A principal source which can authenticate a user given a
    login and a password """

    def authenticate(login, password):
        """Return a principal matching the login/password pair.

        If there is no principal in this principal source which
        matches the login/password pair, return ``None``.

        Note: A login is different than an id.  Principals may have
        logins that differ from their id.  For example, a user may
        have a login which is his email address.  He'd like to be able
        to change his login when his email address changes without
        effecting his security profile on the site.  """


class IContainerPrincipalSource(IContainer):
    """This is a marker interface for specifying principal sources that are
    also containers. """


class IContainedPrincipalSource(IPrincipalSource, IContained):
    """This is a marker interface for principal sources that can be directly
    added to an authentication utility. It ensures that principal source can
    **only** be added to pluggable authentication utilities."""

    __parent__= Field(
        constraint = ContainerTypesConstraint(IPluggableAuthentication))
