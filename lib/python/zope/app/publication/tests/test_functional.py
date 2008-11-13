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
"""Test not found errors

$Id: test_functional.py 75790 2007-05-16 04:53:12Z hdima $
"""

import re
import unittest
from zope.testing import renormalizing
from zope.app.testing import functional
from zope.app.publication.testing import PublicationLayer


checker = renormalizing.RENormalizing([
    (re.compile(r"HTTP/1\.([01]) (\d\d\d) .*"), r"HTTP/1.\1 \2 <MESSAGE>"),
    ])


def test_suite():
    notfound = functional.FunctionalDocFileSuite('../notfound.txt')
    notfound.layer = PublicationLayer
    methodnotallowed = functional.FunctionalDocFileSuite(
        '../methodnotallowed.txt')
    methodnotallowed.layer = PublicationLayer
    httpfactory = functional.FunctionalDocFileSuite(
        '../httpfactory.txt', checker=checker)
    httpfactory.layer = PublicationLayer
    return unittest.TestSuite((
        notfound,
        methodnotallowed,
        httpfactory,
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

