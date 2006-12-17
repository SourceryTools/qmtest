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
"""$Id: ftests.py 29143 2005-02-14 22:43:16Z srichter $
"""
import unittest
from xml.dom import minidom
from zope.app.testing.functional import BrowserTestCase

class TestNavTree(BrowserTestCase):

    def testnavtree(self):
        # Add some folders
        response = self.publish("/+/action.html", basic='mgr:mgrpw', 
                                form={'type_name':u'zope.app.content.Folder', 
                                      'id':u'First'})
        self.assertEqual(response.getStatus(), 302)
        response = self.publish("/+/action.html", basic='mgr:mgrpw', 
                                form={'type_name':u'zope.app.content.Folder', 
                                      'id':u'S&econd'})
        self.assertEqual(response.getStatus(), 302)
        response = self.publish("/+/action.html", basic='mgr:mgrpw', 
                                form={'type_name':u'zope.app.content.Folder', 
                                      'id':u'Third'})
        self.assertEqual(response.getStatus(), 302)
        response = self.publish("/First/+/action.html", basic='mgr:mgrpw', 
                                form={'type_name':u'zope.app.content.Folder', 
                                      'id':u'Firsts"Folder'})
        self.assertEqual(response.getStatus(), 302)
        response = self.publish("/First/+/action.html", basic='mgr:mgrpw', 
                                form={'type_name':u'zope.app.content.Folder', 
                                      'id':u'somesite'})
        self.assertEqual(response.getStatus(), 302)

        #add a site manager This will break when site adding is fixed
        # see above for examples to fix by filling out a form
        # when further action is required to make a site
        response = self.publish("/First/somesite/addSiteManager.html",
                                                basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 302)
        # /First/FirstsFolder/@@singleBranchTree.xml 
        # contains those 4 elements above
        # /@@children.xml 
        # contains First Second and Third
        
        response = self.publish(
                      "/First/somesite/++etc++site/@@singleBranchTree.xml",
                                                basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)

        tree = minidom.parseString(response.getBody())

        response = self.publish("/@@children.xml", basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)

        tree = minidom.parseString(response.getBody())

        response = self.publish("/First/+/action.html", basic='mgr:mgrpw', 
                                form={'type_name':u'zope.app.content.Folder', 
                                      'id':u'Firsts2ndFolder'})
        self.assertEqual(response.getStatus(), 302)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestNavTree))
    return suite

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

