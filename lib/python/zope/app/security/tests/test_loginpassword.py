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
"""Test Login and Password

$Id: test_loginpassword.py 39687 2005-10-28 10:14:24Z hdima $
"""
import unittest

from zope.app.security.loginpassword import LoginPassword

class Test(unittest.TestCase):

    def testLoginPassword(self):
        lp = LoginPassword("tim", "123")
        self.assertEqual(lp.getLogin(), "tim")
        self.assertEqual(lp.getPassword(), "123")
        lp = LoginPassword(None, None)
        self.assertEqual(lp.getLogin(), None)
        self.assertEqual(lp.getPassword(), None)
        lp = LoginPassword(None, "123")
        self.assertEqual(lp.getLogin(), None)
        self.assertEqual(lp.getPassword(), None)
        lp = LoginPassword("tim", None)
        self.assertEqual(lp.getLogin(), "tim")
        self.assertEqual(lp.getPassword(), "")
        lp.needLogin("tim") # This method should exist

def test_suite():
    loader=unittest.TestLoader()
    return loader.loadTestsFromTestCase(Test)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
