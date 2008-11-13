##############################################################################
#
# Copyright (c) 2006 Lovely Systems and Contributors.
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
"""Test the Dublin Core Property implementation

$Id: test_property.py 70826 2006-10-20 03:41:16Z baijum $
"""
__docformat__ = "reStructuredText"

import doctest
import unittest

from zope import component

from zope.testing.doctestunit import DocFileSuite

from zope.app.testing import setup, placelesssetup
from zope.dublincore import annotatableadapter
from zope.dublincore import testing
from zope.dublincore.interfaces import IWriteZopeDublinCore


def setUp(test):
    setup.placefulSetUp()
    setup.setUpAnnotations()
    testing.setUpDublinCore()

def tearDown(test):
    setup.placefulTearDown()


def test_suite():

    return unittest.TestSuite(
        (
        DocFileSuite('../property.txt',
                     setUp=setUp,
                     tearDown=tearDown,
                     optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS,
                     ),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
