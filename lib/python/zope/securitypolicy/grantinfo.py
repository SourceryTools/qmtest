##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Grant info

$Id: grantinfo.py 80108 2007-09-26 15:02:36Z rogerineichen $
"""
from zope.annotation.interfaces import IAnnotations
from zope.securitypolicy.interfaces import Unset
from zope.securitypolicy.interfaces import IGrantInfo

from zope.securitypolicy.principalpermission import \
     AnnotationPrincipalPermissionManager
prinperkey = AnnotationPrincipalPermissionManager.key
del AnnotationPrincipalPermissionManager

from zope.securitypolicy.principalrole import \
     AnnotationPrincipalRoleManager
prinrolekey = AnnotationPrincipalRoleManager.key
del AnnotationPrincipalRoleManager

from zope.securitypolicy.rolepermission import \
     AnnotationRolePermissionManager
rolepermkey = AnnotationRolePermissionManager.key
del AnnotationRolePermissionManager

class AnnotationGrantInfo(object):

    prinper = prinrole = permrole = {}

    def __init__(self, context):
        self._context = context
        annotations = IAnnotations(context, None)
        if annotations is not None:

            prinper = annotations.get(prinperkey)
            if prinper is not None:
                self.prinper = prinper._bycol # by principals

            prinrole = annotations.get(prinrolekey)
            if prinrole is not None:
                self.prinrole = prinrole._bycol # by principals

            roleper = annotations.get(rolepermkey)
            if roleper is not None:
                self.permrole = roleper._byrow # by permission
            
    def __nonzero__(self):
        return bool(self.prinper or self.prinrole or self.permrole)

    def principalPermissionGrant(self, principal, permission):
        prinper = self.prinper.get(principal)
        if prinper:
            return prinper.get(permission, Unset)
        return Unset

    def getRolesForPermission(self, permission):
        permrole = self.permrole.get(permission)
        if permrole:
            return permrole.items()
        return ()

    def getRolesForPrincipal(self, principal):
        prinrole = self.prinrole.get(principal)
        if prinrole:
            return prinrole.items()
        return ()
