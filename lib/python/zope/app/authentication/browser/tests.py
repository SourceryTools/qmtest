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
"""Pluggable Authentication Service Tests

$Id: tests.py 29143 2005-02-14 22:43:16Z srichter $
"""
__docformat__ = "reStructuredText"
import unittest
from zope.testing import doctest
from zope.app.testing.setup import placefulSetUp, placefulTearDown


def schemaSearchSetUp(self):
    placefulSetUp(site=True)

def schemaSearchTearDown(self):
    placefulTearDown()

def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite('schemasearch.txt'),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
