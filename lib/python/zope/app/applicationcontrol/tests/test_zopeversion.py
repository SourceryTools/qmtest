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

$Id: test_zopeversion.py 41452 2006-01-26 14:57:18Z hdima $
"""
import os
import shutil
import tempfile
import unittest
from xml.sax.saxutils import quoteattr

from zope.interface.verify import verifyObject
from zope.app.applicationcontrol.interfaces import IZopeVersion
from zope.app.applicationcontrol.zopeversion import ZopeVersion


class Test(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="test-zopeversion-")

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def prepare(self, version, fields):
        if version:
            f = open(os.path.join(self.tmpdir, "version.txt"), "w")
            f.write(version)
            if not version.endswith("\n"):
                f.write("\n")
            f.close()
        if fields:
            os.mkdir(os.path.join(self.tmpdir, ".svn"))
            f = open(os.path.join(self.tmpdir, ".svn", "entries"), "w")
            fields = ["%s=%s" % (key, quoteattr(val))
                      for key, val in fields.items()]
            text = ('<?xml version="1.0" encoding="utf-8"?>\n'
                    '<wc-entries\n'
                    '   xmlns="svn:">\n'
                    '<entry\n'
                    '   name=""\n'
                    '   kind="dir"\n'
                    '   %s/>\n'
                    '</wc-entries>\n' % "\n   ".join(fields))
            f.write(text)
            f.close()

    def _Test__new(self):
        return ZopeVersion(self.tmpdir)

    def test_IVerify(self):
        verifyObject(IZopeVersion, self._Test__new())

    # In .svn/entries we check only two attributes:
    #   'url' - repository path
    #   'revision' - checked out revision number

    def test_ZopeVersion(self):
        self.prepare(None, None)
        zope_version = self._Test__new()
        self.assertEqual(zope_version.getZopeVersion(), "Development/Unknown")

    def test_ZopeVersion_svntrunk(self):
        self.prepare(None, {
            "url": "svn+ssh://svn.zope.org/repos/main/Zope3/trunk/src/zope",
            "revision": "10000"
            })
        zope_version = self._Test__new()
        self.assertEqual(zope_version.getZopeVersion(),
                        "Development/Revision: 10000")

    def test_ZopeVersion_svnbranch(self):
        self.prepare(None, {
            "url": "svn+ssh://svn.zope.org/repos/main/Zope3/branches/Zope3-1.0/src/zope",
            "revision": "10000"
            })
        zope_version = self._Test__new()
        self.assertEqual(zope_version.getZopeVersion(),
                        "Development/Revision: 10000/Branch: Zope3-1.0")

    def test_ZopeVersion_svntag(self):
        self.prepare(None, {
            "url": "svn+ssh://svn.zope.org/repos/main/Zope3/tags/Zope3-1.0/src/zope",
            "revision": "10000"
            })
        zope_version = self._Test__new()
        self.assertEqual(zope_version.getZopeVersion(),
                        "Development/Revision: 10000/Tag: Zope3-1.0")

    def test_ZopeVersion_svn_unknown(self):
        self.prepare(None, {"uuid": ""})
        zope_version = self._Test__new()
        self.assertEqual(zope_version.getZopeVersion(), "Development/Unknown")

    def test_ZopeVersion_release(self):
        self.prepare("Zope 3 1.0.0", None)
        zope_version = self._Test__new()
        self.assertEqual(zope_version.getZopeVersion(),
                         "Zope 3 1.0.0")

    def test_ZopeVersion_release_empty(self):
        self.prepare(" ", None)
        zope_version = self._Test__new()
        self.assertEqual(zope_version.getZopeVersion(), "Development/Unknown")

    def test_ZopeVersion_release_svntrunk(self):
        # demonstrate that the version.txt data is discarded if
        # there's revision-control metadata:
        self.prepare("Zope 3 1.0.0", {
            "url": "svn+ssh://svn.zope.org/repos/main/Zope3/trunk/src/zope",
            "revision": "10000"
            })
        zope_version = self._Test__new()
        self.assertEqual(zope_version.getZopeVersion(),
                        "Development/Revision: 10000")


def test_suite():
    return unittest.makeSuite(Test)

if __name__ == '__main__':
    unittest.main(defaultTest="test_suite")
