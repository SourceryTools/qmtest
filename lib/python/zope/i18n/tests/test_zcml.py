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
"""Test the gts ZCML namespace directives.

$Id: test_zcml.py 67630 2006-04-27 00:54:03Z jim $
"""
import os
import unittest

import zope.component
import zope.i18n.tests
from zope.component.testing import PlacelessSetup
from zope.configuration import xmlconfig
from zope.i18n.interfaces import ITranslationDomain

template = """\
<configure
    xmlns='http://namespaces.zope.org/zope'
    xmlns:i18n='http://namespaces.zope.org/i18n'>
  %s
</configure>"""

class DirectivesTest(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(DirectivesTest, self).setUp()
        self.context = xmlconfig.file('meta.zcml', zope.i18n)

    def testRegisterTranslations(self):
        self.assert_(zope.component.queryUtility(ITranslationDomain) is None)
        xmlconfig.string(
            template % '''
            <configure package="zope.i18n.tests">
            <i18n:registerTranslations directory="locale" />
            </configure>
            ''', self.context)
        path = os.path.join(os.path.dirname(zope.i18n.tests.__file__),
                            'locale', 'en', 'LC_MESSAGES', 'zope-i18n.mo')
        util = zope.component.getUtility(ITranslationDomain, 'zope-i18n')
        self.assertEquals(util._catalogs,
                          {'test': ['test'], 'en': [unicode(path)]})

def test_suite():
    return unittest.makeSuite(DirectivesTest)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
