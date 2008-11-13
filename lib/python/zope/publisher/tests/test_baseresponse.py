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
"""Tests for BaseResponse

$Id: test_baseresponse.py 38357 2005-09-07 20:14:34Z srichter $
"""

from unittest import TestCase, TestSuite, main, makeSuite
from zope.publisher.base import BaseResponse
from zope.publisher.interfaces import IResponse
from zope.interface.verify import verifyObject
from StringIO import StringIO


class TestBaseResponse(TestCase):

    def test_interface(self):
        verifyObject(IResponse, BaseResponse())


def test_suite():
    return TestSuite((
        makeSuite(TestBaseResponse),
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')
