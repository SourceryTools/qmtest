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
"""Container View Permissions Tests

$Id: $
"""
import unittest
import transaction

from zope.security.interfaces import Unauthorized

from zope.app.testing.functional import BrowserTestCase
from zope.app.file import File
from zope.dublincore.interfaces import IZopeDublinCore
from zope.app.securitypolicy.interfaces import IRolePermissionManager


class Tests(BrowserTestCase):

    def test_default_view_permissions(self):
        """Tests the default view permissions.

        See zope/app/securitypolicy/configure.zcml for the grants of
        zope.View and zope.app.dublincore.view to zope.Anonymous. These
        ensure that, by default, anonymous users can view container contents.
        """
        # add an item that can be viewed from the root folder
        file = File()
        self.getRootFolder()['file'] = file
        IZopeDublinCore(file).title = u'My File'
        transaction.commit()

        response = self.publish('/')
        self.assertEquals(response.getStatus(), 200)
        body = response.getBody()

        # confirm we can see the file name
        self.assert_(body.find('<a href="file">file</a>') != -1)

        # confirm we can see the metadata title
        self.assert_(body.find('<td><span>My File</span></td>') != -1)

    def test_deny_view(self):
        """Tests the denial of view permissions to anonymous.

        This test uses the ZMI interface to deny anonymous zope.View permission
        to the root folder.
        """
        # deny zope.View to zope.Anonymous
        prm = IRolePermissionManager(self.getRootFolder())
        prm.denyPermissionToRole('zope.View', 'zope.Anonymous')
        transaction.commit()

        # confirm Unauthorized when viewing root folder
        self.assertRaises(Unauthorized, self.publish, '/')

    def test_deny_dublincore_view(self):
        """Tests the denial of dublincore view permissions to anonymous.

        Users who can view a folder contents page but cannot view dublin core
        should still be able to see the folder items' names, but not their
        title, modified, and created info.
        """
        # add an item that can be viewed from the root folder
        file = File()
        self.getRootFolder()['file'] = file
        IZopeDublinCore(file).title = u'My File'

        # deny zope.app.dublincore.view to zope.Anonymous
        prm = IRolePermissionManager(self.getRootFolder())
        prm.denyPermissionToRole('zope.app.dublincore.view', 'zope.Anonymous')
        transaction.commit()

        response = self.publish('/')
        self.assertEquals(response.getStatus(), 200)
        body = response.getBody()

        # confirm we can see the file name
        self.assert_(body.find('<a href="file">file</a>') != -1)

        # confirm we *cannot* see the metadata title
        self.assert_(body.find('My File') == -1)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Tests))
    return suite

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
