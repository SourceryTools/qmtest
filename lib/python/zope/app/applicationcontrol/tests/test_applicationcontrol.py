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
##############################################################################
"""Application Control Tests

$Id: test_applicationcontrol.py 25177 2004-06-02 13:17:31Z jim $
"""
import unittest
from zope.interface.verify import verifyObject

import time
from zope.app.applicationcontrol.applicationcontrol import ApplicationControl
from zope.app.applicationcontrol.interfaces import IApplicationControl

# seconds, time values may differ in order to be assumed equal
time_tolerance = 2

class Test(unittest.TestCase):

    def _Test__new(self):
        return ApplicationControl()

    def test_IVerify(self):
        verifyObject(IApplicationControl, self._Test__new())

    def test_startTime(self):
        assert_time = time.time()
        test_time = self._Test__new().getStartTime()

        self.failUnless(abs(assert_time - test_time) < time_tolerance)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(Test),
        ))

if __name__ == '__main__':
    unittest.main()
