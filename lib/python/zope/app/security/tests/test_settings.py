##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""Security Settings Tests

$Id: test_settings.py 25177 2004-06-02 13:17:31Z jim $
"""
import unittest

from zope.app.security.settings import Allow
from cPickle import Pickler, Unpickler
from StringIO import StringIO

class Test(unittest.TestCase):

    def testPickleUnpickle(self):
        s = StringIO()
        p = Pickler(s)
        p.dump(Allow)
        s.seek(0)
        u = Unpickler(s)
        newAllow = u.load()

        self.failUnless(newAllow is Allow)

def test_suite():
    loader=unittest.TestLoader()
    return loader.loadTestsFromTestCase(Test)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
