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
"""Functional tests for the site management.

$Id: ftests.py 67637 2006-04-27 12:15:56Z srichter $
"""
__docformat__ = "reStructuredText"

import unittest

from zope.testing import doctest
from zope.app.testing import functional

def test_suite():
    return unittest.TestSuite((
        functional.FunctionalDocFileSuite(
            "site.txt",
            optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE),
        ))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
