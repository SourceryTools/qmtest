##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Example Zope doctest

$Id: testZopeDocTest.py 76989 2007-06-23 17:08:16Z shh $
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from unittest import TestSuite
from Testing.ZopeTestCase import ZopeDocTestSuite
from Testing.ZopeTestCase import ZopeDocFileSuite


def setUp(self):
    '''This method will run after the test_class' setUp.

    >>> 'object' in folder.objectIds()
    True

    >>> foo
    1
    '''
    self.folder.manage_addFolder('object', '')
    self.globs['foo'] = 1


def test_suite():
    return TestSuite((
        ZopeDocTestSuite(setUp=setUp),
        ZopeDocFileSuite('ZopeDocTest.txt', setUp=setUp),
    ))

if __name__ == '__main__':
    framework()

