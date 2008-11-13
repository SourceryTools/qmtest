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
"""Unit tests for zope.thread.

$Id: tests.py 26023 2004-07-01 19:05:30Z jim $
"""

def test_suite():
    import unittest
    from doctest import DocTestSuite
    suite = unittest.TestSuite()
    suite.addTest(DocTestSuite('zope.thread'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

