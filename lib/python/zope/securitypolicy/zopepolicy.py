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
"""Define Zope's default security policy

$Id: zopepolicy.py 80108 2007-09-26 15:02:36Z rogerineichen $
"""

import zope.interface

from zope.security.checker import CheckerPublic
from zope.security.management import system_user
from zope.security.simplepolicies import ParanoidSecurityPolicy
from zope.security.interfaces import ISecurityPolicy
from zope.security.proxy import removeSecurityProxy

from zope.app import zapi

from zope.app.security.interfaces import PrincipalLookupError

from zope.securitypolicy.principalpermission import principalPermissionManager
globalPrincipalPermissionSetting = principalPermissionManager.getSetting

from zope.securitypolicy.rolepermission import rolePermissionManager
globalRolesForPermission = rolePermissionManager.getRolesForPermission

from zope.securitypolicy.principalrole import principalRoleManager
globalRolesForPrincipal = principalRoleManager.getRolesForPrincipal

from zope.securitypolicy.interfaces import Allow, Deny, Unset
from zope.securitypolicy.interfaces import IRolePermissionMap
from zope.securitypolicy.interfaces import IPrincipalPermissionMap
from zope.securitypolicy.interfaces import IPrincipalRoleMap
from zope.securitypolicy.interfaces import IGrantInfo

SettingAsBoolean = {Allow: True, Deny: False, Unset: None, None: None}

class CacheEntry:
    pass
        
class ZopeSecurityPolicy(ParanoidSecurityPolicy):
    zope.interface.classProvides(ISecurityPolicy)

    def __init__(self, *args, **kw):
        ParanoidSecurityPolicy.__init__(self, *args, **kw)
        self._cache = {}

    def invalidate_cache(self):
        self._cache = {}

    def cache(self, parent):
        cache = self._cache.get(id(parent))
        if cache:
            cache = cache[0]
        else:
            cache = CacheEntry()
            self._cache[id(parent)] = cache, parent
        return cache
    
    def cached_decision(self, parent, principal, groups, permission):
        # Return the decision for a principal and permission

        cache = self.cache(parent)
        try:
            cache_decision = cache.decision
        except AttributeError:
            cache_decision = cache.decision = {}

        cache_decision_prin = cache_decision.get(principal)
        if not cache_decision_prin:
            cache_decision_prin = cache_decision[principal] = {}
            
        try:
            return cache_decision_prin[permission]
        except KeyError:
            pass

        # cache_decision_prin[permission] is the cached decision for a
        # principal and permission.
            
        decision = self.cached_prinper(parent, principal, groups, permission)
        if (decision is None) and groups:
            decision = self._group_based_cashed_prinper(parent, principal,
                                                        groups, permission)
        if decision is not None:
            cache_decision_prin[permission] = decision
            return decision

        roles = self.cached_roles(parent, permission)
        if roles:
            prin_roles = self.cached_principal_roles(parent, principal)
            if groups:
                prin_roles = self.cached_principal_roles_w_groups(
                    parent, principal, groups, prin_roles)
            for role, setting in prin_roles.items():
                if setting and (role in roles):
                    cache_decision_prin[permission] = decision = True
                    return decision

        cache_decision_prin[permission] = decision = False
        return decision
        
    def cached_prinper(self, parent, principal, groups, permission):
        # Compute the permission, if any, for the principal.
        cache = self.cache(parent)
        try:
            cache_prin = cache.prin
        except AttributeError:
            cache_prin = cache.prin = {}

        cache_prin_per = cache_prin.get(principal)
        if not cache_prin_per:
            cache_prin_per = cache_prin[principal] = {}

        try:
            return cache_prin_per[permission]
        except KeyError:
            pass

        if parent is None:
            prinper = SettingAsBoolean[
                globalPrincipalPermissionSetting(permission, principal, None)
                ]
            cache_prin_per[permission] = prinper
            return prinper

        prinper = IPrincipalPermissionMap(parent, None)
        if prinper is not None:
            prinper = SettingAsBoolean[
                prinper.getSetting(permission, principal, None)
                ]
            if prinper is not None:
                cache_prin_per[permission] = prinper
                return prinper

        parent = removeSecurityProxy(getattr(parent, '__parent__', None))
        prinper = self.cached_prinper(parent, principal, groups, permission)
        cache_prin_per[permission] = prinper
        return prinper

    def _group_based_cashed_prinper(self, parent, principal, groups,
                                    permission):
        denied = False
        for group_id, ggroups in groups:
            decision = self.cached_prinper(parent, group_id, ggroups,
                                           permission)
            if (decision is None) and ggroups:
                decision = self._group_based_cashed_prinper(
                    parent, group_id, ggroups, permission)
            
            if decision is None:
                continue
            
            if decision:
                return decision

            denied = True

        if denied:
            return False

        return None
        
    def cached_roles(self, parent, permission):
        cache = self.cache(parent)
        try:
            cache_roles = cache.roles
        except AttributeError:
            cache_roles = cache.roles = {}
        try:
            return cache_roles[permission]
        except KeyError:
            pass
        
        if parent is None:
            roles = dict(
                [(role, 1)
                 for (role, setting) in globalRolesForPermission(permission)
                 if setting is Allow
                 ]
               )
            cache_roles[permission] = roles
            return roles

        roles = self.cached_roles(
            removeSecurityProxy(getattr(parent, '__parent__', None)),
            permission)
        roleper = IRolePermissionMap(parent, None)
        if roleper:
            roles = roles.copy()
            for role, setting in roleper.getRolesForPermission(permission):
                if setting is Allow:
                    roles[role] = 1
                elif role in roles:
                    del roles[role]

        cache_roles[permission] = roles
        return roles

    def cached_principal_roles_w_groups(self, parent,
                                        principal, groups, prin_roles):
        denied = {}
        allowed = {}
        for group_id, ggroups in groups:
            group_roles = dict(self.cached_principal_roles(parent, group_id))
            if ggroups:
                group_roles = self.cached_principal_roles_w_groups(
                    parent, group_id, ggroups, group_roles)
            for role, setting in group_roles.items():
                if setting:
                    allowed[role] = setting
                else:
                    denied[role] = setting

        denied.update(allowed)
        denied.update(prin_roles)
        return denied

    def cached_principal_roles(self, parent, principal):
        cache = self.cache(parent)
        try:
            cache_principal_roles = cache.principal_roles
        except AttributeError:
            cache_principal_roles = cache.principal_roles = {}
        try:
            return cache_principal_roles[principal]
        except KeyError:
            pass

        if parent is None:
            roles = dict(
                [(role, SettingAsBoolean[setting])
                 for (role, setting) in globalRolesForPrincipal(principal)
                 ]
                 )
            roles['zope.Anonymous'] = True # Everybody has Anonymous
            cache_principal_roles[principal] = roles
            return roles
            
        roles = self.cached_principal_roles(
            removeSecurityProxy(getattr(parent, '__parent__', None)),
            principal)

        prinrole = IPrincipalRoleMap(parent, None)
        if prinrole:
            roles = roles.copy()
            for role, setting in prinrole.getRolesForPrincipal(principal):
                roles[role] = SettingAsBoolean[setting]

        cache_principal_roles[principal] = roles
        return roles

    def checkPermission(self, permission, object):
        if permission is CheckerPublic:
            return True

        object = removeSecurityProxy(object)
        seen = {}
        for participation in self.participations:
            principal = participation.principal
            if principal is system_user:
                continue # always allow system_user

            if principal.id in seen:
                continue

            if not self.cached_decision(
                object, principal.id, self._groupsFor(principal), permission,
                ):
                return False

            seen[principal.id] = 1

        return True

    def _findGroupsFor(self, principal, getPrincipal, seen):
        result = []
        for group_id in getattr(principal, 'groups', ()):
            if group_id in seen:
                # Dang, we have a cycle.  We don't want to
                # raise an exception here (or do we), so we'll skip it
                continue
            seen.append(group_id)
            
            try:
                group = getPrincipal(group_id)
            except PrincipalLookupError:
                # It's bad if we have an undefined principal,
                # but we don't want to fail here.  But we won't
                # honor any grants for the group. We'll just skip it.
                continue

            result.append((group_id,
                           self._findGroupsFor(group, getPrincipal, seen)))
            seen.pop()
            
        return tuple(result)

    def _groupsFor(self, principal):
        groups = self._cache.get(principal.id)
        if groups is None:
            groups = getattr(principal, 'groups', ())
            if groups:
                getPrincipal = zapi.principals().getPrincipal
                groups = self._findGroupsFor(principal, getPrincipal, [])
            else:
                groups = ()

            self._cache[principal.id] = groups

        return groups

def settingsForObject(ob):
    """Analysis tool to show all of the grants to a process
    """
    result = []
    while ob is not None:
        data = {}
        result.append((getattr(ob, '__name__', '(no name)'), data))
        
        principalPermissions = IPrincipalPermissionMap(ob, None)
        if principalPermissions is not None:
            settings = principalPermissions.getPrincipalsAndPermissions()
            settings.sort()
            data['principalPermissions'] = [
                {'principal': pr, 'permission': p, 'setting': s}
                for (p, pr, s) in settings]

        principalRoles = IPrincipalRoleMap(ob, None)
        if principalRoles is not None:
            settings = principalRoles.getPrincipalsAndRoles()
            data['principalRoles'] = [
                {'principal': p, 'role': r, 'setting': s}
                for (r, p, s) in settings]

        rolePermissions = IRolePermissionMap(ob, None)
        if rolePermissions is not None:
            settings = rolePermissions.getRolesAndPermissions()
            data['rolePermissions'] = [
                {'permission': p, 'role': r, 'setting': s}
                for (p, r, s) in settings]
                
        ob = getattr(ob, '__parent__', None)

    data = {}
    result.append(('global settings', data))

    settings = principalPermissionManager.getPrincipalsAndPermissions()
    settings.sort()
    data['principalPermissions'] = [
        {'principal': pr, 'permission': p, 'setting': s}
        for (p, pr, s) in settings]

    settings = principalRoleManager.getPrincipalsAndRoles()
    data['principalRoles'] = [
        {'principal': p, 'role': r, 'setting': s}
        for (r, p, s) in settings]

    settings = rolePermissionManager.getRolesAndPermissions()
    data['rolePermissions'] = [
        {'permission': p, 'role': r, 'setting': s}
        for (p, r, s) in settings]

    return result

