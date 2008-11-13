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
"""Role Permission View Classes

$Id: rolepermissionview.py 80149 2007-09-26 22:00:18Z rogerineichen $
"""
from datetime import datetime

from zope.i18n import translate
from zope.interface import implements
from zope.exceptions.interfaces import UserError
from zope.i18nmessageid import ZopeMessageFactory as _

from zope.app import zapi
from zope.app.security.interfaces import IPermission
from zope.securitypolicy.interfaces import Unset, Allow, Deny
from zope.securitypolicy.interfaces import IRole, IRolePermissionManager

class RolePermissionView(object):

    _pagetip = _("""For each permission you want to grant (or deny) to a role,
        set the entry for that permission and role to a '+' (or '-').
        Permissions are shown on the left side, going down.
        Roles are shown accross the top.
        """)

    def pagetip(self):
        return translate(self._pagetip, context=self.request)

    def roles(self):
        roles = getattr(self, '_roles', None)
        if roles is None:
            roles = [
                (translate(role.title, context=self.request).strip(), role)
                for name, role in zapi.getUtilitiesFor(IRole)]
            roles.sort()
            roles = self._roles = [role for name, role in roles]
        return roles

    def permissions(self):
        permissions = getattr(self, '_permissions', None)
        if permissions is None:
            permissions = [
                (translate(perm.title, context=self.request).strip(), perm)
                for name, perm in zapi.getUtilitiesFor(IPermission)
                if name != 'zope.Public']
            permissions.sort()
            permissions = self._permissions = [perm
                                               for name, perm in permissions]

        return permissions

    def availableSettings(self, noacquire=False):
        aq = {'id': Unset.getName(), 'shorttitle': ' ',
              'title': _('permission-acquire', 'Acquire')}
        rest = [{'id': Allow.getName(), 'shorttitle': '+',
                 'title': _('permission-allow', 'Allow')},
                {'id': Deny.getName(), 'shorttitle': '-',
                 'title': _('permission-deny', 'Deny')},
                ]
        if noacquire:
            return rest
        else:
            return [aq]+rest

    def permissionRoles(self):
        context = self.context.__parent__
        roles = self.roles()
        return [PermissionRoles(permission, context, roles)
                for permission in self.permissions()]

    def permissionForID(self, pid):
        roles = self.roles()
        perm = zapi.getUtility(IPermission, pid)
        return PermissionRoles(perm, self.context.__parent__, roles)

    def roleForID(self, rid):
        permissions = self.permissions()
        role = zapi.getUtility(IRole, rid)
        return RolePermissions(role, self.context.__parent__, permissions)


    def update(self, testing=None):
        status = ''
        changed = False

        if 'SUBMIT' in self.request:
            roles       = [r.id for r in self.roles()]
            permissions = [p.id for p in self.permissions()]
            prm         = IRolePermissionManager(self.context.__parent__)
            for ip in range(len(permissions)):
                rperm = self.request.get("p%s" % ip)
                if rperm not in permissions: continue
                for ir in range(len(roles)):
                    rrole = self.request.get("r%s" % ir)
                    if rrole not in roles: continue
                    setting = self.request.get("p%sr%s" % (ip, ir), None)
                    if setting is not None:
                        if setting == Unset.getName():
                            prm.unsetPermissionFromRole(rperm, rrole)
                        elif setting == Allow.getName():
                            prm.grantPermissionToRole(rperm, rrole)
                        elif setting == Deny.getName():
                            prm.denyPermissionToRole(rperm, rrole)
                        else:
                            raise ValueError("Incorrect setting: %s" % setting)
            changed = True

        if 'SUBMIT_PERMS' in self.request:
            prm = IRolePermissionManager(self.context.__parent__)
            roles = self.roles()
            rperm = self.request.get('permission_id')
            settings = self.request.get('settings', ())
            for ir in range(len(roles)):
                rrole = roles[ir].id
                setting = settings[ir]
                if setting == Unset.getName():
                    prm.unsetPermissionFromRole(rperm, rrole)
                elif setting == Allow.getName():
                    prm.grantPermissionToRole(rperm, rrole)
                elif setting == Deny.getName():
                    prm.denyPermissionToRole(rperm, rrole)
                else:
                    raise ValueError("Incorrect setting: %s" % setting)
            changed = True

        if 'SUBMIT_ROLE' in self.request:
            role_id = self.request.get('role_id')
            prm = IRolePermissionManager(self.context.__parent__)
            allowed = self.request.get(Allow.getName(), ())
            denied = self.request.get(Deny.getName(), ())
            for permission in self.permissions():
                rperm = permission.id
                if rperm in allowed and rperm in denied:
                    permission_translated = translate(
                        permission.title, context=self.request)
                    msg = _('You choose both allow and deny for permission'
                            ' "${permission}". This is not allowed.',
                            mapping = {'permission': permission_translated})
                    raise UserError(msg)
                if rperm in allowed:
                    prm.grantPermissionToRole(rperm, role_id)
                elif rperm in denied:
                    prm.denyPermissionToRole(rperm, role_id)
                else:
                    prm.unsetPermissionFromRole(rperm, role_id)
            changed = True

        if changed:
            formatter = self.request.locale.dates.getFormatter(
                'dateTime', 'medium')
            status = _("Settings changed at ${date_time}",
                       mapping={'date_time':
                                formatter.format(datetime.utcnow())})

        return status


class PermissionRoles(object):

    implements(IPermission)

    def __init__(self, permission, context, roles):
        self._permission = permission
        self._context    = context
        self._roles      = roles

    def _getId(self):
        return self._permission.id

    id = property(_getId)

    def _getTitle(self):
        return self._permission.title

    title = property(_getTitle)

    def _getDescription(self):
        return self._permission.description

    description = property(_getDescription)

    def roleSettings(self):
        """
        Returns the list of setting names of each role for this permission.
        """
        prm = IRolePermissionManager(self._context)
        proles = prm.getRolesForPermission(self._permission.id)
        settings = {}
        for role, setting in proles:
            settings[role] = setting.getName()
        nosetting = Unset.getName()
        return [settings.get(role.id, nosetting) for role in self._roles]

class RolePermissions(object):

    implements(IRole)

    def __init__(self, role, context, permissions):
        self._role = role
        self._context = context
        self._permissions = permissions

    def _getId(self):
        return self._role.id

    id = property(_getId)

    def _getTitle(self):
        return self._role.title

    title = property(_getTitle)

    def _getDescription(self):
        return self._role.description

    description = property(_getDescription)

    def permissionsInfo(self):
        prm = IRolePermissionManager(self._context)
        rperms = prm.getPermissionsForRole(self._role.id)
        settings = {}
        for permission, setting in rperms:
            settings[permission] = setting.getName()
        nosetting = Unset.getName()
        return [{'id': permission.id,
                 'title': permission.title,
                 'setting': settings.get(permission.id, nosetting)}
                for permission in self._permissions]
