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
"""ZODB-based Authentication Source

$Id: principalfolder.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = "reStructuredText"

from persistent import Persistent
from zope import interface
from zope import component
from zope.event import notify
from zope.schema import Text, TextLine, Password, Choice
from zope.publisher.interfaces import IRequest

from zope.app import zapi
from zope.app.container.interfaces import DuplicateIDError
from zope.app.container.contained import Contained
from zope.app.container.constraints import contains, containers
from zope.app.container.btree import BTreeContainer
from zope.app.i18n import ZopeMessageFactory as _
from zope.app.security.interfaces import IAuthentication

from zope.app.authentication import interfaces


class IInternalPrincipal(interface.Interface):
    """Principal information"""

    login = TextLine(
        title=_("Login"),
        description=_("The Login/Username of the principal. "
                      "This value can change."))

    def setPassword(password, passwordManagerName=None):
        pass

    password = Password(
        title=_("Password"),
        description=_("The password for the principal."))

    passwordManagerName = Choice(
        title=_("Password Manager"),
        vocabulary="Password Manager Names",
        description=_("The password manager will be used"
            " for encode/check the password"),
        default="Plain Text",
        # TODO: The password manager name may be changed only
        # if the password changed
        readonly=True
        )

    title = TextLine(
        title=_("Title"),
        description=_("Provides a title for the principal."))

    description = Text(
        title=_("Description"),
        description=_("Provides a description for the principal."),
        required=False,
        missing_value='',
        default=u'')


class IInternalPrincipalContainer(interface.Interface):
    """A container that contains internal principals."""

    prefix = TextLine(
        title=_("Prefix"),
        description=_(
        "Prefix to be added to all principal ids to assure "
        "that all ids are unique within the authentication service"),
        missing_value=u"",
        default=u'',
        readonly=True)

    contains(IInternalPrincipal)


class IInternalPrincipalContained(interface.Interface):
    """Principal information"""

    containers(IInternalPrincipalContainer)


class ISearchSchema(interface.Interface):
    """Search Interface for this Principal Provider"""

    search = TextLine(
        title=_("Search String"),
        description=_("A Search String"),
        required=False,
        default=u'',
        missing_value=u'')


class InternalPrincipal(Persistent, Contained):
    """An internal principal for Persistent Principal Folder."""

    interface.implements(IInternalPrincipal, IInternalPrincipalContained)

    # If you're searching for self._passwordManagerName, or self._password
    # probably you just need to evolve the database to new generation
    # at /++etc++process/@@generations.html

    # NOTE: All changes needs to be synchronized with the evolver at
    # zope.app.zopeappgenerations.evolve2

    def __init__(self, login, password, title, description=u'',
            passwordManagerName="Plain Text"):
        self._login = login
        self._passwordManagerName = passwordManagerName
        self.password = password
        self.title = title
        self.description = description

    def getPasswordManagerName(self):
        return self._passwordManagerName

    passwordManagerName = property(getPasswordManagerName)

    def _getPasswordManager(self):
        return zapi.getUtility(
            interfaces.IPasswordManager, self.passwordManagerName)

    def getPassword(self):
        return self._password

    def setPassword(self, password, passwordManagerName=None):
        if passwordManagerName is not None:
            self._passwordManagerName = passwordManagerName
        passwordManager = self._getPasswordManager()
        self._password = passwordManager.encodePassword(password)

    password = property(getPassword, setPassword)

    def checkPassword(self, password):
        passwordManager = self._getPasswordManager()
        return passwordManager.checkPassword(self.password, password)

    def getPassword(self):
        return self._password

    def getLogin(self):
        return self._login

    def setLogin(self, login):
        oldLogin = self._login
        self._login = login
        if self.__parent__ is not None:
            try:
                self.__parent__.notifyLoginChanged(oldLogin, self)
            except ValueError:
                self._login = oldLogin
                raise

    login = property(getLogin, setLogin)


class PrincipalInfo(object):
    """An implementation of IPrincipalInfo used by the principal folder.

    A principal info is created with id, login, title, and description:

      >>> info = PrincipalInfo('users.foo', 'foo', 'Foo', 'An over-used term.')
      >>> info
      PrincipalInfo('users.foo')
      >>> info.id
      'users.foo'
      >>> info.login
      'foo'
      >>> info.title
      'Foo'
      >>> info.description
      'An over-used term.'

    """
    interface.implements(interfaces.IPrincipalInfo)

    def __init__(self, id, login, title, description):
        self.id = id
        self.login = login
        self.title = title
        self.description = description

    def __repr__(self):
        return 'PrincipalInfo(%r)' % self.id


class PrincipalFolder(BTreeContainer):
    """A Persistent Principal Folder and Authentication plugin.

    See principalfolder.txt for details.
    """

    interface.implements(interfaces.IAuthenticatorPlugin,
                         interfaces.IQuerySchemaSearch,
                         IInternalPrincipalContainer)

    schema = ISearchSchema

    def __init__(self, prefix=''):
        self.prefix = unicode(prefix)
        super(PrincipalFolder, self).__init__()
        self.__id_by_login = self._newContainerData()

    def notifyLoginChanged(self, oldLogin, principal):
        """Notify the Container about changed login of a principal.

        We need this, so that our second tree can be kept up-to-date.
        """
        # A user with the new login already exists
        if principal.login in self.__id_by_login:
            raise ValueError('Principal Login already taken!')

        del self.__id_by_login[oldLogin]
        self.__id_by_login[principal.login] = principal.__name__

    def __setitem__(self, id, principal):
        """Add principal information.

        Create a Principal Folder

            >>> pf = PrincipalFolder()

        Create a principal with 1 as id
        Add a login attr since __setitem__ is in need of one

            >>> principal = Principal(1)
            >>> principal.login = 1

        Add the principal within the Principal Folder

            >>> pf.__setitem__(u'1', principal)

        Try to add another principal with the same id.
        It should raise a DuplicateIDError

            >>> try:
            ...     pf.__setitem__(u'1', principal)
            ... except DuplicateIDError, e:
            ...     pass
            >>>
        """
        # A user with the new login already exists
        if principal.login in self.__id_by_login:
            raise DuplicateIDError('Principal Login already taken!')

        super(PrincipalFolder, self).__setitem__(id, principal)
        self.__id_by_login[principal.login] = id

    def __delitem__(self, id):
        """Remove principal information."""
        principal = self[id]
        super(PrincipalFolder, self).__delitem__(id)
        del self.__id_by_login[principal.login]

    def authenticateCredentials(self, credentials):
        """Return principal info if credentials can be authenticated
        """
        if not isinstance(credentials, dict):
            return None
        if not ('login' in credentials and 'password' in credentials):
            return None
        id = self.__id_by_login.get(credentials['login'])
        if id is None:
            return None
        internal = self[id]
        if not internal.checkPassword(credentials["password"]):
            return None
        return PrincipalInfo(self.prefix + id, internal.login, internal.title,
                             internal.description)

    def principalInfo(self, id):
        if id.startswith(self.prefix):
            internal = self.get(id[len(self.prefix):])
            if internal is not None:
                return PrincipalInfo(id, internal.login, internal.title,
                                     internal.description)

    def search(self, query, start=None, batch_size=None):
        """Search through this principal provider."""
        search = query.get('search')
        if search is None:
            return
        search = search.lower()
        n = 1
        for i, value in enumerate(self.values()):
            if (search in value.title.lower() or
                search in value.description.lower() or
                search in value.login.lower()):
                if not ((start is not None and i < start)
                        or (batch_size is not None and n > batch_size)):
                    n += 1
                    yield self.prefix + value.__name__

class Principal(object):
    """A group-aware implementation of zope.security.interfaces.IPrincipal.

    A principal is created with an ID:

      >>> p = Principal(1)
      >>> p
      Principal(1)
      >>> p.id
      1

    title and description may also be provided:

      >>> p = Principal('george', 'George', 'A site member.')
      >>> p
      Principal('george')
      >>> p.id
      'george'
      >>> p.title
      'George'
      >>> p.description
      'A site member.'

    The `groups` is a simple list, filled in by plugins.

      >>> p.groups
      []

    The `allGroups` attribute is a readonly iterable of the full closure of the
    groups in the `groups` attribute--that is, if the principal is a direct
    member of the 'Administrators' group, and the 'Administrators' group is
    a member of the 'Reviewers' group, then p.groups would be 
    ['Administrators'] and list(p.allGroups) would be
    ['Administrators', 'Reviewers'].

    To illustrate this, we'll need to set up a dummy authentication utility,
    and a few principals.  Our main principal will also gain some groups, as if
    plugins had added the groups to the list.  This is all setup--skip to the
    next block to actually see `allGroups` in action.
    
      >>> p.groups.extend(
      ...     ['content_administrators', 'zope_3_project',
      ...      'list_administrators', 'zpug'])
      >>> editor = Principal('editors', 'Content Editors')
      >>> creator = Principal('creators', 'Content Creators')
      >>> reviewer = Principal('reviewers', 'Content Reviewers')
      >>> reviewer.groups.extend(['editors', 'creators'])
      >>> usermanager = Principal('user_managers', 'User Managers')
      >>> contentAdmin = Principal(
      ...     'content_administrators', 'Content Administrators')
      >>> contentAdmin.groups.extend(['reviewers', 'user_managers'])
      >>> zope3Dev = Principal('zope_3_project', 'Zope 3 Developer')
      >>> zope3ListAdmin = Principal(
      ...     'zope_3_list_admin', 'Zope 3 List Administrators')
      >>> zope3ListAdmin.groups.append('zope_3_project') # duplicate, but
      ... # should only appear in allGroups once
      >>> listAdmin = Principal('list_administrators', 'List Administrators')
      >>> listAdmin.groups.append('zope_3_list_admin')
      >>> zpugMember = Principal('zpug', 'ZPUG Member')
      >>> martians = Principal('martians', 'Martians') # not in p's allGroups
      >>> group_data = dict((p.id, p) for p in (
      ...     editor, creator, reviewer, usermanager, contentAdmin,
      ...     zope3Dev, zope3ListAdmin, listAdmin, zpugMember, martians))
      >>> class DemoAuth(object):
      ...     interface.implements(IAuthentication)
      ...     def getPrincipal(self, id):
      ...         return group_data[id]
      ...
      >>> demoAuth = DemoAuth()
      >>> component.provideUtility(demoAuth)

    Now, we have a user with the following groups (lowest level are p's direct
    groups, and lines show membership):

      editors  creators
         \------/
             |                                     zope_3_project (duplicate)
          reviewers  user_managers                          |
               \---------/                           zope_3_list_admin
                    |                                       |
          content_administrators   zope_3_project   list_administrators   zpug

    The allGroups value includes all of the shown groups, and with
    'zope_3_project' only appearing once.

      >>> p.groups # doctest: +NORMALIZE_WHITESPACE
      ['content_administrators', 'zope_3_project', 'list_administrators',
       'zpug']
      >>> list(p.allGroups) # doctest: +NORMALIZE_WHITESPACE
      ['content_administrators', 'reviewers', 'editors', 'creators',
       'user_managers', 'zope_3_project', 'list_administrators',
       'zope_3_list_admin', 'zpug']
    """
    interface.implements(interfaces.IPrincipal)

    def __init__(self, id, title=u'', description=u''):
        self.id = id
        self.title = title
        self.description = description
        self.groups = []

    def __repr__(self):
        return 'Principal(%r)' % self.id

    @property
    def allGroups(self):
        if self.groups:
            seen = set()
            principals = component.getUtility(IAuthentication)
            stack = [iter(self.groups)]
            while stack:
                try:
                    group_id = stack[-1].next()
                except StopIteration:
                    stack.pop()
                else:
                    if group_id not in seen:
                        yield group_id
                        seen.add(group_id)
                        group = principals.getPrincipal(group_id)
                        stack.append(iter(group.groups))

class AuthenticatedPrincipalFactory(object):
    """Creates 'authenticated' principals.

    An authenticated principal is created as a result of an authentication
    operation.

    To use the factory, create it with the info (interfaces.IPrincipalInfo) of
    the principal to create and a request:

      >>> info = PrincipalInfo('users.mary', 'mary', 'Mary', 'The site admin.')
      >>> from zope.publisher.base import TestRequest
      >>> request = TestRequest('/')
      >>> factory = AuthenticatedPrincipalFactory(info, request)

    The factory must be called with a pluggable-authentication object:

      >>> class Auth:
      ...     prefix = 'auth.'
      >>> auth = Auth()

      >>> principal = factory(auth)

    The factory uses the pluggable authentication and the info to
    create a principal with the same ID, title, and description:

      >>> principal.id
      'auth.users.mary'
      >>> principal.title
      'Mary'
      >>> principal.description
      'The site admin.'

    It also fires an AuthenticatedPrincipalCreatedEvent:

      >>> from zope.component.eventtesting import getEvents
      >>> [event] = getEvents(interfaces.IAuthenticatedPrincipalCreated)
      >>> event.principal is principal, event.authentication is auth
      (True, True)
      >>> event.info
      PrincipalInfo('users.mary')
      >>> event.request is request
      True

    Listeners can subscribe to this event to perform additional operations
    when the authenticated principal is created.

    For information on how factories are used in the authentication process,
    see README.txt.
    """
    component.adapts(interfaces.IPrincipalInfo, IRequest)

    interface.implements(interfaces.IAuthenticatedPrincipalFactory)

    def __init__(self, info, request):
        self.info = info
        self.request = request

    def __call__(self, authentication):
        principal = Principal(authentication.prefix + self.info.id,
                              self.info.title,
                              self.info.description)
        notify(interfaces.AuthenticatedPrincipalCreated(
            authentication, principal, self.info, self.request))
        return principal


class FoundPrincipalFactory(object):
    """Creates 'found' principals.

    A 'found' principal is created as a result of a principal lookup.

    To use the factory, create it with the info (interfaces.IPrincipalInfo) of
    the principal to create:

      >>> info = PrincipalInfo('users.sam', 'sam', 'Sam', 'A site user.')
      >>> factory = FoundPrincipalFactory(info)

    The factory must be called with a pluggable-authentication object:

      >>> class Auth:
      ...     prefix = 'auth.'
      >>> auth = Auth()

      >>> principal = factory(auth)

    The factory uses the pluggable-authentication object and the info
    to create a principal with the same ID, title, and description:

      >>> principal.id
      'auth.users.sam'
      >>> principal.title
      'Sam'
      >>> principal.description
      'A site user.'

    It also fires a FoundPrincipalCreatedEvent:

      >>> from zope.component.eventtesting import getEvents
      >>> [event] = getEvents(interfaces.IFoundPrincipalCreated)
      >>> event.principal is principal, event.authentication is auth
      (True, True)
      >>> event.info
      PrincipalInfo('users.sam')

    Listeners can subscribe to this event to perform additional operations
    when the 'found' principal is created.

    For information on how factories are used in the authentication process,
    see README.txt.
    """
    component.adapts(interfaces.IPrincipalInfo)

    interface.implements(interfaces.IFoundPrincipalFactory)

    def __init__(self, info):
        self.info = info

    def __call__(self, authentication):
        principal = Principal(authentication.prefix + self.info.id,
                              self.info.title,
                              self.info.description)
        notify(interfaces.FoundPrincipalCreated(authentication,
                                                principal, self.info))
        return principal
