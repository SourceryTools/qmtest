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
"""Registration functional tests

$Id: tests.py 67630 2006-04-27 00:54:03Z jim $
"""

import unittest
import zope.app.testing.functional

from zope import interface

class ISampleBase(interface.Interface):
    pass

class ISample(ISampleBase):
    pass

class Sample:
    interface.implements(ISample)


def test_suite():
    return zope.app.testing.functional.FunctionalDocFileSuite(
        'registration.txt')
        
if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

