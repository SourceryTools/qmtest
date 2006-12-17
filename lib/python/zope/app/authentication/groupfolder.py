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
"""Zope Groups Folder implementation

$Id: groupfolder.py 41374 2006-01-20 04:19:08Z poster $

"""
import BTrees.OOBTree
import persistent

from zope import interface, event, schema, component
from zope.interface import alsoProvides
from zope.security.interfaces import (
    IGroup, IGroupAwarePrincipal, IMemberAwareGroup)

from zope.app import zapi
from zope.app.container.btree import BTreeContainer
import zope.app.container.constraints
import zope.app.container.interfaces
from zope.app.i18n import ZopeMessageFactory as _
import zope.app.security.vocabulary
from zope.app.security.interfaces import IAuthenticatedGroup, IEveryoneGroup
from zope.app.authentication import principalfolder, interfaces


class IGroupInformation(interface.Interface):

    title = schema.TextLine(
        title=_("Title"),
        description=_("Provides a title for the permission."),
        required=True)

    description = schema.Text(
        title=_("Description"),
        description=_("Provides a description for the permission."),
        required=False)

    principals = schema.List(
        title=_("Principals"),
        value_type=schema.Choice(
            source=zope.app.security.vocabulary.PrincipalSource()),
        description=_(
        "List of ids of principals which belong to the group"),
        required=False)


class IGroupFolder(zope.app.container.interfaces.IContainer):

    zope.app.container.constraints.contains(IGroupInformation)

    prefix = schema.TextLine(
        title=_("Group ID prefix"),
        description=_("Prefix added to IDs of groups in this folder"),
        readonly=True,
        )

    def getGroupsForPrincipal(principalid):
        """Get groups the given principal belongs to"""

    def getPrincipalsForGroup(groupid):
        """Get principals which belong to the group"""


class IGroupContained(zope.app.container.interfaces.IContained):

    zope.app.container.constraints.containers(IGroupFolder)

class IGroupSearchCriteria(interface.Interface):

    search = schema.TextLine(
        title=_("Group Search String"),
        required=False,
        missing_value=u'',
        )

class IGroupPrincipalInfo(interfaces.IPrincipalInfo):
    members = interface.Attribute('an iterable of members of the group')

class GroupInfo(object):
    """An implementation of IPrincipalInfo used by the group folder.

    A group info is created with id, title, and description:

      >>> class DemoGroupInformation(object):
      ...     interface.implements(IGroupInformation)
      ...     def __init__(self, title, description, principals):
      ...         self.title = title
      ...         self.description = description
      ...         self.principals = principals
      ...
      >>> i = DemoGroupInformation(
      ...     'Managers', 'Taskmasters', ('joe', 'jane'))
      ...
      >>> info = GroupInfo('groups.managers', i)
      >>> info
      GroupInfo('groups.managers')
      >>> info.id
      'groups.managers'
      >>> info.title
      'Managers'
      >>> info.description
      'Taskmasters'
      >>> info.members
      ('joe', 'jane')
      >>> info.members = ('joe', 'jane', 'jaime')
      >>> info.members
      ('joe', 'jane', 'jaime')

    """
    interface.implements(IGroupPrincipalInfo)

    def __init__(self, id, information):
        self.id = id
        self._information = information

    @property
    def title(self):
        return self._information.title

    @property
    def description(self):
        return self._information.description

    @apply
    def members():
        def get(self):
            return self._information.principals
        def set(self, value):
            self._information.principals = value
        return property(get, set)

    def __repr__(self):
        return 'GroupInfo(%r)' % self.id


class GroupFolder(BTreeContainer):

    interface.implements(
        interfaces.IAuthenticatorPlugin,
        interfaces.IQuerySchemaSearch,
        IGroupFolder)

    schema = IGroupSearchCriteria

    def __init__(self, prefix=u''):
        self.prefix=prefix
        super(BTreeContainer,self).__init__()
        # __inversemapping is used to map principals to groups
        self.__inverseMapping = BTrees.OOBTree.OOBTree()

    def __setitem__(self, name, value):
        BTreeContainer.__setitem__(self, name, value)
        group_id = self._groupid(value)
        self._addPrincipalsToGroup(value.principals, group_id)
        if value.principals:
            event.notify(
                interfaces.PrincipalsAddedToGroup(
                    value.principals, self.__parent__.prefix + group_id))
        group = principalfolder.Principal(self.prefix + name)
        event.notify(interfaces.GroupAdded(group))

    def __delitem__(self, name):
        value = self[name]
        group_id = self._groupid(value)
        self._removePrincipalsFromGroup(value.principals, group_id)
        if value.principals:
            event.notify(
                interfaces.PrincipalsRemovedFromGroup(
                    value.principals, self.__parent__.prefix + group_id))
        BTreeContainer.__delitem__(self, name)

    def _groupid(self, group):
        return self.prefix+group.__name__

    def _addPrincipalsToGroup(self, principal_ids, group_id):
        for principal_id in principal_ids:
            self.__inverseMapping[principal_id] = (
                self.__inverseMapping.get(principal_id, ())
                + (group_id,))

    def _removePrincipalsFromGroup(self, principal_ids, group_id):
        for principal_id in principal_ids:
            groups = self.__inverseMapping.get(principal_id)
            if groups is None:
                return
            new = tuple([id for id in groups if id != group_id])
            if new:
                self.__inverseMapping[principal_id] = new
            else:
                del self.__inverseMapping[principal_id]

    def getGroupsForPrincipal(self, principalid):
        """Get groups the given principal belongs to"""
        return self.__inverseMapping.get(principalid, ())

    def getPrincipalsForGroup(self, groupid):
        """Get principals which belong to the group"""
        return self[groupid].principals

    def search(self, query, start=None, batch_size=None):
        """ Search for groups"""
        search = query.get('search')
        if search is not None:
            n = 0
            search = search.lower()
            for i, (id, groupinfo) in enumerate(self.items()):
                if (search in groupinfo.title.lower() or
                    (groupinfo.description and 
                     search in groupinfo.description.lower())):
                    if not ((start is not None and i < start)
                            or
                            (batch_size is not None and n >= batch_size)):
                        n += 1
                        yield self.prefix + id

    def authenticateCredentials(self, credentials):
        # user folders don't authenticate
        pass

    def principalInfo(self, id):
        if id.startswith(self.prefix):
            id = id[len(self.prefix):]
            info = self.get(id)
            if info is not None:
                return GroupInfo(
                    self.prefix+id, info)

class GroupCycle(Exception):
    """There is a cyclic relationship among groups
    """

class InvalidPrincipalIds(Exception):
    """A user has a group id for a group that can't be found
    """

class InvalidGroupId(Exception):
    """A user has a group id for a group that can't be found
    """

def nocycles(principal_ids, seen, getPrincipal):
    for principal_id in principal_ids:
        if principal_id in seen:
            raise GroupCycle(principal_id, seen)
        seen.append(principal_id)
        principal = getPrincipal(principal_id)
        nocycles(principal.groups, seen, getPrincipal)
        seen.pop()

class GroupInformation(persistent.Persistent):

    interface.implements(IGroupInformation, IGroupContained)

    __parent__ = __name__ = None

    _principals = ()

    def __init__(self, title='', description=''):
        self.title = title
        self.description = description

    def setPrincipals(self, prinlist, check=True):
        # method is not a part of the interface
        parent = self.__parent__
        old = self._principals
        self._principals = tuple(prinlist)

        if parent is not None:
            oldset = set(old)
            new = set(prinlist)
            group_id = parent._groupid(self)
            removed = oldset - new
            added = new - oldset
            try:
                parent._removePrincipalsFromGroup(removed, group_id)
            except AttributeError:
                removed = None

            try:
                parent._addPrincipalsToGroup(added, group_id)
            except AttributeError:
                added = None

            if check:
                try:
                    nocycles(new, [], zapi.principals().getPrincipal)
                except GroupCycle:
                    # abort
                    self.setPrincipals(old, False)
                    raise
            # now that we've gotten past the checks, fire the events.
            if removed:
                event.notify(
                    interfaces.PrincipalsRemovedFromGroup(
                        removed, self.__parent__.__parent__.prefix + group_id))
            if added:
                event.notify(
                    interfaces.PrincipalsAddedToGroup(
                        added, self.__parent__.__parent__.prefix + group_id))

    principals = property(lambda self: self._principals, setPrincipals)


def specialGroups(event):
    principal = event.principal
    if (IGroup.providedBy(principal) or
        not IGroupAwarePrincipal.providedBy(principal)):
        return

    everyone = component.queryUtility(IEveryoneGroup)
    if everyone is not None:
        principal.groups.append(everyone.id)

    auth = component.queryUtility(IAuthenticatedGroup)
    if auth is not None:
        principal.groups.append(auth.id)


def setGroupsForPrincipal(event):
    """Set group information when a principal is created"""

    principal = event.principal
    if not IGroupAwarePrincipal.providedBy(principal):
        return

    authentication = event.authentication

    for name, plugin in authentication.getAuthenticatorPlugins():
        if not IGroupFolder.providedBy(plugin):
            continue
        groupfolder = plugin
        principal.groups.extend(
            [authentication.prefix + id
             for id in groupfolder.getGroupsForPrincipal(principal.id)
             ])
        id = principal.id
        prefix = authentication.prefix + groupfolder.prefix
        if id.startswith(prefix) and id[len(prefix):] in groupfolder:
            alsoProvides(principal, IGroup)

@component.adapter(interfaces.IFoundPrincipalCreated)
def setMemberSubscriber(event):
    """adds `getMembers`, `setMembers` to groups made from IGroupPrincipalInfo.
    """
    info = event.info
    if IGroupPrincipalInfo.providedBy(info):
        principal = event.principal
        principal.getMembers = lambda : info.members
        def setMembers(value):
            info.members = value
        principal.setMembers = setMembers
        alsoProvides(principal, IMemberAwareGroup)
