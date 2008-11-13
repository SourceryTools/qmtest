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
"""Pluggable Authentication Service Tests

$Id: tests.py 75772 2007-05-15 18:21:29Z hdima $
"""

__docformat__ = "reStructuredText"

import re
import unittest
from zope.testing import renormalizing, doctest
from zope.app.testing.setup import placefulSetUp, placefulTearDown
import transaction
from zope.interface import directlyProvides
from zope.exceptions.interfaces import UserError
from zope.app.testing import functional
from zope.app.authentication.principalfolder import PrincipalFolder
from zope.app.authentication.principalfolder import Principal
from zope.app.authentication.principalfolder import IInternalPrincipal
from zope.app.authentication.testing import AppAuthenticationLayer


def schemaSearchSetUp(self):
    placefulSetUp(site=True)

def schemaSearchTearDown(self):
    placefulTearDown()

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


checker = renormalizing.RENormalizing([
    (re.compile(r"HTTP/1\.1 200 .*"), "HTTP/1.1 200 OK"),
    (re.compile(r"HTTP/1\.1 303 .*"), "HTTP/1.1 303 See Other"),
    (re.compile(r"HTTP/1\.1 401 .*"), "HTTP/1.1 401 Unauthorized"),
    ])


def test_suite():
    FunkTest.layer = AppAuthenticationLayer
    principalfolder = functional.FunctionalDocFileSuite(
        'principalfolder.txt', checker=checker)
    principalfolder.layer = AppAuthenticationLayer
    groupfolder = functional.FunctionalDocFileSuite(
        'groupfolder.txt', checker=checker)
    groupfolder.layer = AppAuthenticationLayer
    pau_prefix_and_searching = functional.FunctionalDocFileSuite(
        'pau_prefix_and_searching.txt', checker=checker)
    pau_prefix_and_searching.layer = AppAuthenticationLayer
    group_searching_with_empty_string = functional.FunctionalDocFileSuite(
        'group_searching_with_empty_string.txt', checker=checker)
    group_searching_with_empty_string.layer = AppAuthenticationLayer
    special_groups = functional.FunctionalDocFileSuite(
        'special-groups.txt', checker=checker)
    special_groups.layer = AppAuthenticationLayer
    issue663 = functional.FunctionalDocFileSuite('issue663.txt')
    issue663.layer = AppAuthenticationLayer
    return unittest.TestSuite((
        principalfolder,
        groupfolder,
        pau_prefix_and_searching,
        group_searching_with_empty_string,
        special_groups,
        unittest.makeSuite(FunkTest),
        issue663,
        doctest.DocFileSuite('schemasearch.txt'),
        ))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
