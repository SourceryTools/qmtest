##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Object Interface Vocabulary Tests

$Id: test_vocabulary.py 29143 2005-02-14 22:43:16Z srichter $
"""
import unittest
from zope.testing.doctestunit import DocTestSuite
from zope.app.testing import setup

def test_suite():
    return DocTestSuite('zope.app.interface.vocabulary',
                        setUp=setup.placelessSetUp,
                        tearDown=setup.placelessTearDown)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
