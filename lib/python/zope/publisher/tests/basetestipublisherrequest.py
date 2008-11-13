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
"""IPublisherReuqest Test

$Id: basetestipublisherrequest.py 26559 2004-07-15 21:22:32Z srichter $
"""

from zope.interface.verify import verifyObject
from zope.publisher.interfaces import IPublisherRequest


class BaseTestIPublisherRequest(object):
    def testVerifyIPublisherRequest(self):
        verifyObject(IPublisherRequest, self._Test__new())

    def testHaveCustomTestsForIPublisherRequest(self):
        # Make sure that tests are defined for things we can't test here
        self.test_IPublisherRequest_retry
        self.test_IPublisherRequest_traverse
        self.test_IPublisherRequest_processInputs

    def testPublicationManagement(self):
        from zope.publisher.tests.publication import TestPublication

        request = self._Test__new()
        publication = TestPublication()
        request.setPublication(publication)
        self.assertEqual(id(request.publication), id(publication))
