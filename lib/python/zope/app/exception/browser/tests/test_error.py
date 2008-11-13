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
"""Functional tests for NotFoundError

$Id: test_error.py 73711 2007-03-27 10:50:23Z dobe $
"""
import unittest
from zope.app.testing import functional
from zope.component.interfaces import ComponentLookupError
from zope.app.exception.testing import AppExceptionLayer

class RaiseComponentLookupError(object):

    def __call__(self):
        raise ComponentLookupError()


class TestComponentLookupError(functional.BrowserTestCase):

    def testComponentLookupError(self):
        response = self.publish('/foobar', basic='mgr:mgrpw',
                                handle_errors=True)
        self.assertEqual(response.getStatus(), 404)
        body = response.getBody()
        self.assert_(
            'The page that you are trying to access is not available' in body)


def test_suite():
    TestComponentLookupError.layer = AppExceptionLayer
    systemerror = functional.FunctionalDocFileSuite('../systemerror.txt')
    systemerror.layer = AppExceptionLayer
    return unittest.TestSuite((
        unittest.makeSuite(TestComponentLookupError),
        systemerror,
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
