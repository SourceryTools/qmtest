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
"""This module tests the Gettext Export and Import funciotnality of the
Translation Domain.

$Id: test_filters.py 29143 2005-02-14 22:43:16Z srichter $
"""
import unittest
import time
from cStringIO import StringIO
from zope.interface import implements

from zope.app.testing import ztapi
from zope.app.testing.placelesssetup import PlacelessSetup
from zope.component.interfaces import IFactory
from zope.component.factory import Factory

from zope.app.i18n.messagecatalog import MessageCatalog
from zope.i18n.negotiator import negotiator
from zope.i18n.interfaces import INegotiator, IUserPreferredLanguages

from zope.app.i18n.translationdomain import TranslationDomain
from zope.app.i18n.filters import GettextImportFilter, GettextExportFilter


class Environment(object):

    implements(IUserPreferredLanguages)

    def __init__(self, langs=()):
        self.langs = langs

    def getPreferredLanguages(self):
        return self.langs


class TestGettextExportImport(PlacelessSetup, unittest.TestCase):

    _data = '''msgid ""
msgstr ""
"Project-Id-Version: Zope 3\\n"
"PO-Revision-Date: %s\\n"
"Last-Translator: Zope 3 Gettext Export Filter\\n"
"Zope-Language: de\\n"
"Zope-Domain: default\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"

msgid "Choose"
msgstr "Ausw\xc3\xa4hlen!"

msgid "greeting"
msgstr "hallo"
'''

    def setUp(self):
        super(TestGettextExportImport, self).setUp()

        # Setup the negotiator utility
        ztapi.provideUtility(INegotiator, negotiator)

        self._domain = TranslationDomain()
        self._domain.domain = 'default'
        ztapi.provideUtility(IFactory, Factory(MessageCatalog),
                             'zope.app.MessageCatalog')

    def testImportExport(self):
        imp = GettextImportFilter(self._domain)
        imp.importMessages(['de'], StringIO(self._data %'2002/02/02 02:02'))

        exp = GettextExportFilter(self._domain)
        result = exp.exportMessages(['de'])

        dt = time.time()
        dt = time.localtime(dt)
        dt = time.strftime('%Y/%m/%d %H:%M', dt)

        self.assertEqual(result.strip(), (self._data %dt).strip())


def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(TestGettextExportImport)


if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())
