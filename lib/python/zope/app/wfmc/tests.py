##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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
"""WFMC Tests Setup

$Id$
"""
__docformat__ = "reStructuredText"
import os
import unittest

from zope.configuration import xmlconfig
from zope.testing import module, doctest

import zope.app.wfmc
from zope.app.testing import placelesssetup
from zope.app.testing import ztapi

def zcml(s):
    context = xmlconfig.file('meta.zcml', package=zope.app.wfmc)
    xmlconfig.string(s, context)

def setUp(test):
    test.globs['this_directory'] = os.path.dirname(__file__)
    placelesssetup.setUp(test)

def test_suite():
    return doctest.DocFileSuite(
                'zcml.txt', globs={'zcml': zcml},
                setUp=setUp,
                tearDown=placelesssetup.tearDown,
                optionflags=doctest.NORMALIZE_WHITESPACE,
           )

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
