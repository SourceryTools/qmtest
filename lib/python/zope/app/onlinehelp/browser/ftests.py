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
"""Functional Tests for Onlinehelp

$Id: ftests.py 29184 2005-02-17 20:49:07Z rogerineichen $
"""
import os
import transaction
import unittest

from zope.app.folder.interfaces import IRootFolder
from zope.app.file import File
from zope.app.testing.functional import BrowserTestCase
from zope.app.onlinehelp.tests.test_onlinehelp import testdir
from zope.app.onlinehelp import globalhelp

class Test(BrowserTestCase):

    def test_contexthelp(self):
        path = os.path.join(testdir(), 'help.txt')
        globalhelp.registerHelpTopic('help', 'Help', '', path, IRootFolder)
        path = os.path.join(testdir(), 'help2.txt')
        globalhelp.registerHelpTopic('help2', 'Help2', '', path, IRootFolder,
            'contents.html')

        transaction.commit()

        response = self.publish("/+/action.html", basic='mgr:mgrpw', 
                                form={'type_name':u'zope.app.content.File', 
                                      'id':u'file'})

        self.assertEqual(response.getStatus(), 302)

        response = self.publish('/contents.html', basic='mgr:mgrpw')

        self.assertEqual(response.getStatus(), 200)
        body = ' '.join(response.getBody().split())
        self.assert_(body.find(
            "javascript:popup('contents.html/++help++/@@contexthelp.html") >= 0)

        response = self.publish(
            '/contents.html/++help++/@@contexthelp.html', basic='mgr:mgrpw')

        self.assertEqual(response.getStatus(), 200)
        body = ' '.join(response.getBody().split())
        self.assert_(body.find("This is another help!") >= 0)

        response = self.publish('/index.html/++help++/@@contexthelp.html', 
                                basic='mgr:mgrpw')

        self.assertEqual(response.getStatus(), 200)
        body = ' '.join(response.getBody().split())
        self.assert_(body.find("This is a help!") >= 0)

        response = self.publish('/file/edit.html/++help++/@@contexthelp.html',
                                basic='mgr:mgrpw')

        self.assertEqual(response.getStatus(), 200)
        body = ' '.join(response.getBody().split())
        self.assert_(body.find(
            "Welcome to the Zope 3 Online Help System.") >= 0)

        path = '/contents.html/++help++'
        response = self.publish(path, basic='mgr:mgrpw')

        self.assertEqual(response.getStatus(), 200)
        body = ' '.join(response.getBody().split())
        self.assert_(body.find("Topics") >= 0)

        self.checkForBrokenLinks(body, path, basic='mgr:mgrpw')


def test_suite():
    return unittest.makeSuite(Test)

if __name__ == '__main__':
    unittest.main()
