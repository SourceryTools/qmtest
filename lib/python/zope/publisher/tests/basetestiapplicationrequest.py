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
"""IApplicationRequest Base Test

$Id: basetestiapplicationrequest.py 38967 2005-10-08 16:27:57Z torsti $
"""
from zope.interface.verify import verifyObject
from zope.publisher.interfaces import IApplicationRequest

from zope.interface.common.tests.basemapping import BaseTestIEnumerableMapping

from zope.interface.common.tests.basemapping import testIReadMapping


class BaseTestIApplicationRequest(BaseTestIEnumerableMapping):
    def testVerifyIApplicationRequest(self):
        verifyObject(IApplicationRequest, self._Test__new())

    def testHaveCustomTestsForIApplicationRequest(self):
        # Make sure that tests are defined for things we can't test here
        self.test_IApplicationRequest_bodyStream

    def testEnvironment(self):
        request = self._Test__new(foo='Foo', bar='Bar')

        try:
            request.environment = {}
        except AttributeError:
            pass
        else:
            raise "Shouldn't be able to set environment"

        environment = request.environment

        testIReadMapping(self, environment,
                         {'foo': 'Foo', 'bar': 'Bar'},
                         ['splat'])
