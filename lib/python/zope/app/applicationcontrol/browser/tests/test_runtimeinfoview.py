##############################################################################
#
# Copyright (c) 2001, 2002, 2003 Zope Corporation and Contributors.
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
"""Runtime View tests

$Id: test_runtimeinfoview.py 29842 2005-04-02 19:16:09Z hdima $
"""
import unittest
from types import DictType
from zope.app.testing import ztapi

from zope.app.applicationcontrol.applicationcontrol import applicationController
from zope.app.applicationcontrol.runtimeinfo import RuntimeInfo
from zope.app.applicationcontrol.browser.runtimeinfo import RuntimeInfoView
from zope.app.applicationcontrol.interfaces import \
     IApplicationControl, IRuntimeInfo
from zope.app.component.testing import PlacefulSetup

class Test(PlacefulSetup, unittest.TestCase):

    def _TestView__newView(self, container):
        view = RuntimeInfoView()
        view.context = container
        view.request = None
        return view

    def test_RuntimeInfoView(self):
        ztapi.provideAdapter(IApplicationControl, IRuntimeInfo, RuntimeInfo)
        test_runtimeinfoview = self._TestView__newView(applicationController)

        test_format = test_runtimeinfoview.runtimeInfo()
        self.failUnless(isinstance(test_format, DictType))

        assert_keys = ['ZopeVersion', 'PythonVersion', 'PythonPath',
              'SystemPlatform', 'PreferredEncoding', 'FileSystemEncoding',
              'CommandLine', 'ProcessId', 'Uptime' ]
        test_keys = test_format.keys()

        assert_keys.sort()
        test_keys.sort()
        self.failUnlessEqual(assert_keys, test_keys)

        self.failUnlessEqual("Unavailable", test_format["ZopeVersion"])

    def test_RuntimeInfoFailureView(self):
        test_runtimeinfoview = self._TestView__newView(applicationController)

        test_format = test_runtimeinfoview.runtimeInfo()
        self.failUnless(isinstance(test_format, DictType))

        assert_keys = ['ZopeVersion', 'PythonVersion', 'PythonPath',
              'SystemPlatform', 'PreferredEncoding', 'FileSystemEncoding',
              'CommandLine', 'ProcessId', 'Uptime']
        test_keys = test_format.keys()

        assert_keys.sort()
        test_keys.sort()
        self.failUnlessEqual(assert_keys, test_keys)

        for key in assert_keys:
            self.failUnlessEqual("Unavailable", test_format[key])


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(Test),
        ))

if __name__ == '__main__':
    unittest.main()
