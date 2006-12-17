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
"""Interfaces for security machinery.

$Id: interfaces.py 41374 2006-01-20 04:19:08Z poster $
"""

from zope.interface import Interface, Attribute, implements
from zope.interface.common.interfaces import IAttributeError
from zope.schema import Text, TextLine, List
from zope.i18nmessageid import MessageFactory
_ = MessageFactory('zope')

class IUnauthorized(Interface):
    pass

class Unauthorized(Exception):
    """Some user wasn't allowed to access a resource"""

    implements(IUnauthorized)


class IForbidden(Interface):
    pass

class Forbidden(Exception):
    """A resource cannot be accessed under any circumstances
    """
    implements(IForbidden)

class IForbiddenAttribute(IForbidden, IAttributeError):
    pass

class ForbiddenAttribute(Forbidden, AttributeError):
    """An attribute is unavailable because it is forbidden (private)
    """
    implements(IForbiddenAttribute)


class ISecurityManagement(Interface):
    """Public security management API."""

    def getSecurityPolicy():
        """Get the system default security policy."""

    def setSecurityPolicy(aSecurityPolicy):
        """Set the system default security policy.

        This method should only be called by system startup code.  It
        should never, for example, be called during a web request.
        """


class ISecurityChecking(Interface):
    """Public security API."""

    def checkPermission(permission, object, interaction=None):
        """Return whether security policy allows permission on object.

        Arguments:
        permission -- A permission name
        object -- The object being accessed according to the permission
        interaction -- An interaction, which provides access to information
            such as authenticated principals.  If it is None, the current
            interaction is used.
        """


class ISecurityProxyFactory(Interface):

    def __call__(object, checker=None):
        """Create a security proxy

        If a checker is given, then use it, otherwise, try to figure
        out a checker.

        If the object is already a security proxy, then it will be
        returned.
        """


class IChecker(Interface):
    """Security-proxy plugin objects that implement low-level checks

    The checker is responsible for creating proxies for
    operation return values, via the proxy method.

    There are check_getattr() and check_setattr() methods for checking
    getattr and setattr, and a check() method for all other operations.

    The check methods may raise errors.  They return no value.

    Example (for __getitem__):

           checker.check(ob, \"__getitem__\")
           return checker.proxy(ob[key])
    """

    def check_getattr(ob, name):
        """Check whether attribute access is allowed.

        May raise Unauthorized or Forbidden.  Returns no value.

        If a checker implements __setitem__, then __setitem__ will be
        called rather than check_getattr to check whether an attribute
        access is allowed.  This is a hack that allows significantly
        greater performance due to the fact that low-level operator
        access is much faster than method access.
        """

    def check_setattr(ob, name):
        """Check whether attribute assignment is allowed.
        
        May raise Unauthorized or Forbidden.  Returns no value.
        """

    def check(ob, operation):
        """Check whether operation is allowed.

        The operation name is the Python special method name,
        e.g. "__getitem__".

        May raise Unauthorized or Forbidden.  Returns no value.

        If a checker implements __setitem__, then __setitem__ will be
        called rather than check to chack whether an operation is
        allowed.  This is a hack that allows significantly greater
        performance due to the fact that low-level operator access is
        much faster than method access.
        """

    def proxy(value):
        """Return a security proxy for the value.

        If a checker implements __getitem__, then __getitem__ will be
        called rather than proxy to proxy the value.  This is a hack
        that allows significantly greater performance due to the fact
        that low-level operator access is much faster than method
        access.
        """


class INameBasedChecker(IChecker):
    """Security checker that uses permissions to check attribute access."""

    def permission_id(name):
        """Return the permission used to check attribute access on name.

        This permission is used by both check and check_getattr.
        """

    def setattr_permission_id(name):
        """Return the permission used to check attribute assignment on name.

        This permission is used by check_setattr.
        """


class ISecurityPolicy(Interface):

    def __call__(participation=None):
        """Creates a new interaction for a given request.

        If participation is not None, it is added to the new interaction.
        """


class IInteraction(Interface):
    """A representation of an interaction between some actors and the system.
    """

    participations = Attribute("""An iterable of participations.""")

    def add(participation):
        """Add a participation."""

    def remove(participation):
        """Remove a participation."""

    def checkPermission(permission, object):
        """Return whether security context allows permission on object.

        Arguments:
        permission -- A permission name
        object -- The object being accessed according to the permission
        """


class IParticipation(Interface):

    interaction = Attribute("The interaction")
    principal = Attribute("The authenticated principal")


class NoInteraction(Exception):
    """No interaction started
    """

class IInteractionManagement(Interface):
    """Interaction management API.

    Every thread has at most one active interaction at a time.
    """

    def newInteraction(participation=None):
        """Start a new interaction.

        If participation is not None, it is added to the new interaction.

        Raises an error if the calling thread already has an interaction.
        """

    def queryInteraction():
        """Return the current interaction.

        Return None if there is no interaction.
        """

    def getInteraction():
        """Return the current interaction.

        Raise NoInteraction if there isn't a current interaction.
        """

    def endInteraction():
        """End the current interaction.

        Does nothing if there is no interaction.
        """
        
class IPrincipal(Interface):
    """Principals are security artifacts that execute actions in a security
    environment.

    The most common examples of principals include user and group objects.

    It is likely that IPrincipal objects will have associated views
    used to list principals in management interfaces. For example, a
    system in which other meta-data are provided for principals might
    extend IPrincipal and register a view for the extended interface
    that displays the extended information. We'll probably want to
    define a standard view name (e.g.  'inline_summary') for this
    purpose.
    """

    id = TextLine(
        title=_("Id"),
        description=_("The unique identification of the principal."),
        required=True,
        readonly=True)

    title = TextLine(
        title=_("Title"),
        description=_("The title of the principal. "
                      "This is usually used in the UI."),
        required=False)

    description = Text(
        title=_("Description"),
        description=_("A detailed description of the principal."),
        required=False)
        
        
class IGroupAwarePrincipal(IPrincipal):
    """Group aware principal interface
    Extends IPrincipal to contain group information.
    """
    
    groups = Attribute(
        'An iterable of groups to which the principal directly belongs')

class IGroupClosureAwarePrincipal(IGroupAwarePrincipal):

    allGroups = Attribute(
        "An iterable of the full closure of the principal's groups.")

class IGroup(IPrincipal):
    """Group of principals
    """

class IMemberGetterGroup(IGroup):
    """a group that can get its members"""

    def getMembers():
        """return an iterable of the members of the group"""

class IMemberAwareGroup(IMemberGetterGroup):
    """a group that can both set and get its members."""

    def setMembers(value):
        """set members of group to the principal ids in the iterable value"""

class IPermission(Interface):
    """A permission object."""

    id = TextLine(
        title=_("Id"),
        description=_("Id as which this permission will be known and used."),
        readonly=True,
        required=True)

    title = TextLine(
        title=_("Title"),
        description=_("Provides a title for the permission."),
        required=True)

    description = Text(
        title=_("Description"),
        description=_("Provides a description for the permission."),
        required=False)


        
    





