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
"""Unit tests for zope.security.simpleinteraction.

$Id: test_simpleinteraction.py 70826 2006-10-20 03:41:16Z baijum $
"""
import unittest

from zope.interface.verify import verifyObject
from zope.security.interfaces import IInteraction
from zope.security.simplepolicies import ParanoidSecurityPolicy

class RequestStub(object):

    def __init__(self, principal=None):
        self.principal = principal
        self.interaction = None


class TestInteraction(unittest.TestCase):

    def test(self):
        interaction = ParanoidSecurityPolicy()
        verifyObject(IInteraction, interaction)

    def test_add(self):
        rq = RequestStub()
        interaction = ParanoidSecurityPolicy()
        interaction.add(rq)
        self.assert_(rq in interaction.participations)
        self.assert_(rq.interaction is interaction)

        # rq already added
        self.assertRaises(ValueError, interaction.add, rq)

        interaction2 = ParanoidSecurityPolicy()
        self.assertRaises(ValueError, interaction2.add, rq)

    def test_remove(self):
        rq = RequestStub()
        interaction = ParanoidSecurityPolicy()

        self.assertRaises(ValueError, interaction.remove, rq)

        interaction.add(rq)

        interaction.remove(rq)
        self.assert_(rq not in interaction.participations)
        self.assert_(rq.interaction is None)

    def testCreateInteraction(self):
        i1 = ParanoidSecurityPolicy()
        verifyObject(IInteraction, i1)
        self.assertEquals(list(i1.participations), [])

        user = object()
        request = RequestStub(user)
        i2 = ParanoidSecurityPolicy(request)
        verifyObject(IInteraction, i2)
        self.assertEquals(list(i2.participations), [request])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestInteraction))
    return suite


if __name__ == '__main__':
    unittest.main()
