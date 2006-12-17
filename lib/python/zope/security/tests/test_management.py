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
""" Unit tests for SecurityManagement

$Id: test_management.py 40098 2005-11-14 19:14:00Z poster $
"""

import unittest

from zope.interface.verify import verifyObject
from zope.testing.cleanup import CleanUp


class Test(CleanUp, unittest.TestCase):

    def test_import(self):
        from zope.security import management
        from zope.security.interfaces import ISecurityManagement
        from zope.security.interfaces import IInteractionManagement

        verifyObject(ISecurityManagement, management)
        verifyObject(IInteractionManagement, management)

    def test_securityPolicy(self):
        from zope.security.management import setSecurityPolicy
        from zope.security.management import getSecurityPolicy
        from zope.security.simplepolicies import PermissiveSecurityPolicy

        policy = PermissiveSecurityPolicy
        setSecurityPolicy(policy)
        self.assert_(getSecurityPolicy() is policy)

    def test_query_new_end_restore_Interaction(self):
        from zope.security.management import queryInteraction
        self.assertEquals(queryInteraction(), None)

        from zope.security.management import newInteraction

        newInteraction()

        interaction = queryInteraction()
        self.assert_(interaction is not None)
        self.assertRaises(AssertionError, newInteraction)

        from zope.security.management import endInteraction
        endInteraction()
        self.assertEquals(queryInteraction(), None)

        from zope.security.management import restoreInteraction
        restoreInteraction()
        self.assert_(interaction is queryInteraction())

        endInteraction()
        self.assertEquals(queryInteraction(), None)

        endInteraction()
        self.assertEquals(queryInteraction(), None)

        newInteraction()
        self.assert_(queryInteraction() is not None)
        
        restoreInteraction() # restore to no interaction
        self.assert_(queryInteraction() is None)

    def test_checkPermission(self):
        from zope.security import checkPermission
        from zope.security.management import setSecurityPolicy
        from zope.security.management import queryInteraction
        from zope.security.management import newInteraction

        permission = 'zope.Test'
        obj = object()

        class PolicyStub(object):

            def checkPermission(s, p, o,):
                self.assert_(p is permission)
                self.assert_(o is obj)
                self.assert_(s is queryInteraction() or s is interaction)
                return s is interaction

        setSecurityPolicy(PolicyStub)
        newInteraction()
        interaction = queryInteraction()
        self.assertEquals(checkPermission(permission, obj), True)

    def test_checkPublicPermission(self):
        from zope.security import checkPermission
        from zope.security.checker import CheckerPublic
        from zope.security.management import setSecurityPolicy
        from zope.security.management import newInteraction

        obj = object()

        class ForbiddenPolicyStub(object):

            def checkPermission(s, p, o):
                return False

        setSecurityPolicy(ForbiddenPolicyStub)
        newInteraction()
        self.assertEquals(checkPermission('zope.Test', obj), False)
        self.assertEquals(checkPermission(None, obj), True)
        self.assertEquals(checkPermission(CheckerPublic, obj), True)


def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(Test)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
