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
"""Pluggable Authentication Utility Interfaces

$Id: interfaces.py 73548 2007-03-25 09:05:22Z dobe $
"""
__docformat__ = "reStructuredText"

import zope.interface
import zope.schema
import zope.security.interfaces
from zope.app.authentication.i18n import ZopeMessageFactory as _
from zope.app.security.interfaces import ILogout
from zope.app.container.constraints import contains, containers
from zope.app.container.interfaces import IContainer


class IPlugin(zope.interface.Interface):
    """A plugin for a pluggable authentication component."""


class IPluggableAuthentication(ILogout, IContainer):
    """Provides authentication services with the help of various plugins.
    
    IPluggableAuthentication implementations will also implement
    zope.app.security.interfaces.IAuthentication.  The `authenticate` method
    of this interface in an IPluggableAuthentication should annotate the
    IPrincipalInfo with the credentials plugin and authentication plugin used.
    The `getPrincipal` method should annotate the IPrincipalInfo with the
    authentication plugin used.
    """

    contains(IPlugin)

    credentialsPlugins = zope.schema.List(
        title=_('Credentials Plugins'),
        description=_("""Used for extracting credentials.
        Names may be of ids of non-utility ICredentialsPlugins contained in
        the IPluggableAuthentication, or names of registered
        ICredentialsPlugins utilities.  Contained non-utility ids mask 
        utility names."""),
        value_type=zope.schema.Choice(vocabulary='CredentialsPlugins'),
        default=[],
        )

    authenticatorPlugins = zope.schema.List(
        title=_('Authenticator Plugins'),
        description=_("""Used for converting credentials to principals.
        Names may be of ids of non-utility IAuthenticatorPlugins contained in
        the IPluggableAuthentication, or names of registered
        IAuthenticatorPlugins utilities.  Contained non-utility ids mask 
        utility names."""),
        value_type=zope.schema.Choice(vocabulary='AuthenticatorPlugins'),
        default=[],
        )

    def getCredentialsPlugins():
        """Return iterable of (plugin name, actual credentials plugin) pairs.
        Looks up names in credentialsPlugins as contained ids of non-utility
        ICredentialsPlugins first, then as registered ICredentialsPlugin
        utilities.  Names that do not resolve are ignored."""

    def getAuthenticatorPlugins():
        """Return iterable of (plugin name, actual authenticator plugin) pairs.
        Looks up names in authenticatorPlugins as contained ids of non-utility
        IAuthenticatorPlugins first, then as registered IAuthenticatorPlugin
        utilities.  Names that do not resolve are ignored."""

    prefix = zope.schema.TextLine(
        title=_('Prefix'),
        default=u'',
        required=True,
        readonly=True,
        )

    def logout(request):
        """Performs a logout by delegating to its authenticator plugins."""


class ICredentialsPlugin(IPlugin):
    """Handles credentials extraction and challenges per request."""

    containers(IPluggableAuthentication)

    challengeProtocol = zope.interface.Attribute(
        """A challenge protocol used by the plugin.

        If a credentials plugin works with other credentials pluggins, it
        and the other cooperating plugins should specify a common (non-None)
        protocol. If a plugin returns True from its challenge method, then
        other credentials plugins will be called only if they have the same
        protocol.
        """)

    def extractCredentials(request):
        """Ties to extract credentials from a request.

        A return value of None indicates that no credentials could be found.
        Any other return value is treated as valid credentials.
        """

    def challenge(request):
        """Possibly issues a challenge.

        This is typically done in a protocol-specific way.

        If a challenge was issued, return True, otherwise return False.
        """

    def logout(request):
        """Possibly logout.

        If a logout was performed, return True, otherwise return False.
        """

class IAuthenticatorPlugin(IPlugin):
    """Authenticates a principal using credentials.

    An authenticator may also be responsible for providing information
    about and creating principals.
    """
    containers(IPluggableAuthentication)

    def authenticateCredentials(credentials):
        """Authenticates credentials.

        If the credentials can be authenticated, return an object that provides
        IPrincipalInfo. If the plugin cannot authenticate the credentials,
        returns None.
        """

    def principalInfo(id):
        """Returns an IPrincipalInfo object for the specified principal id.

        If the plugin cannot find information for the id, returns None.
        """

class IPasswordManager(zope.interface.Interface):
    """Password manager."""

    def encodePassword(password):
        """Return encoded data for the password."""

    def checkPassword(storedPassword, password):
        """Return whether the password coincide with the storedPassword."""

class IPrincipalInfo(zope.interface.Interface):
    """Minimal information about a principal."""

    id = zope.interface.Attribute("The principal id.")

    title = zope.interface.Attribute("The principal title.")

    description = zope.interface.Attribute("A description of the principal.")

    credentialsPlugin = zope.interface.Attribute(
        """Plugin used to generate the credentials for this principal info.
        
        Optional.  Should be set in IPluggableAuthentication.authenticate.
        """)

    authenticatorPlugin = zope.interface.Attribute(
        """Plugin used to authenticate the credentials for this principal info.
        
        Optional.  Should be set in IPluggableAuthentication.authenticate and
        IPluggableAuthentication.getPrincipal.
        """)

class IPrincipal(zope.security.interfaces.IGroupClosureAwarePrincipal):

    groups = zope.schema.List(
        title=_("Groups"),
        description=_(
            """ids of groups to which the principal directly belongs.

            Plugins may append to this list.  Mutating the list only affects
            the life of the principal object, and does not persist (so
            persistently adding groups to a principal should be done by working
            with a plugin that mutates this list every time the principal is
            created, like the group folder in this package.)
            """),
        value_type=zope.schema.TextLine(),
        required=False)

class IPrincipalFactory(zope.interface.Interface):
    """A principal factory."""

    def __call__(authentication):
        """Creates a principal.

        The authentication utility that called the factory is passed
        and should be included in the principal-created event.
        """


class IFoundPrincipalFactory(IPrincipalFactory):
    """A found principal factory."""


class IAuthenticatedPrincipalFactory(IPrincipalFactory):
    """An authenticated principal factory."""


class IPrincipalCreated(zope.interface.Interface):
    """A principal has been created."""

    principal = zope.interface.Attribute("The principal that was created")

    authentication = zope.interface.Attribute(
        "The authentication utility that created the principal")

    info = zope.interface.Attribute("An object providing IPrincipalInfo.")


class IAuthenticatedPrincipalCreated(IPrincipalCreated):
    """A principal has been created by way of an authentication operation."""

    request = zope.interface.Attribute(
        "The request the user was authenticated against")


class AuthenticatedPrincipalCreated:
    """
    >>> from zope.interface.verify import verifyObject
    >>> event = AuthenticatedPrincipalCreated("authentication", "principal",
    ...     "info", "request")
    >>> verifyObject(IAuthenticatedPrincipalCreated, event)
    True
    """

    zope.interface.implements(IAuthenticatedPrincipalCreated)

    def __init__(self, authentication, principal, info, request):
        self.authentication = authentication
        self.principal = principal
        self.info = info
        self.request = request


class IFoundPrincipalCreated(IPrincipalCreated):
    """A principal has been created by way of a search operation."""


class FoundPrincipalCreated:
    """
    >>> from zope.interface.verify import verifyObject
    >>> event = FoundPrincipalCreated("authentication", "principal",
    ...     "info")
    >>> verifyObject(IFoundPrincipalCreated, event)
    True
    """

    zope.interface.implements(IFoundPrincipalCreated)

    def __init__(self, authentication, principal, info):
        self.authentication = authentication
        self.principal = principal
        self.info = info


class IQueriableAuthenticator(zope.interface.Interface):
    """Indicates the authenticator provides a search UI for principals."""


class IQuerySchemaSearch(zope.interface.Interface):
    """An interface for searching using schema-constrained input."""

    schema = zope.interface.Attribute("""
        The schema that constrains the input provided to the search method.

        A mapping of name/value pairs for each field in this schema is used
        as the query argument in the search method.
        """)

    def search(query, start=None, batch_size=None):
        """Returns an iteration of principal IDs matching the query.

        query is a mapping of name/value pairs for fields specified by the
        schema.

        If the start argument is provided, then it should be an
        integer and the given number of initial items should be
        skipped.

        If the batch_size argument is provided, then it should be an
        integer and no more than the given number of items should be
        returned.
        """

class IGroupAdded(zope.interface.Interface):
    """A group has been added."""

    group = zope.interface.Attribute("""The group that was defined""")


class GroupAdded:
    """
    >>> from zope.interface.verify import verifyObject
    >>> event = GroupAdded("group")
    >>> verifyObject(IGroupAdded, event)
    True
    """

    zope.interface.implements(IGroupAdded)

    def __init__(self, group):
        self.group = group

    def __repr__(self):
        return "<GroupAdded %r>" % self.group.id

class IPrincipalsAddedToGroup(zope.interface.Interface):
    group_id = zope.interface.Attribute(
        'the id of the group to which the principal was added')
    principal_ids = zope.interface.Attribute(
        'an iterable of one or more ids of principals added')

class IPrincipalsRemovedFromGroup(zope.interface.Interface):
    group_id = zope.interface.Attribute(
        'the id of the group from which the principal was removed')
    principal_ids = zope.interface.Attribute(
        'an iterable of one or more ids of principals removed')

class AbstractMembersChanged(object):

    def __init__(self, principal_ids, group_id):
        self.principal_ids = principal_ids
        self.group_id = group_id

    def __repr__(self):
        return "<%s %r %r>" % (
            self.__class__.__name__, sorted(self.principal_ids), self.group_id)

class PrincipalsAddedToGroup(AbstractMembersChanged):
    zope.interface.implements(IPrincipalsAddedToGroup)

class PrincipalsRemovedFromGroup(AbstractMembersChanged):
    zope.interface.implements(IPrincipalsRemovedFromGroup)
