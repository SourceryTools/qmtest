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
"""Test handler for Annotation Role Permission Manager.

$Id: test_annotationrolepermissionmanager.py 80107 2007-09-26 14:58:39Z rogerineichen $
"""
import unittest
from zope.interface import implements
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.security.interfaces import IPermission
from zope.security.permission import Permission

from zope.app.testing import ztapi
from zope.app.component.testing import PlacefulSetup

from zope.securitypolicy.role import Role
from zope.securitypolicy.interfaces import Allow, Deny
from zope.securitypolicy.interfaces import IRole
from zope.securitypolicy.rolepermission import AnnotationRolePermissionManager

class Manageable(object):
    implements(IAttributeAnnotatable)

class Test(PlacefulSetup, unittest.TestCase):

    def setUp(self):
        PlacefulSetup.setUp(self)

        read = Permission('read', 'Read Something')
        ztapi.provideUtility(IPermission, read, name=read.id)        
        self.read = read.id

        write = Permission('write', 'Write Something')
        ztapi.provideUtility(IPermission, write, name=write.id)        
        self.write = write.id

        peon = Role('peon', 'Poor Slob')
        ztapi.provideUtility(IRole, peon, name=peon.id)        
        self.peon = peon.id

        manager = Role('manager', 'Supreme Being')
        ztapi.provideUtility(IRole, manager, name=manager.id)        
        self.manager = manager.id

    def testNormal(self):
        obj = Manageable()
        mgr = AnnotationRolePermissionManager(obj)
        mgr.grantPermissionToRole(self.read,self.manager)
        mgr.grantPermissionToRole(self.write,self.manager)
        mgr.grantPermissionToRole(self.write,self.manager)

        mgr.grantPermissionToRole(self.read,self.peon)

        l = list(mgr.getPermissionsForRole(self.manager))
        self.failUnless((self.read, Allow) in l)
        self.failUnless((self.write, Allow) in l)

        l = list(mgr.getPermissionsForRole(self.peon))
        self.failUnless([(self.read, Allow)] == l)

        l = list(mgr.getRolesForPermission(self.read))
        self.failUnless((self.manager, Allow) in l)
        self.failUnless((self.peon, Allow) in l)

        l = list(mgr.getRolesForPermission(self.write))
        self.assertEqual(l, [(self.manager, Allow)])

        mgr.denyPermissionToRole(self.read, self.peon)
        l = list(mgr.getPermissionsForRole(self.peon))
        self.assertEqual(l, [(self.read, Deny)])

        mgr.unsetPermissionFromRole(self.read, self.peon)

        l = list(mgr.getRolesForPermission(self.read))
        self.assertEqual(l, [(self.manager, Allow)])


def test_suite():
    loader=unittest.TestLoader()
    return loader.loadTestsFromTestCase(Test)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
