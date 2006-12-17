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
"""Functional tests for the unique id utility.

$Id: ftests.py 30951 2005-06-29 21:48:07Z benji_york $
"""
import unittest
import re
from transaction import commit

from zope.app import zapi
from zope.app.testing import ztapi, setup
from zope.app.testing.functional import BrowserTestCase


class TestIntIds(BrowserTestCase):

    def setUp(self):
        from zope.app.intid import IntIds
        from zope.app.intid.interfaces import IIntIds

        BrowserTestCase.setUp(self)

        self.basepath = '/++etc++site/default'
        root = self.getRootFolder()

        sm = zapi.traverse(root, '/++etc++site')
        setup.addUtility(sm, 'intid', IIntIds, IntIds())
        commit()

        type_name = 'BrowserAdd__zope.app.intid.IntIds'

        response = self.publish(
            self.basepath + '/contents.html',
            basic='mgr:mgrpw',
            form={'type_name': type_name,
                  'new_value': 'mgr' })

#        root = self.getRootFolder()
#        default = zapi.traverse(root, '/++etc++site/default')
#        rm = default.getRegistrationManager()
#        registration = UtilityRegistration(
#            'cwm', IIntIds, zapi.traverse(self.basepath+'/intid'))
#        pd_id = rm.addRegistration(registration)
#        zapi.traverse(rm, pd_id).status = ActiveStatus

    def test(self):
        response = self.publish(self.basepath + '/intid/@@index.html',
                                basic='mgr:mgrpw')
        self.assertEquals(response.getStatus(), 200)
        # The utility registers in itself when it is being added
        self.assert_(response.getBody().find('1 objects') > 0)
        self.assert_('<a href="/++etc++site">/++etc++site</a>'
                     not in response.getBody())

        response = self.publish(self.basepath + '/intid/@@populate',
                                basic='mgr:mgrpw')
        self.assertEquals(response.getStatus(), 302)

        response = self.publish(self.basepath
                                + '/intid/@@index.html?testing=1',
                                basic='mgr:mgrpw')
        self.assertEquals(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('3 objects' in body)
        self.assert_('<a href="/++etc++site">/++etc++site</a>' in body)
        self.checkForBrokenLinks(body, response.getPath(), basic='mgr:mgrpw')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestIntIds))
    return suite


if __name__ == '__main__':
    unittest.main()
