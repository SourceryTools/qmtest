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
"""Zope Version Tests

$Id: test_zopeversion.py 70397 2006-09-27 13:32:51Z hdima $
"""
import os
import shutil
import tempfile
import unittest

from zope.interface.verify import verifyObject
from zope.app.applicationcontrol.interfaces import IZopeVersion
from zope.app.applicationcontrol.zopeversion import ZopeVersion


class MockZopeVersion(ZopeVersion):

    def setSVNInfoOutput(self, lines):
        self.__lines = lines

    def _getSVNInfoOutput(self):
        return self.__lines

class Test(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="test-zopeversion-")
        self.zopeVersion = MockZopeVersion(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def prepare(self, version, fields):
        if version:
            f = open(os.path.join(self.tmpdir, "version.txt"), "w")
            try:
                f.write(version)
                if not version.endswith("\n"):
                    f.write("\n")
            finally:
                f.close()
        if fields:
            os.mkdir(os.path.join(self.tmpdir, ".svn"))
            self.zopeVersion.setSVNInfoOutput(fields)

    def test_IVerify(self):
        verifyObject(IZopeVersion, self.zopeVersion)

    def test_ZopeVersion(self):
        self.prepare(None, None)
        self.assertEqual(self.zopeVersion.getZopeVersion(),
            "Development/Unknown")

    def test_ZopeVersion_svntrunk(self):
        self.prepare(None, [
            "URL: svn+ssh://svn.zope.org/repos/main/Zope3/trunk/src/zope",
            "Revision: 10000"
            ])
        self.assertEqual(self.zopeVersion.getZopeVersion(),
            "Development/Revision: 10000")

    def test_ZopeVersion_svnbranch(self):
        self.prepare(None, [
            "URL: svn+ssh://svn.zope.org/repos/main/Zope3/branches/Zope3-1.0/src/zope",
            "Revision: 10000"
            ])
        self.assertEqual(self.zopeVersion.getZopeVersion(),
            "Development/Revision: 10000/Branch: Zope3-1.0")

    def test_ZopeVersion_svntag(self):
        self.prepare(None, [
            "URL: svn+ssh://svn.zope.org/repos/main/Zope3/tags/Zope3-1.0/src/zope",
            "Revision: 10000"
            ])
        self.assertEqual(self.zopeVersion.getZopeVersion(),
            "Development/Revision: 10000/Tag: Zope3-1.0")

    def test_ZopeVersion_svn_unknown(self):
        self.prepare(None, ["Nope: "])
        self.assertEqual(self.zopeVersion.getZopeVersion(),
            "Development/Unknown")

    def test_ZopeVersion_release(self):
        self.prepare("Zope 3 1.0.0", None)
        self.assertEqual(self.zopeVersion.getZopeVersion(),
            "Zope 3 1.0.0")

    def test_ZopeVersion_release_empty(self):
        self.prepare(" ", None)
        self.assertEqual(self.zopeVersion.getZopeVersion(),
            "Development/Unknown")

    def test_ZopeVersion_release_svntrunk(self):
        # demonstrate that the version.txt data is discarded if
        # there's revision-control metadata:
        self.prepare("Zope 3 1.0.0", [
            "URL: svn+ssh://svn.zope.org/repos/main/Zope3/trunk/src/zope",
            "Revision: 10000"
            ])
        self.assertEqual(self.zopeVersion.getZopeVersion(),
            "Development/Revision: 10000")


def test_suite():
    return unittest.makeSuite(Test)

if __name__ == '__main__':
    unittest.main(defaultTest="test_suite")
