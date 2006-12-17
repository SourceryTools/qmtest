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
"""This module tests the regular persistent Translation Domain.

$Id: test_translationdomain.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest, os
from zope.i18n.translationdomain import TranslationDomain
from zope.i18n.gettextmessagecatalog import GettextMessageCatalog
from zope.i18n.tests.test_itranslationdomain import \
     TestITranslationDomain, Environment
from zope.i18nmessageid import MessageFactory
from zope.i18n.interfaces import ITranslationDomain
import zope.component

def testdir():
    from zope.i18n import tests
    return os.path.dirname(tests.__file__)


class TestGlobalTranslationDomain(unittest.TestCase, TestITranslationDomain):

    def setUp(self):
        TestITranslationDomain.setUp(self)

    def _getTranslationDomain(self):
        domain = TranslationDomain('default')
        path = testdir()
        en_catalog = GettextMessageCatalog('en', 'default',
                                           os.path.join(path, 'en-default.mo'))
        de_catalog = GettextMessageCatalog('de', 'default',
                                           os.path.join(path, 'de-default.mo'))

        domain.addCatalog(en_catalog)
        domain.addCatalog(de_catalog)
        return domain

    def testNoTargetLanguage(self):
        # Having a fallback would interfere with this test
        self._domain.setLanguageFallbacks([])
        TestITranslationDomain.testNoTargetLanguage(self)

    def testSimpleNoTranslate(self):
        translate = self._domain.translate
        eq = self.assertEqual
        # Unset fallback translation languages
        self._domain.setLanguageFallbacks([])

        # Test that a translation in an unsupported language returns the
        # default, if there is no fallback language
        eq(translate('short_greeting', target_language='es'), 'short_greeting')
        eq(translate('short_greeting', target_language='es',
                     default='short_greeting'), 'short_greeting')

        # Same test, but use the context argument instead of target_language
        context = Environment()
        eq(translate('short_greeting', context=context), 'short_greeting')
        eq(translate('short_greeting', context=context,
                     default='short_greeting'), 'short_greeting')

    def testEmptyStringTranslate(self):
        translate = self._domain.translate
        self.assertEqual(translate(u'', target_language='en'), u'')
        self.assertEqual(translate(u'', target_language='foo'), u'')

    def testStringTranslate(self):
        self.assertEqual(
            self._domain.translate(u'short_greeting', target_language='en'),
            u'Hello!')

    def testMessageIDTranslate(self):
        factory = MessageFactory('default')
        translate = self._domain.translate
        msgid = factory(u'short_greeting', 'default')
        self.assertEqual(translate(msgid, target_language='en'), u'Hello!')
        # MessageID attributes override arguments
        msgid = factory('43-not-there', 'this ${that} the other',
                        mapping={'that': 'THAT'})
        self.assertEqual(
            translate(msgid, target_language='en', default="default",
                         mapping={"that": "that"}), "this THAT the other")

    def testMessageIDTranslateForDifferentDomain(self):
        domain = TranslationDomain('other')
        path = testdir()
        en_catalog = GettextMessageCatalog('en', 'other',
                                           os.path.join(path, 'en-default.mo'))
        domain.addCatalog(en_catalog)

        zope.component.provideUtility(domain, ITranslationDomain, 'other')

        factory = MessageFactory('other')
        msgid = factory(u'short_greeting', 'default')
        self.assertEqual(
            self._domain.translate(msgid, target_language='en'), u'Hello!')

    def testSimpleFallbackTranslation(self):
        translate = self._domain.translate
        eq = self.assertEqual
        # Test that a translation in an unsupported language returns a
        # translation in the fallback language (by default, English)
        eq(translate('short_greeting', target_language='es'),
           u'Hello!')
        # Same test, but use the context argument instead of target_language
        context = Environment()
        eq(translate('short_greeting', context=context),
           u'Hello!')

    def testInterpolationWithoutTranslation(self):
        translate = self._domain.translate
        self.assertEqual(
            translate('42-not-there', target_language="en",
                      default="this ${that} the other",
                      mapping={"that": "THAT"}),
            "this THAT the other")


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestGlobalTranslationDomain))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

