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
"""Source Widget Tests

$Id$
"""
from zope.app.testing import placelesssetup

def test_suite():
    from zope.testing import doctest
    return doctest.DocFileSuite(
        '../source.txt',
        setUp=placelesssetup.setUp, tearDown=placelesssetup.tearDown)

if __name__ == '__main__':
    import unittest
    unittest.main(defaultTest='test_suite')

