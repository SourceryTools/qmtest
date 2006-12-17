##############################################################################
#
# Copyright (c) 2004-2005 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Functional tests

$Id: ftests.py 69215 2006-07-19 22:00:21Z jim $
"""
import unittest
import transaction

from zope import copypastemove
from zope.interface import implements, Interface, directlyProvides
from zope.exceptions.interfaces import UserError

from zope.app.testing import ztapi
from zope.app.testing import functional
from zope.app.authentication.principalfolder import PrincipalFolder
from zope.app.authentication.principalfolder import Principal
from zope.app.authentication.principalfolder import IInternalPrincipal

class FunkTest(functional.BrowserTestCase):

    def test_copypaste_duplicated_id_object(self):

        root = self.getRootFolder()

        # Create a principal Folder
        root['pf'] = PrincipalFolder()
        pf = root['pf']

        # Create a principal with p1 as login
        principal = Principal('p1')
        principal.login = 'p1'
        directlyProvides(principal, IInternalPrincipal)

        pf['p1'] = principal

        transaction.commit()
        self.assertEqual(len(pf.keys()), 1)
        #raise str([x for x in pf.keys()])

        response = self.publish('/pf/@@contents.html',
                                basic='mgr:mgrpw',
                                form={'ids': [u'p1'],
                                      'container_copy_button': u'Copy'})
        self.assertEqual(response.getStatus(), 302)


        # Try to paste the file
        try:
            response = self.publish('/pf/@@contents.html',
                                    basic='mgr:mgrpw',
                                    form={'container_paste_button': ''})
        except UserError, e:
            self.assertEqual(
                str(e),
                "The given name(s) [u'p1'] is / are already being used")
        else:
            # test failed !
            self.asserEqual(1, 0)

    def test_cutpaste_duplicated_id_object(self):

        root = self.getRootFolder()

        # Create a principal Folder
        root['pf'] = PrincipalFolder()
        pf = root['pf']

        # Create a principal with p1 as login
        principal = Principal('p1')
        principal.login = 'p1'
        directlyProvides(principal, IInternalPrincipal)

        pf['p1'] = principal

        transaction.commit()
        self.assertEqual(len(pf.keys()), 1)
        #raise str([x for x in pf.keys()])

        response = self.publish('/pf/@@contents.html',
                                basic='mgr:mgrpw',
                                form={'ids': [u'p1'],
                                      'container_cut_button': u'Cut'})
        self.assertEqual(response.getStatus(), 302)


        # Try to paste the file
        try:
            response = self.publish('/pf/@@contents.html',
                                    basic='mgr:mgrpw',
                                    form={'container_paste_button': ''})
        except UserError, e:
            self.assertEqual(
                str(e),
                "The given name(s) [u'p1'] is / are already being used")
        else:
            # test failed !
            self.asserEqual(1, 0)


def test_suite():
    return unittest.TestSuite((
        functional.FunctionalDocFileSuite('principalfolder.txt'),
        functional.FunctionalDocFileSuite('groupfolder.txt'),
        functional.FunctionalDocFileSuite('pau_prefix_and_searching.txt'),
        functional.FunctionalDocFileSuite(
            'group_searching_with_empty_string.txt'),
        functional.FunctionalDocFileSuite('special-groups.txt'),
        unittest.makeSuite(FunkTest),
        functional.FunctionalDocFileSuite('issue663.txt'),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
