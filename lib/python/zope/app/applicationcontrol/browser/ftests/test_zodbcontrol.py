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
"""ZODB Control Tests

$Id: test_zodbcontrol.py 37393 2005-07-23 15:43:27Z philikon $
"""
import unittest

from zope.app.testing.functional import BrowserTestCase


class ZODBControlTest(BrowserTestCase):

    def testZODBControlOverview(self):
        response = self.publish('/++etc++process/@@ZODBControl.html',
                                basic='globalmgr:globalmgrpw',
                                form={'days': u'3'})
        body = response.getBody()
        self.assert_('value="3"' in body)
        self.assert_('>Demo Storage</' in body)
        self.assert_('>1 KB</' in body)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ZODBControlTest))
    return suite

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
